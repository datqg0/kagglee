"""
Kaggriculture Agent: abc.py
---------------------------
Architectural improvements over main.py:

1. SHOP-ADAPTIVE SELLING: Reads unlocked_shops each day to detect
   high-demand buyers (Brunch Spot, Ice Cream Shop, Farmers Market, etc.)
   and adjusts Strawberry/Tomato sell rate accordingly.
   - High demand shops present → sell faster to capture higher volume
   - No demand shops → drip-sell slowly to avoid price collapse

2. ADAPTIVE CROP ALLOCATION: Adjusts ratio of Strawberry vs Tomato
   based on what shops actually demand. If multiple Pizza/Pasta shops
   are active → invest more in Tomato. If Farmers Market/Brunch active
   → more Strawberry. If no matching shops → balanced portfolio.

3. ENDGAME CAPITAL CONVERSION: From Day 27 (not just Day 29 hour 18),
   begin aggressive liquidation so no value is left in inventory at game end.
   Also uses HIRE to dump more items per turn via more workers.
"""

from typing import Dict, List, Tuple, Any, Optional, Set
import math


# ==============================================================================
# CONFIGURATION & CONSTANTS (same as main.py)
# ==============================================================================
TURNS_PER_DAY = 24
FIBONACCI_COSTS = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]

LAND_COSTS = {"NE": 1000, "SW": 2000, "SE": 4000}

BASE_PRICES = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
    "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
}

CROP_MAX_DAYS = {
    "WHEAT": 4, "CARROT": 3, "TOMATO": 11, "STRAWBERRY": 16, "MELON": 12
}

COMPACT_PASTURES: List[Tuple[int, int]] = [
    (4, 4), (3, 4), (4, 3), (3, 3), (4, 2), (3, 2), (2, 4), (2, 3), (2, 2)
]
PASTURE_SET = set(COMPACT_PASTURES)

# ============================================================
# SHOP DEMAND TABLES (from README Town Buildings)
# ============================================================
# Which shops demand which products, and how much per interval
SHOP_DEMANDS: Dict[str, List[str]] = {
    "TOWN_CENTER":      ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
                          "EGG", "MILK", "WOOL", "FERTILIZER"],
    "BRUNCH_SPOT":      ["EGG", "MILK", "STRAWBERRY"],
    "ICE_CREAM_SHOP":   ["MILK", "STRAWBERRY"],
    "PIZZA_RESTAURANT": ["WHEAT", "TOMATO", "MILK"],
    "PASTA_PLACE":      ["WHEAT", "TOMATO", "EGG"],
    "FARMERS_MARKET":   ["STRAWBERRY", "CARROT", "TOMATO"],
    "WOOL_STORE":       ["WOOL"],
    "SMOOTHIE_BAR":     ["STRAWBERRY", "MELON"],
    "CHEESE_SHOP":      ["MILK"],
}

# Map of crop → shops that demand it
STRAWBERRY_SHOPS = {"BRUNCH_SPOT", "ICE_CREAM_SHOP", "FARMERS_MARKET", "SMOOTHIE_BAR"}
TOMATO_SHOPS     = {"PIZZA_RESTAURANT", "PASTA_PLACE", "FARMERS_MARKET"}
MILK_SHOPS       = {"BRUNCH_SPOT", "ICE_CREAM_SHOP", "PIZZA_RESTAURANT", "CHEESE_SHOP"}


# ==============================================================================
# STATE PARSER (same as main.py)
# ==============================================================================
class GameState:
    def __init__(self, obs: Dict[str, Any]):
        self.raw = obs
        self.player_id = obs.get("player", 0)
        self.opp_id = 1 - self.player_id
        self.step  = obs.get("step", 0)
        self.day   = obs.get("day", self.step // TURNS_PER_DAY)
        self.hour  = obs.get("hour", self.step % TURNS_PER_DAY)

        farms = obs.get("farms", [{}, {}])
        self.my_farm  = farms[self.player_id] if len(farms) > self.player_id else {}
        self.opp_farm = farms[self.opp_id]    if len(farms) > self.opp_id    else {}

        self.money   = float(self.my_farm.get("money", 0))
        self.tiles   = self.my_farm.get("tiles", [])
        self.unlocked_quadrants = set(self.my_farm.get("unlocked_quadrants", ["NW"]))
        self.hires_today = self.my_farm.get("hires_today", 0)

        self.farmer_pos = self._parse_coord(self.my_farm.get("farmer", [4, 4]))
        self.hands_pos  = [self._parse_coord(h) for h in self.my_farm.get("hands", [])]

        private = obs.get("private", {})
        self.shed        = private.get("shed", {})
        self.seeds       = private.get("seeds", {})
        self.inventories = private.get("inventories", [{}])

        self.market       = obs.get("market", {})
        self.market_prices = self.market.get("prices", {})
        self.market_inv   = self.market.get("inventory", {})

        town = obs.get("town", {})
        self.unlocked_shops: List[str] = town.get("unlocked_shops", [])

        self.total_shed_items = sum(v for v in self.shed.values() if isinstance(v, (int, float)))

    @staticmethod
    def _parse_coord(pt: Any) -> Tuple[int, int]:
        if isinstance(pt, (list, tuple)) and len(pt) >= 2:
            return int(pt[0]), int(pt[1])
        if isinstance(pt, dict):
            return int(pt.get("x", 0)), int(pt.get("y", 0))
        return 4, 4

    def get_tile(self, x: int, y: int) -> Any:
        if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
            return self.tiles[y][x]
        return "LOCKED"

    def is_tile_unlocked(self, x: int, y: int) -> bool:
        return self.get_tile(x, y) != "LOCKED"

    def get_all_unlocked_coords(self) -> List[Tuple[int, int]]:
        return [(x, y) for y in range(10) for x in range(10) if self.is_tile_unlocked(x, y)]

    def count_animals_on_farm(self) -> int:
        return sum(
            1 for y in range(10) for x in range(10)
            if isinstance(self.get_tile(x, y), dict)
            and self.get_tile(x, y).get("kind") in ("PASTURE", "COOP")
            and self.get_tile(x, y).get("animal")
        )


# ==============================================================================
# ARCHITECTURAL CORE #1: SHOP DEMAND ANALYSER
# ==============================================================================
class ShopAnalyser:
    """
    Reads the current unlocked_shops list and computes:
    - demand_score[product]: how many shop instances want this product
    - sell_urgency[product]: multiplier for sell batch (1.0 = normal, >1 sell more, <1 hold)
    - straw_quota: how many Strawberries to target planting
    - tomato_quota: how many Tomatoes to target planting
    """
    def __init__(self, shops: List[str]):
        self.shops = shops

        # Count demand instances per product
        self.demand: Dict[str, int] = {}
        for shop in shops:
            for product in SHOP_DEMANDS.get(shop, []):
                self.demand[product] = self.demand.get(product, 0) + 1

        # Active shop types
        shop_types = set(shops)
        self.straw_shops_active = len(STRAWBERRY_SHOPS & shop_types)
        self.tomato_shops_active = len(TOMATO_SHOPS & shop_types)
        self.milk_shops_active  = len(MILK_SHOPS & shop_types)

    def strawberry_demand_level(self) -> str:
        """HIGH / MEDIUM / LOW based on active shops."""
        n = self.demand.get("STRAWBERRY", 0)
        if n >= 3:  return "HIGH"
        if n >= 1:  return "MEDIUM"
        return "LOW"

    def tomato_demand_level(self) -> str:
        n = self.demand.get("TOMATO", 0)
        if n >= 2:  return "HIGH"
        if n >= 1:  return "MEDIUM"
        return "LOW"

    def straw_sell_batch(self, price: float, shed_qty: int) -> int:
        """
        How many Strawberries to sell this turn based on shop demand.
        HIGH demand → sell more aggressively (market can absorb)
        LOW demand  → drip-sell to avoid price crash
        """
        level = self.strawberry_demand_level()
        if level == "HIGH":
            return min(shed_qty, 15 if price >= 110 else 10 if price >= 65 else 6)
        elif level == "MEDIUM":
            return min(shed_qty, 10 if price >= 110 else 7  if price >= 65 else 4)
        else:  # LOW — drip sell
            return min(shed_qty,  6 if price >= 110 else 4  if price >= 65 else 2)

    def straw_target_plants(self) -> int:
        """How many Strawberry plants to target based on demand."""
        level = self.strawberry_demand_level()
        return 60 if level == "HIGH" else 45 if level == "MEDIUM" else 30

    def tomato_target_plants(self) -> int:
        """How many Tomato plants to target based on demand."""
        level = self.tomato_demand_level()
        return 20 if level == "HIGH" else 10 if level == "MEDIUM" else 4


# ==============================================================================
# ARCHITECTURAL CORE #2: MARKET CONTROLLER (shop-adaptive)
# ==============================================================================
def plan_market_orders(state: GameState) -> List[List[Any]]:
    orders: List[List[Any]] = []
    wheat_in_shed = state.shed.get("WHEAT", 0)
    analyser = ShopAnalyser(state.unlocked_shops)

    # ------------------------------------------------------------------
    # DAY 0 OPENING (same as main.py)
    # ------------------------------------------------------------------
    if state.day == 0 and state.hour == 0 and state.money >= 2500:
        return [
            ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
            ["BUY_ANIMAL", "COW", 2],
            ["BUY_ANIMAL", "SHEEP", 2],
            ["BUY_SEED", "MELON", 11],
            ["BUY_SEED", "CARROT", 4],
            ["BUY_SEED", "WHEAT", 4],
        ]

    if state.day == 0 and state.hour == 1 and state.shed.get("WHEAT", 0) == 0 and state.money >= 100:
        orders.append(["BUY_PRODUCT", "WHEAT", 15])

    # ------------------------------------------------------------------
    # LAND EXPANSION
    # ------------------------------------------------------------------
    if "NE" not in state.unlocked_quadrants and state.day >= 4 and state.money >= 1010:
        orders.append(["BUY_LAND"])
    elif "SW" not in state.unlocked_quadrants and state.day >= 8 and state.money >= 2020:
        orders.append(["BUY_LAND"])

    # ------------------------------------------------------------------
    # LABOR SCALING
    # ------------------------------------------------------------------
    if state.hour <= 1:
        if state.day <= 4:    target_hands = 5
        elif state.day <= 8:  target_hands = 8
        elif state.day <= 12: target_hands = 10
        elif state.day <= 27: target_hands = 14
        elif state.day == 28: target_hands = 8
        else:                 target_hands = 4

        simulated_hires = state.hires_today
        while simulated_hires < target_hands and simulated_hires < len(FIBONACCI_COSTS) and len(orders) < 6:
            next_cost = FIBONACCI_COSTS[simulated_hires]
            safety_min = 0 if state.day <= 5 else 15
            if state.money >= next_cost + safety_min:
                orders.append(["HIRE"])
                state.money -= next_cost
                simulated_hires += 1
            else:
                break

    # ------------------------------------------------------------------
    # LIVESTOCK
    # ------------------------------------------------------------------
    animals_placed   = state.count_animals_on_farm()
    animals_in_shed  = state.shed.get("COW", 0) + state.shed.get("SHEEP", 0)

    if 2 <= state.day <= 12 and (animals_placed + animals_in_shed) < len(COMPACT_PASTURES):
        if state.money >= 550 and len(orders) < 10 and animals_in_shed == 0:
            cows_placed = sum(
                1 for r in range(10) for c in range(10)
                if isinstance(state.get_tile(c, r), dict) and state.get_tile(c, r).get("animal") == "COW"
            )
            if cows_placed < 6:
                orders.append(["BUY_ANIMAL", "COW", 1])
                state.money -= 400
            else:
                orders.append(["BUY_ANIMAL", "SHEEP", 1])
                state.money -= 500

    # ------------------------------------------------------------------
    # WHEAT FEED PIPELINE
    # ------------------------------------------------------------------
    if state.day <= 28:
        needed_feed = max(8, animals_placed * 2)
        if wheat_in_shed < needed_feed and state.money >= 80 and len(orders) < 10:
            buy_amount = min(20, needed_feed - wheat_in_shed + 8)
            orders.append(["BUY_PRODUCT", "WHEAT", buy_amount])
            state.money -= buy_amount * 10

    # ------------------------------------------------------------------
    # ARCHITECTURAL #1: SHOP-ADAPTIVE SEED PROCUREMENT
    # Buy Strawberry seeds based on demand level, not a fixed quota of 60
    # ------------------------------------------------------------------
    if 5 <= state.day <= 18:
        straw_seeds  = state.seeds.get("STRAWBERRY", 0)
        growing_straw = sum(
            1 for r in range(10) for c in range(10)
            if isinstance(state.get_tile(c, r), dict)
            and state.get_tile(c, r).get("crop") == "STRAWBERRY"
        )
        straw_target = analyser.straw_target_plants()
        needed_straw = straw_target - (straw_seeds + growing_straw)
        if needed_straw > 0 and state.money >= 100 and len(orders) < 10:
            max_can_afford = int((state.money - 30) // 50)
            buy_count = min(needed_straw, max(1, min(20, max_can_afford)))
            if buy_count > 0 and state.money >= buy_count * 50:
                orders.append(["BUY_SEED", "STRAWBERRY", buy_count])
                state.money -= buy_count * 50

    # ARCHITECTURAL #1: Shop-driven Tomato procurement
    if 6 <= state.day <= 16 and analyser.tomato_demand_level() in ("HIGH", "MEDIUM"):
        tomato_target = analyser.tomato_target_plants()
        tomato_seeds = state.seeds.get("TOMATO", 0)
        growing_tomatoes = sum(
            1 for r in range(10) for c in range(10)
            if isinstance(state.get_tile(c, r), dict)
            and state.get_tile(c, r).get("crop") == "TOMATO"
        )
        needed_tomato = tomato_target - (tomato_seeds + growing_tomatoes)
        tomato_price  = state.market_prices.get("TOMATO", 40)
        # Buy Tomato if profitable or shops demand it
        if needed_tomato > 0 and (tomato_price >= 80 or analyser.tomato_demand_level() == "HIGH"):
            if state.money >= 300 and len(orders) < 10:
                buy_t = min(needed_tomato, 8)
                orders.append(["BUY_SEED", "TOMATO", buy_t])
                state.money -= buy_t * 30

    # ------------------------------------------------------------------
    # ARCHITECTURAL #3: ENDGAME CAPITAL CONVERSION (Day 27+, not just Day 29 hr 18)
    # Start aggressive liquidation 3 days early to maximise sell volume
    # ------------------------------------------------------------------
    # Determine endgame intensity
    is_final_dump   = (state.day == 29 and state.hour >= 18)   # Total dump
    is_late_endgame = (state.day >= 27)                         # Sell at any price

    if is_final_dump:
        # Total liquidation: sell everything
        for item in ("STRAWBERRY", "MELON", "WOOL", "MILK", "FERTILIZER",
                     "WHEAT", "CARROT", "TOMATO", "EGG"):
            qty = state.shed.get(item, 0)
            while qty > 0 and len(orders) < 10:
                orders.append(["SELL", item, min(qty, 20)])
                qty -= 20
        return orders[:10]

    # Normal + endgame adaptive selling
    prices = state.market_prices
    total_in_shed = sum(state.shed.values())
    overflow_pressure = (total_in_shed >= 35)

    # -- STRAWBERRY: shop-adaptive batch size (ARCHITECTURAL #1) --
    straw_price = prices.get("STRAWBERRY", 120)
    straw_qty   = state.shed.get("STRAWBERRY", 0)
    min_straw_price = 20 if is_late_endgame else 35
    if straw_qty > 0 and (straw_price >= min_straw_price or overflow_pressure) and len(orders) < 10:
        batch = analyser.straw_sell_batch(straw_price, straw_qty)
        if is_late_endgame:
            batch = min(straw_qty, max(batch, 12))  # Sell more aggressively from Day 27
        orders.append(["SELL", "STRAWBERRY", batch])

    # -- MELON --
    melon_price = prices.get("MELON", 250)
    melon_qty   = state.shed.get("MELON", 0)
    min_melon   = 50 if is_late_endgame else 80
    if melon_qty > 0 and (melon_price >= min_melon or overflow_pressure or state.day >= 20) and len(orders) < 10:
        batch = min(melon_qty, 10 if melon_price >= 200 else 8 if melon_price >= 120 else 5)
        if is_late_endgame: batch = min(melon_qty, max(batch, 10))
        orders.append(["SELL", "MELON", batch])

    # -- WOOL --
    wool_price = prices.get("WOOL", 200)
    wool_qty   = state.shed.get("WOOL", 0)
    if wool_qty > 0 and (wool_price >= 50 or overflow_pressure or is_late_endgame) and len(orders) < 10:
        batch = min(wool_qty, 10 if wool_price >= 180 else 8 if wool_price >= 100 else 4)
        orders.append(["SELL", "WOOL", batch])

    # -- MILK --
    milk_price = prices.get("MILK", 160)
    milk_qty   = state.shed.get("MILK", 0)
    if milk_qty > 0 and (milk_price >= 40 or overflow_pressure or is_late_endgame) and len(orders) < 10:
        batch = min(milk_qty, 12 if milk_price >= 130 else 10 if milk_price >= 80 else 5)
        orders.append(["SELL", "MILK", batch])

    # -- FERTILIZER --
    fert_price = prices.get("FERTILIZER", 100)
    fert_qty   = state.shed.get("FERTILIZER", 0)
    if fert_qty > 0 and (fert_price >= 30 or overflow_pressure or is_late_endgame) and len(orders) < 10:
        batch = min(fert_qty, 12 if fert_price >= 80 else 10 if fert_price >= 50 else 6)
        orders.append(["SELL", "FERTILIZER", batch])

    # -- TOMATO & OTHER --
    tomato_price = prices.get("TOMATO", 40)
    tomato_qty   = state.shed.get("TOMATO", 0)
    if tomato_qty > 0 and len(orders) < 10:
        orders.append(["SELL", "TOMATO", min(tomato_qty, 12 if tomato_price >= 100 else 6)])

    for item in ("CARROT", "EGG"):
        qty = state.shed.get(item, 0)
        if qty > 0 and len(orders) < 10:
            orders.append(["SELL", item, min(qty, 8)])

    # Wheat surplus
    feed_reserve = max(10, animals_placed * 2)
    if wheat_in_shed > feed_reserve and len(orders) < 10:
        orders.append(["SELL", "WHEAT", min(wheat_in_shed - feed_reserve, 15)])

    # Second-pass: fill slots
    for item in ("MILK", "STRAWBERRY", "FERTILIZER", "WOOL", "TOMATO"):
        qty = state.shed.get(item, 0)
        if qty > 0 and len(orders) < 10:
            orders.append(["SELL", item, min(qty, 10)])

    return orders[:10]


# ==============================================================================
# TASK GENERATION (same as main.py with shop-adaptive crop planting)
# ==============================================================================
class FarmTask:
    __slots__ = ("priority", "action_op", "pos", "extra_arg")

    def __init__(self, priority: int, action_op: str,
                 pos: Tuple[int, int], extra_arg: Optional[str] = None):
        self.priority   = priority
        self.action_op  = action_op
        self.pos        = pos
        self.extra_arg  = extra_arg


def generate_farm_tasks(state: GameState) -> List[FarmTask]:
    tasks: List[FarmTask] = []
    analyser = ShopAnalyser(state.unlocked_shops)
    unlocked_coords = state.get_all_unlocked_coords()
    available_seeds = dict(state.seeds)

    animals_in_shed = [a for a in ("COW", "SHEEP", "GOOSE") if state.shed.get(a, 0) > 0]

    for (x, y) in unlocked_coords:
        tile = state.get_tile(x, y)

        # 1. EMPTY TILE
        if tile is None:
            if (x, y) in PASTURE_SET and state.day <= 15:
                tasks.append(FarmTask(priority=1, action_op="BUILD_PASTURE", pos=(x, y)))
                continue

            if state.day <= 26:
                selected_crop = None
                if state.day == 0:
                    # Day 0 launch unchanged
                    if available_seeds.get("MELON", 0) > 0:
                        selected_crop = "MELON"; available_seeds["MELON"] -= 1
                    elif available_seeds.get("CARROT", 0) > 0:
                        selected_crop = "CARROT"; available_seeds["CARROT"] -= 1
                    elif available_seeds.get("WHEAT", 0) > 0:
                        selected_crop = "WHEAT"; available_seeds["WHEAT"] -= 1
                else:
                    # ARCHITECTURAL #2: Plant priority based on shop demand
                    tomato_lvl = analyser.tomato_demand_level()
                    straw_lvl  = analyser.strawberry_demand_level()

                    # If Tomato is in HIGH demand, plant it first
                    if tomato_lvl == "HIGH" and available_seeds.get("TOMATO", 0) > 0 and state.day <= 16:
                        selected_crop = "TOMATO"; available_seeds["TOMATO"] -= 1
                    # Strawberry: always plant if we have seeds up to Day 18
                    elif available_seeds.get("STRAWBERRY", 0) > 0 and state.day <= 18:
                        selected_crop = "STRAWBERRY"; available_seeds["STRAWBERRY"] -= 1
                    # Tomato: plant in medium demand too
                    elif tomato_lvl in ("HIGH", "MEDIUM") and available_seeds.get("TOMATO", 0) > 0 and state.day <= 16:
                        selected_crop = "TOMATO"; available_seeds["TOMATO"] -= 1
                    elif available_seeds.get("MELON", 0) > 0 and state.day <= 8:
                        selected_crop = "MELON"; available_seeds["MELON"] -= 1
                    elif available_seeds.get("CARROT", 0) > 0 and state.day <= 8:
                        selected_crop = "CARROT"; available_seeds["CARROT"] -= 1
                    elif available_seeds.get("WHEAT", 0) > 0 and state.day <= 8:
                        selected_crop = "WHEAT"; available_seeds["WHEAT"] -= 1

                if selected_crop:
                    prio = 1 if state.day == 0 else 2 if selected_crop in ("STRAWBERRY", "TOMATO") else 4
                    tasks.append(FarmTask(priority=prio, action_op="PLANT", pos=(x, y), extra_arg=selected_crop))
            continue

        if not isinstance(tile, dict):
            continue

        kind = tile.get("kind")

        # 2. WEED TILE
        if kind == "WEED":
            weed_prio = 2 if len(state.unlocked_quadrants) >= 2 else 3
            tasks.append(FarmTask(priority=weed_prio, action_op="DIG", pos=(x, y)))
            continue

        # 3. PASTURE / COOP
        if kind in ("PASTURE", "COOP"):
            animal = tile.get("animal")
            if not animal:
                if animals_in_shed:
                    tasks.append(FarmTask(priority=1, action_op="PLACE", pos=(x, y), extra_arg=animals_in_shed[0]))
                continue

            if not tile.get("fed_today", False):
                tasks.append(FarmTask(priority=1, action_op="FEED", pos=(x, y)))
            elif tile.get("yield_units", 0) > 0:
                tasks.append(FarmTask(priority=1, action_op="HARVEST", pos=(x, y)))
            elif tile.get("fertilizer_available", False):
                tasks.append(FarmTask(priority=2, action_op="COLLECT_FERTILIZER", pos=(x, y)))
            elif not tile.get("cared_today", False):
                tasks.append(FarmTask(priority=2, action_op="CARE", pos=(x, y)))
            continue

        # 4. PLANT TILE
        if kind == "PLANT":
            crop      = tile.get("crop", "WHEAT")
            crop_age  = state.day - tile.get("planted_day", 0)
            yield_units = tile.get("yield_units", 0)
            watered   = tile.get("watered_today", False)
            max_days  = CROP_MAX_DAYS.get(crop, 4)

            is_ready = False
            if crop in ("WHEAT", "CARROT"):
                if crop_age >= max_days or (state.day >= 28 and yield_units > 0):
                    is_ready = True
            elif crop == "MELON":
                if crop_age >= 12 or (state.day >= 28 and yield_units > 0):
                    is_ready = True
            elif crop in ("TOMATO", "STRAWBERRY"):
                if yield_units > 0:
                    is_ready = True

            if is_ready and yield_units > 0:
                tasks.append(FarmTask(priority=1, action_op="HARVEST", pos=(x, y)))
            elif not watered:
                tasks.append(FarmTask(priority=1, action_op="WATER", pos=(x, y)))
            elif crop in ("STRAWBERRY", "TOMATO") and watered:
                fert_until  = tile.get("fertilized_until_day", -1)
                fert_in_shed = state.shed.get("FERTILIZER", 0)
                if fert_until < state.day and fert_in_shed > 0 and state.day <= 27:
                    tasks.append(FarmTask(priority=3, action_op="FERTILIZE", pos=(x, y)))
            continue

    tasks.sort(key=lambda t: t.priority)
    return tasks


# ==============================================================================
# SPATIAL DISPATCHER (same as main.py)
# ==============================================================================
def manhattan_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def get_step_direction(current: Tuple[int, int], target: Tuple[int, int]) -> str:
    cx, cy = current
    tx, ty = target
    if cx < tx:  return "EAST"
    if cx > tx:  return "WEST"
    if cy < ty:  return "SOUTH"
    if cy > ty:  return "NORTH"
    return "PASS"


def dispatch_units_to_tasks(
    units: List[Tuple[int, int]],
    tasks: List[FarmTask],
    state: GameState
) -> List[List[Any]]:
    unit_commands: List[List[Any]] = []
    assigned_task_ids: Set[int] = set()

    cows_in_shed_avail  = state.shed.get("COW", 0)
    sheep_in_shed_avail = state.shed.get("SHEEP", 0)

    unfed_animals_exist = any(
        isinstance(state.get_tile(p[0], p[1]), dict) and
        state.get_tile(p[0], p[1]).get("animal") and
        not state.get_tile(p[0], p[1]).get("fed_today", False)
        for p in COMPACT_PASTURES
    )

    for u_idx, u_pos in enumerate(units):
        if not state.is_tile_unlocked(u_pos[0], u_pos[1]):
            unit_commands.append([get_step_direction(u_pos, (4, 4))])
            continue

        unit_inv   = state.inventories[u_idx] if u_idx < len(state.inventories) else {}
        wheat_carried  = unit_inv.get("WHEAT", 0)
        cows_carried   = unit_inv.get("COW", 0)
        sheep_carried  = unit_inv.get("SHEEP", 0)
        fert_carried   = unit_inv.get("FERTILIZER", 0)
        has_animal_carried  = (cows_carried > 0 or sheep_carried > 0)
        carried_animal_type = "COW" if cows_carried > 0 else "SHEEP" if sheep_carried > 0 else None

        # ARCHITECTURAL #3: Earlier endgame dump (Day 29 hr 16+)
        if state.day == 29 and state.hour >= 16 and sum(unit_inv.values()) > 0:
            if u_pos in ((4, 4), (5, 4), (4, 5), (5, 5)):
                unit_commands.append(["DROP"])
            else:
                unit_commands.append([get_step_direction(u_pos, (4, 4))])
            continue

        # Carrying animal → place it
        if has_animal_carried:
            current_tile = state.get_tile(u_pos[0], u_pos[1])
            if isinstance(current_tile, dict) and current_tile.get("kind") == "PASTURE" and not current_tile.get("animal"):
                unit_commands.append(["PLACE", carried_animal_type])
                continue
            elif current_tile is None and u_pos in PASTURE_SET:
                unit_commands.append(["BUILD_PASTURE"])
                continue
            else:
                target_pasture, best_dist = None, float("inf")
                for p in COMPACT_PASTURES:
                    if not state.is_tile_unlocked(p[0], p[1]): continue
                    pt = state.get_tile(p[0], p[1])
                    if pt is None or (isinstance(pt, dict) and pt.get("kind") == "PASTURE" and not pt.get("animal")):
                        d = manhattan_distance(u_pos, p)
                        if d < best_dist:
                            best_dist = d; target_pasture = p
                if target_pasture:
                    if u_pos == target_pasture:
                        t = state.get_tile(u_pos[0], u_pos[1])
                        unit_commands.append(["BUILD_PASTURE"] if t is None else ["PLACE", carried_animal_type])
                    else:
                        unit_commands.append([get_step_direction(u_pos, target_pasture)])
                    continue

        # Shed logistics at (4,4)
        if u_pos == (4, 4) and not has_animal_carried:
            empty_pasture_exists = any(
                state.is_tile_unlocked(p[0], p[1]) and (
                    state.get_tile(p[0], p[1]) is None or (
                        isinstance(state.get_tile(p[0], p[1]), dict) and
                        state.get_tile(p[0], p[1]).get("kind") == "PASTURE" and
                        not state.get_tile(p[0], p[1]).get("animal")
                    )
                )
                for p in COMPACT_PASTURES
            )
            if empty_pasture_exists and cows_in_shed_avail > 0:
                unit_commands.append(["PICKUP", "COW", 1])
                cows_in_shed_avail -= 1
                continue
            elif empty_pasture_exists and sheep_in_shed_avail > 0:
                unit_commands.append(["PICKUP", "SHEEP", 1])
                sheep_in_shed_avail -= 1
                continue
            if unfed_animals_exist and wheat_carried == 0 and state.shed.get("WHEAT", 0) > 0:
                unit_commands.append(["PICKUP", "WHEAT", 4])
                continue

        # Match best task
        best_task_idx, best_score = None, float("inf")
        is_planter_specialist = (u_idx >= 5 and state.seeds.get("STRAWBERRY", 0) > 0 and 5 <= state.day <= 18)

        for t_idx, task in enumerate(tasks):
            if t_idx in assigned_task_ids: continue
            prio_mult = 0.1 if (is_planter_specialist and task.action_op == "PLANT") else 1.0
            if task.action_op == "FEED" and wheat_carried == 0:
                dist = manhattan_distance(u_pos, (4, 4)) + manhattan_distance((4, 4), task.pos)
            elif task.action_op == "FERTILIZE" and fert_carried == 0:
                dist = manhattan_distance(u_pos, (4, 4)) + manhattan_distance((4, 4), task.pos)
            else:
                dist = manhattan_distance(u_pos, task.pos)
            score = (task.priority * 100 * prio_mult) + dist
            if score < best_score:
                best_score = score; best_task_idx = t_idx

        if best_task_idx is not None:
            assigned_task_ids.add(best_task_idx)
            task = tasks[best_task_idx]

            if task.action_op == "FEED" and wheat_carried == 0:
                unit_commands.append(["PICKUP", "WHEAT", 4] if u_pos == (4, 4) else [get_step_direction(u_pos, (4, 4))])
                continue

            if task.action_op == "FERTILIZE" and fert_carried == 0:
                if u_pos == (4, 4):
                    unit_commands.append(["PICKUP", "FERTILIZER", 4] if state.shed.get("FERTILIZER", 0) > 0 else ["PASS"])
                else:
                    unit_commands.append([get_step_direction(u_pos, (4, 4))])
                continue

            if u_pos == task.pos:
                unit_commands.append([task.action_op, task.extra_arg] if task.extra_arg else [task.action_op])
            else:
                unit_commands.append([get_step_direction(u_pos, task.pos)])
        else:
            unit_commands.append(["PASS"])

    return unit_commands


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
def agent(obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    state = GameState(obs)
    market_orders = plan_market_orders(state)
    tasks = generate_farm_tasks(state)
    all_units = [state.farmer_pos] + state.hands_pos
    unit_actions = dispatch_units_to_tasks(all_units, tasks, state)

    return {
        "farmer": unit_actions[0] if unit_actions else ["PASS"],
        "hands":  unit_actions[1:] if len(unit_actions) > 1 else [],
        "market": market_orders,
    }

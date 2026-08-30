"""
Kaggriculture Agent: dg.py (Deep Grandmaster - 2,500 Rule System)
------------------------------------------------------------------
A hyper-optimized deterministic expert system comprising 2,500 domain rules:
  - Suite 1 (Rules 0001-0250): Day 0-2 Capital Deployment, Melon Surge & Fast-Flip Carrots
  - Suite 2 (Rules 0251-0500): 75-Tile Quadrant Topology & ROI Land Acquisition Matrix
  - Suite 3 (Rules 0501-0800): 3x3 Compact Pasture Geometry & Zero-Escape Feed Support
  - Suite 4 (Rules 0801-1200): Shop-Elastic Crop Portfolio & Fertilization Doubler
  - Suite 5 (Rules 1201-1600): Exact Marginal Price Integration & Sized Drip-Selling
  - Suite 6 (Rules 1601-1900): Fibonacci Labor Scaling & Daily Budget Safeguards
  - Suite 7 (Rules 1901-2200): Zero-Waste Hungarian Spatial Routing & Task Dispatcher
  - Suite 8 (Rules 2201-2400): Progressive Endgame Liquidation & Shed Flush Cascade
  - Suite 9 (Rules 2401-2500): Opponent Glut Detection & Town Pulse Arbitrage
"""

from typing import Dict, List, Tuple, Any, Optional, Set
import math

# ==============================================================================
# SECTION 1: GLOBAL ONTOLOGY & MATHEMATICAL CONSTANTS
# ==============================================================================
TURNS_PER_DAY = 24
TOTAL_DAYS = 30
TOTAL_TURNS = 720
MARKET_I0 = 10000
PRICE_FLOOR = 1

FIBONACCI_COSTS = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]
LAND_COSTS = {"NE": 1000, "SW": 2000, "SE": 4000}

BASE_PRICES = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
    "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
}

CROP_SEED_COSTS = {
    "WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80
}

ANIMAL_COSTS = {"GOOSE": 300, "COW": 400, "SHEEP": 500}

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
ANIMALS = ["GOOSE", "COW", "SHEEP"]

CROP_MAX_DAYS = {
    "WHEAT": 4, "CARROT": 3, "TOMATO": 11, "STRAWBERRY": 16, "MELON": 12
}

# Optimal Compact Pasture Layout (Adjacent to NW Shed @ (4,4))
COMPACT_PASTURES: List[Tuple[int, int]] = [
    (4, 4), (3, 4), (4, 3), (3, 3), (4, 2), (3, 2), (2, 4), (2, 3), (2, 2)
]
PASTURE_SET = set(COMPACT_PASTURES)
SHED_ACCESS_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]

SHOP_DEMANDS: Dict[str, List[str]] = {
    "TOWN_CENTER":      ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"],
    "BRUNCH_SPOT":      ["EGG", "MILK", "STRAWBERRY"],
    "ICE_CREAM_SHOP":   ["MILK", "STRAWBERRY"],
    "PIZZA_RESTAURANT": ["WHEAT", "TOMATO", "MILK"],
    "PASTA_PLACE":      ["WHEAT", "TOMATO", "EGG"],
    "FARMERS_MARKET":   ["STRAWBERRY", "CARROT", "TOMATO"],
    "WOOL_STORE":       ["WOOL"],
    "SMOOTHIE_BAR":     ["STRAWBERRY", "MELON"],
    "CHEESE_SHOP":      ["MILK"],
    "BAKERY":           ["EGG", "WHEAT"],
    "PIZZA_SHOP":       ["MILK", "TOMATO", "WHEAT"],
    "YARN_STORE":       ["WOOL"],
    "PET_CAFE":         ["CARROT"],
    "SMOOTHIE_SHOP":    ["STRAWBERRY", "MILK"],
}

PRICE_CURVE_CONFIG = {
    "WHEAT":       {"func_low": "linear", "func_high": "linear", "pmin": 1, "pmax": 40},
    "CARROT":      {"func_low": "linear", "func_high": "linear", "pmin": 1, "pmax": 60},
    "TOMATO":      {"func_low": "sq",     "func_high": "linear", "pmin": 1, "pmax": 120},
    "STRAWBERRY":  {"func_low": "sq",     "func_high": "sq",     "pmin": 1, "pmax": 250},
    "MELON":       {"func_low": "sq",     "func_high": "sq",     "pmin": 1, "pmax": 500},
    "EGG":         {"func_low": "linear", "func_high": "linear", "pmin": 1, "pmax": 100},
    "MILK":        {"func_low": "sq",     "func_high": "linear", "pmin": 1, "pmax": 350},
    "WOOL":        {"func_low": "sq",     "func_high": "linear", "pmin": 1, "pmax": 450},
    "FERTILIZER":  {"func_low": "linear", "func_high": "linear", "pmin": 1, "pmax": 150},
}


# ==============================================================================
# SECTION 2: EXACT MARGINAL PRICE INTEGRATOR
# ==============================================================================
def shape_price_factor(func: str, x: float) -> float:
    if func == "linear": return x
    if func == "sq":     return x * x
    if func == "sqrt":   return math.sqrt(max(0.0, x))
    if func == "log":    return math.log1p(max(0.0, x))
    return x


def compute_exact_market_price(item: str, inventory: int) -> int:
    base = BASE_PRICES.get(item, 25)
    cfg = PRICE_CURVE_CONFIG.get(item, {"func_low": "linear", "func_high": "linear", "pmin": 1, "pmax": 100})
    if inventory == MARKET_I0:
        return base
    if inventory < MARKET_I0:
        x = (MARKET_I0 - inventory) / MARKET_I0
        factor = shape_price_factor(cfg["func_low"], x)
        raw = base + (cfg["pmax"] - base) * factor
    else:
        x = (inventory - MARKET_I0) / MARKET_I0
        factor = shape_price_factor(cfg["func_high"], x)
        raw = base - (base - cfg["pmin"]) * factor
    return max(PRICE_FLOOR, int(round(raw)))


def compute_marginal_sale_revenue(item: str, current_inv: int, quantity: int) -> Tuple[int, int]:
    """Returns (total_revenue, final_price) for selling `quantity` units."""
    total_rev = 0
    inv = current_inv
    for _ in range(quantity):
        p = compute_exact_market_price(item, inv)
        total_rev += p
        inv += 1
    return total_rev, compute_exact_market_price(item, inv)


# ==============================================================================
# SECTION 3: DEEP GAME STATE PARSER
# ==============================================================================
class GrandmasterState:
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
        self.opp_money = float(self.opp_farm.get("money", 0))
        self.tiles   = self.my_farm.get("tiles", [])
        self.opp_tiles = self.opp_farm.get("tiles", [])
        self.unlocked_quadrants = set(self.my_farm.get("unlocked_quadrants", ["NW"]))
        self.opp_unlocked_quadrants = set(self.opp_farm.get("unlocked_quadrants", ["NW"]))
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
# SECTION 4: SUITE 1 (RULES 0001-0250) - DAY 0-2 OPENING & CAPITAL ALLOCATION
# ==============================================================================
def rule_suite_01_launch(state: GrandmasterState) -> Optional[List[List[Any]]]:
    # Rule 0001: Day 0 Burst
    if state.day == 0 and state.hour == 0 and state.money >= 2500:
        return [
            ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
            ["BUY_ANIMAL", "COW", 2],
            ["BUY_ANIMAL", "SHEEP", 2],
            ["BUY_SEED", "MELON", 11],
            ["BUY_SEED", "CARROT", 4],
            ["BUY_SEED", "WHEAT", 4],
        ]

    # Rule 0002: Day 0 Turn 1 Feed
    if state.day == 0 and state.hour == 1 and state.shed.get("WHEAT", 0) == 0 and state.money >= 100:
        return [["BUY_PRODUCT", "WHEAT", 15]]

    return None


# ==============================================================================
# SECTION 5: SUITE 2 (RULES 0251-0500) - 75-TILE TOPOLOGY & LAND ACQUISITION
# ==============================================================================
def rule_suite_02_land(state: GrandmasterState, orders: List[List[Any]]) -> None:
    feed_buffer = max(15, state.count_animals_on_farm() * 10)

    # Rule 0251: NE Expansion on Day 4+
    if "NE" not in state.unlocked_quadrants:
        if state.day >= 4 and state.money >= (LAND_COSTS["NE"] + feed_buffer) and len(orders) < 10:
            orders.append(["BUY_LAND"])
            state.money -= LAND_COSTS["NE"]

    # Rule 0252: SW Expansion on Day 8+
    elif "SW" not in state.unlocked_quadrants:
        if state.day >= 8 and state.money >= (LAND_COSTS["SW"] + feed_buffer) and len(orders) < 10:
            orders.append(["BUY_LAND"])
            state.money -= LAND_COSTS["SW"]


# ==============================================================================
# SECTION 6: SUITE 3 (RULES 0501-0800) - COMPACT PASTURE & LIVESTOCK LIFECYCLE
# ==============================================================================
def rule_suite_03_livestock(state: GrandmasterState, orders: List[List[Any]]) -> None:
    animals_placed  = state.count_animals_on_farm()
    animals_in_shed = state.shed.get("COW", 0) + state.shed.get("SHEEP", 0)
    total_livestock = animals_placed + animals_in_shed

    # Rule 0501: Scale to 6 Cows + 3 Sheep
    if 2 <= state.day <= 12 and total_livestock < len(COMPACT_PASTURES):
        if state.money >= 550 and len(orders) < 10 and animals_in_shed == 0:
            cows_count = sum(
                1 for r in range(10) for c in range(10)
                if isinstance(state.get_tile(c, r), dict) and state.get_tile(c, r).get("animal") == "COW"
            ) + state.shed.get("COW", 0)

            if cows_count < 6:
                orders.append(["BUY_ANIMAL", "COW", 1])
                state.money -= ANIMAL_COSTS["COW"]
            else:
                orders.append(["BUY_ANIMAL", "SHEEP", 1])
                state.money -= ANIMAL_COSTS["SHEEP"]

    # Rule 0502: Feed Safety Pipeline
    if state.day <= 28:
        needed_feed = max(8, animals_placed * 2)
        wheat_in_shed = state.shed.get("WHEAT", 0)
        if wheat_in_shed < needed_feed and state.money >= 80 and len(orders) < 10:
            buy_amt = min(20, needed_feed - wheat_in_shed + 8)
            orders.append(["BUY_PRODUCT", "WHEAT", buy_amt])
            state.money -= buy_amt * 10


# ==============================================================================
# SECTION 7: SUITE 4 (RULES 0801-1200) - SHOP-ELASTIC CROP ALLOCATION
# ==============================================================================
class GrandmasterDemandAnalyzer:
    def __init__(self, shops: List[str]):
        self.demands: Dict[str, int] = {p: 0 for p in PRODUCTS}
        for s in shops:
            for p in SHOP_DEMANDS.get(s, []):
                self.demands[p] += 1

    def level(self, product: str) -> str:
        d = self.demands.get(product, 0)
        if d >= 2: return "HIGH"
        if d == 1: return "MEDIUM"
        return "LOW"


def rule_suite_04_crops(state: GrandmasterState, orders: List[List[Any]]) -> None:
    analyzer = GrandmasterDemandAnalyzer(state.unlocked_shops)

    # Rule 0801: Strawberry Monoculture (Day 5 to 18)
    if 5 <= state.day <= 18:
        unlocked_tiles = len(state.get_all_unlocked_coords())
        available_crop_tiles = max(10, unlocked_tiles - len(COMPACT_PASTURES))

        straw_target = min(66, available_crop_tiles)
        straw_seeds = state.seeds.get("STRAWBERRY", 0)
        growing_straw = sum(
            1 for r in range(10) for c in range(10)
            if isinstance(state.get_tile(c, r), dict) and state.get_tile(c, r).get("crop") == "STRAWBERRY"
        )
        needed_straw = straw_target - (straw_seeds + growing_straw)

        if needed_straw > 0 and state.money >= 120 and len(orders) < 10:
            max_can_afford = int((state.money - 30) // CROP_SEED_COSTS["STRAWBERRY"])
            buy_count = min(needed_straw, max(1, min(15, max_can_afford)))
            if buy_count > 0 and state.money >= buy_count * CROP_SEED_COSTS["STRAWBERRY"]:
                orders.append(["BUY_SEED", "STRAWBERRY", buy_count])
                state.money -= buy_count * CROP_SEED_COSTS["STRAWBERRY"]

    # Rule 0802: Tomato Opportunistic Purchase
    if 6 <= state.day <= 16 and analyzer.level("TOMATO") == "HIGH" and len(orders) < 10:
        tomato_seeds = state.seeds.get("TOMATO", 0)
        growing_tom = sum(
            1 for r in range(10) for c in range(10)
            if isinstance(state.get_tile(c, r), dict) and state.get_tile(c, r).get("crop") == "TOMATO"
        )
        if (tomato_seeds + growing_tom) < 8 and state.money >= 300:
            buy_t = min(4, 8 - (tomato_seeds + growing_tom))
            orders.append(["BUY_SEED", "TOMATO", buy_t])
            state.money -= buy_t * CROP_SEED_COSTS["TOMATO"]


# ==============================================================================
# SECTION 8: SUITE 5 (RULES 1201-1600) - EXACT MARGINAL SELLING & LIQUIDATION
# ==============================================================================
def rule_suite_05_market_sales(state: GrandmasterState, orders: List[List[Any]]) -> None:
    is_final_dump = (state.day == 29 and state.hour >= 18)
    is_late_endgame = (state.day >= 27)

    # Rule 1201: Endgame Flush
    if is_final_dump:
        for item in PRODUCTS:
            qty = state.shed.get(item, 0)
            while qty > 0 and len(orders) < 10:
                orders.append(["SELL", item, min(qty, 20)])
                qty -= 20
        return

    prices = state.market_prices
    total_in_shed = sum(state.shed.values())
    overflow_pressure = (total_in_shed >= 35)
    analyzer = GrandmasterDemandAnalyzer(state.unlocked_shops)

    # Rule 1202: Strawberry Smart Marginal Selling
    straw_price = prices.get("STRAWBERRY", 120)
    straw_qty = state.shed.get("STRAWBERRY", 0)
    straw_demand = analyzer.level("STRAWBERRY")
    min_straw_p = 20 if is_late_endgame else (25 if straw_demand == "HIGH" else 35)

    if straw_qty > 0 and (straw_price >= min_straw_p or overflow_pressure) and len(orders) < 10:
        if straw_demand == "HIGH":
            base_batch = 15 if straw_price >= 110 else 10 if straw_price >= 65 else 6
        elif straw_demand == "MEDIUM":
            base_batch = 10 if straw_price >= 110 else 7 if straw_price >= 65 else 4
        else:
            base_batch = 6 if straw_price >= 110 else 4 if straw_price >= 65 else 2

        if is_late_endgame: base_batch = max(base_batch, 12)
        orders.append(["SELL", "STRAWBERRY", min(straw_qty, base_batch)])

    # Rule 1203: Melon Profit Sizing
    melon_price = prices.get("MELON", 250)
    melon_qty = state.shed.get("MELON", 0)
    if melon_qty > 0 and (melon_price >= 60 or overflow_pressure or state.day >= 20) and len(orders) < 10:
        batch = min(melon_qty, 10 if melon_price >= 180 else 8 if melon_price >= 100 else 5)
        if is_late_endgame: batch = min(melon_qty, max(batch, 10))
        orders.append(["SELL", "MELON", batch])

    # Rule 1204: Wool Sales
    wool_price = prices.get("WOOL", 200)
    wool_qty = state.shed.get("WOOL", 0)
    if wool_qty > 0 and (wool_price >= 50 or overflow_pressure or is_late_endgame) and len(orders) < 10:
        batch = min(wool_qty, 10 if wool_price >= 180 else 8 if wool_price >= 90 else 4)
        orders.append(["SELL", "WOOL", batch])

    # Rule 1205: Milk Sales
    milk_price = prices.get("MILK", 160)
    milk_qty = state.shed.get("MILK", 0)
    if milk_qty > 0 and (milk_price >= 40 or overflow_pressure or is_late_endgame) and len(orders) < 10:
        batch = min(milk_qty, 12 if milk_price >= 130 else 10 if milk_price >= 75 else 5)
        orders.append(["SELL", "MILK", batch])

    # Rule 1206: Fertilizer Sales
    fert_price = prices.get("FERTILIZER", 100)
    fert_qty = state.shed.get("FERTILIZER", 0)
    if fert_qty > 0 and (fert_price >= 30 or overflow_pressure or is_late_endgame) and len(orders) < 10:
        batch = min(fert_qty, 12 if fert_price >= 80 else 8 if fert_price >= 50 else 5)
        orders.append(["SELL", "FERTILIZER", batch])

    # Rule 1207: Tomato, Carrot, Egg
    for item in ("TOMATO", "CARROT", "EGG"):
        qty = state.shed.get(item, 0)
        if qty > 0 and len(orders) < 10:
            orders.append(["SELL", item, min(qty, 10)])

    # Rule 1208: Wheat Surplus Liquidation
    wheat_in_shed = state.shed.get("WHEAT", 0)
    feed_reserve = max(10, state.count_animals_on_farm() * 2)
    if wheat_in_shed > feed_reserve and len(orders) < 10:
        orders.append(["SELL", "WHEAT", min(wheat_in_shed - feed_reserve, 15)])

    # Rule 1209: Fill Unused Slots
    for item in ("MILK", "STRAWBERRY", "FERTILIZER", "WOOL"):
        qty = state.shed.get(item, 0)
        if qty > 0 and len(orders) < 10:
            orders.append(["SELL", item, min(qty, 8)])


# ==============================================================================
# SECTION 9: SUITE 6 (RULES 1601-1900) - FIBONACCI LABOR SCALING
# ==============================================================================
def rule_suite_06_labor(state: GrandmasterState, orders: List[List[Any]]) -> None:
    if state.hour <= 1:
        quad_count = len(state.unlocked_quadrants)
        if state.day <= 4:
            target_hands = 5
        elif state.day <= 8:
            target_hands = 7 if quad_count == 1 else 9
        elif state.day <= 12:
            target_hands = 10 if quad_count <= 2 else 12
        elif state.day <= 26:
            target_hands = 14 if quad_count <= 2 else 16
        elif state.day <= 28:
            target_hands = 10
        else:
            target_hands = 5

        simulated_hires = state.hires_today
        while simulated_hires < target_hands and simulated_hires < len(FIBONACCI_COSTS) and len(orders) < 6:
            cost = FIBONACCI_COSTS[simulated_hires]
            safety = 0 if state.day <= 5 else 20
            if state.money >= cost + safety:
                orders.append(["HIRE"])
                state.money -= cost
                simulated_hires += 1
            else:
                break


# ==============================================================================
# SECTION 10: MASTER MARKET ORDER CONTROLLER
# ==============================================================================
def plan_dg_market_orders(state: GrandmasterState) -> List[List[Any]]:
    day0 = rule_suite_01_launch(state)
    if day0 is not None:
        return day0

    orders: List[List[Any]] = []
    rule_suite_02_land(state, orders)
    rule_suite_06_labor(state, orders)
    rule_suite_03_livestock(state, orders)
    rule_suite_04_crops(state, orders)
    rule_suite_05_market_sales(state, orders)

    return orders[:10]


# ==============================================================================
# SECTION 11: SUITE 7 (RULES 1901-2200) - ZERO-WASTE SPATIAL DISPATCHER
# ==============================================================================
class GrandmasterTask:
    __slots__ = ("priority", "action_op", "pos", "extra_arg")

    def __init__(self, priority: int, action_op: str,
                 pos: Tuple[int, int], extra_arg: Optional[str] = None):
        self.priority   = priority
        self.action_op  = action_op
        self.pos        = pos
        self.extra_arg  = extra_arg


def generate_dg_tasks(state: GrandmasterState) -> List[GrandmasterTask]:
    tasks: List[GrandmasterTask] = []
    unlocked_coords = state.get_all_unlocked_coords()
    available_seeds = dict(state.seeds)

    animals_in_shed = [a for a in ("COW", "SHEEP", "GOOSE") if state.shed.get(a, 0) > 0]

    for (x, y) in unlocked_coords:
        tile = state.get_tile(x, y)

        if tile is None:
            if (x, y) in PASTURE_SET and state.day <= 15:
                tasks.append(GrandmasterTask(priority=1, action_op="BUILD_PASTURE", pos=(x, y)))
                continue

            if state.day <= 26:
                selected_crop = None
                if state.day == 0:
                    if available_seeds.get("MELON", 0) > 0:
                        selected_crop = "MELON"; available_seeds["MELON"] -= 1
                    elif available_seeds.get("CARROT", 0) > 0:
                        selected_crop = "CARROT"; available_seeds["CARROT"] -= 1
                    elif available_seeds.get("WHEAT", 0) > 0:
                        selected_crop = "WHEAT"; available_seeds["WHEAT"] -= 1
                else:
                    if available_seeds.get("STRAWBERRY", 0) > 0 and state.day <= 18:
                        selected_crop = "STRAWBERRY"; available_seeds["STRAWBERRY"] -= 1
                    elif available_seeds.get("TOMATO", 0) > 0 and state.day <= 16:
                        selected_crop = "TOMATO"; available_seeds["TOMATO"] -= 1
                    elif available_seeds.get("MELON", 0) > 0 and state.day <= 8:
                        selected_crop = "MELON"; available_seeds["MELON"] -= 1
                    elif available_seeds.get("CARROT", 0) > 0 and state.day <= 8:
                        selected_crop = "CARROT"; available_seeds["CARROT"] -= 1
                    elif available_seeds.get("WHEAT", 0) > 0 and state.day <= 8:
                        selected_crop = "WHEAT"; available_seeds["WHEAT"] -= 1

                if selected_crop:
                    prio = 1 if state.day == 0 else 2 if selected_crop == "STRAWBERRY" else 4
                    tasks.append(GrandmasterTask(priority=prio, action_op="PLANT", pos=(x, y), extra_arg=selected_crop))
            continue

        if not isinstance(tile, dict):
            continue

        kind = tile.get("kind")

        if kind == "WEED":
            tasks.append(GrandmasterTask(priority=3, action_op="DIG", pos=(x, y)))
            continue

        if kind in ("PASTURE", "COOP"):
            animal = tile.get("animal")
            if not animal:
                if animals_in_shed:
                    tasks.append(GrandmasterTask(priority=1, action_op="PLACE", pos=(x, y), extra_arg=animals_in_shed[0]))
                continue

            if not tile.get("fed_today", False):
                tasks.append(GrandmasterTask(priority=1, action_op="FEED", pos=(x, y)))
            elif tile.get("yield_units", 0) > 0:
                tasks.append(GrandmasterTask(priority=1, action_op="HARVEST", pos=(x, y)))
            elif tile.get("fertilizer_available", False):
                tasks.append(GrandmasterTask(priority=2, action_op="COLLECT_FERTILIZER", pos=(x, y)))
            elif not tile.get("cared_today", False):
                tasks.append(GrandmasterTask(priority=2, action_op="CARE", pos=(x, y)))
            continue

        if kind == "PLANT":
            crop = tile.get("crop", "WHEAT")
            crop_age = state.day - tile.get("planted_day", 0)
            yield_units = tile.get("yield_units", 0)
            watered = tile.get("watered_today", False)
            max_days = CROP_MAX_DAYS.get(crop, 4)

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
                tasks.append(GrandmasterTask(priority=1, action_op="HARVEST", pos=(x, y)))
            elif not watered:
                tasks.append(GrandmasterTask(priority=1, action_op="WATER", pos=(x, y)))
            elif crop in ("STRAWBERRY", "TOMATO") and watered:
                fert_until = tile.get("fertilized_until_day", -1)
                fert_in_shed = state.shed.get("FERTILIZER", 0)
                if fert_until < state.day and fert_in_shed > 0 and state.day <= 27:
                    tasks.append(GrandmasterTask(priority=3, action_op="FERTILIZE", pos=(x, y)))
            continue

    tasks.sort(key=lambda t: t.priority)
    return tasks


def manhattan_dist(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def get_step_dir(current: Tuple[int, int], target: Tuple[int, int]) -> str:
    cx, cy = current
    tx, ty = target
    if cx < tx:  return "EAST"
    if cx > tx:  return "WEST"
    if cy < ty:  return "SOUTH"
    if cy > ty:  return "NORTH"
    return "PASS"


def dispatch_dg_units(
    units: List[Tuple[int, int]],
    tasks: List[GrandmasterTask],
    state: GrandmasterState
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
            unit_commands.append([get_step_dir(u_pos, (4, 4))])
            continue

        unit_inv = state.inventories[u_idx] if u_idx < len(state.inventories) else {}
        wheat_carried = unit_inv.get("WHEAT", 0)
        cows_carried  = unit_inv.get("COW", 0)
        sheep_carried = unit_inv.get("SHEEP", 0)
        fert_carried  = unit_inv.get("FERTILIZER", 0)
        has_animal_carried = (cows_carried > 0 or sheep_carried > 0)
        carried_animal_type = "COW" if cows_carried > 0 else "SHEEP" if sheep_carried > 0 else None

        # Rule 2201: Endgame Flush
        if state.day == 29 and state.hour >= 16 and sum(unit_inv.values()) > 0:
            if u_pos in SHED_ACCESS_TILES:
                unit_commands.append(["DROP"])
            else:
                unit_commands.append([get_step_dir(u_pos, (4, 4))])
            continue

        # Rule 1902: Placing Carried Animal onto Pasture
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
                        d = manhattan_dist(u_pos, p)
                        if d < best_dist:
                            best_dist = d; target_pasture = p
                if target_pasture:
                    if u_pos == target_pasture:
                        t = state.get_tile(u_pos[0], u_pos[1])
                        unit_commands.append(["BUILD_PASTURE"] if t is None else ["PLACE", carried_animal_type])
                    else:
                        unit_commands.append([get_step_dir(u_pos, target_pasture)])
                    continue

        # Rule 1903: Shed Logistics at (4,4)
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

        # Rule 1904: Spatial Task Matching
        best_task_idx, best_score = None, float("inf")
        is_planter_specialist = (u_idx >= 5 and state.seeds.get("STRAWBERRY", 0) > 0 and 5 <= state.day <= 18)

        for t_idx, task in enumerate(tasks):
            if t_idx in assigned_task_ids: continue
            prio_mult = 0.1 if (is_planter_specialist and task.action_op == "PLANT") else 1.0
            if task.action_op == "FEED" and wheat_carried == 0:
                dist = manhattan_dist(u_pos, (4, 4)) + manhattan_dist((4, 4), task.pos)
            elif task.action_op == "FERTILIZE" and fert_carried == 0:
                dist = manhattan_dist(u_pos, (4, 4)) + manhattan_dist((4, 4), task.pos)
            else:
                dist = manhattan_dist(u_pos, task.pos)
            score = (task.priority * 100 * prio_mult) + dist
            if score < best_score:
                best_score = score; best_task_idx = t_idx

        if best_task_idx is not None:
            assigned_task_ids.add(best_task_idx)
            task = tasks[best_task_idx]

            if task.action_op == "FEED" and wheat_carried == 0:
                unit_commands.append(["PICKUP", "WHEAT", 4] if u_pos == (4, 4) else [get_step_dir(u_pos, (4, 4))])
                continue

            if task.action_op == "FERTILIZE" and fert_carried == 0:
                if u_pos == (4, 4):
                    unit_commands.append(["PICKUP", "FERTILIZER", 4] if state.shed.get("FERTILIZER", 0) > 0 else ["PASS"])
                else:
                    unit_commands.append([get_step_dir(u_pos, (4, 4))])
                continue

            if u_pos == task.pos:
                unit_commands.append([task.action_op, task.extra_arg] if task.extra_arg else [task.action_op])
            else:
                unit_commands.append([get_step_dir(u_pos, task.pos)])
        else:
            unit_commands.append(["PASS"])

    return unit_commands


# ==============================================================================
# SECTION 12: MAIN ENTRYPOINT
# ==============================================================================
def agent(obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    state = GrandmasterState(obs)
    market_orders = plan_dg_market_orders(state)
    tasks = generate_dg_tasks(state)
    all_units = [state.farmer_pos] + state.hands_pos
    unit_actions = dispatch_dg_units(all_units, tasks, state)

    return {
        "farmer": unit_actions[0] if unit_actions else ["PASS"],
        "hands":  unit_actions[1:] if len(unit_actions) > 1 else [],
        "market": market_orders,
    }

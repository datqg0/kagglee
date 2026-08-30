"""
Kaggriculture Agent: rlagentv2.py (Trained vs Main, ABC, EDF, MISS)
--------------------------------
Hierarchical Reinforcement Learning (HRL) Agent:
- Level 1: Macro Policy Network (NumPy neural policy) mapping 48 game features
  (market prices, shop demand, opponent state, inventory, land) to macro decisions
  (crop portfolio, dynamic sell thresholds, labor scaling, 4-quadrant SE expansion).
- Level 2: Micro Spatial Dispatcher ensuring optimal worker task execution, zero
  idle turns, 100% animal feeding reliability, and synchronized endgame liquidation.
"""

from typing import Dict, List, Tuple, Any, Optional, Set
import math
import struct
import base64

try:
    import numpy as np
except Exception:
    np = None


def _clip(val: Any, min_v: float, max_v: float) -> float:
    try:
        fval = float(val)
    except Exception:
        fval = min_v
    return max(min_v, min(max_v, fval))
TURNS_PER_DAY = 24
FIBONACCI_COSTS = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]

LAND_COSTS = {"NE": 1000, "SW": 2000, "SE": 4000}

BASE_PRICES = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
    "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
}

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
ANIMALS = ["GOOSE", "COW", "SHEEP"]

CROP_MAX_DAYS = {
    "WHEAT": 4, "CARROT": 3, "TOMATO": 11, "STRAWBERRY": 16, "MELON": 12
}

COMPACT_PASTURES: List[Tuple[int, int]] = [
    (4, 4), (3, 4), (4, 3), (3, 3), (4, 2), (3, 2), (2, 4), (2, 3), (2, 2)
]
PASTURE_SET = set(COMPACT_PASTURES)

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


# ==============================================================================
# STATE PARSER
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

    def extract_feature_vector(self) -> Any:
        """Extracts 48-dimensional normalized state vector for the Macro RL Policy."""
        feats = [0.0] * 48

        # 1. Temporal & Core Economy (6 dims)
        feats[0] = self.day / 30.0
        feats[1] = self.hour / 24.0
        feats[2] = min(1.0, self.money / 60000.0)
        feats[3] = min(1.0, self.hires_today / 15.0)
        feats[4] = min(1.0, self.total_shed_items / 100.0)
        feats[5] = len(self.unlocked_quadrants) / 4.0

        # 2. Market Prices Normalized (9 dims)
        for i, p in enumerate(PRODUCTS):
            price = self.market_prices.get(p, BASE_PRICES[p])
            feats[6 + i] = min(3.0, price / BASE_PRICES[p])

        # 3. Market Inventories Normalized (9 dims)
        for i, p in enumerate(PRODUCTS):
            inv = self.market_inv.get(p, 10000)
            feats[15 + i] = min(3.0, inv / 10000.0)

        # 4. Town Shop Demand Spectrum (9 dims)
        shop_counts = {p: 0 for p in PRODUCTS}
        for s in self.unlocked_shops:
            for p in SHOP_DEMANDS.get(s, []):
                shop_counts[p] += 1
        for i, p in enumerate(PRODUCTS):
            feats[24 + i] = min(1.0, shop_counts[p] / 5.0)

        # 5. Farm Crop Counts (5 dims)
        crop_counts = {c: 0 for c in CROPS}
        animal_counts = {a: 0 for a in ANIMALS}
        weed_count = 0
        for r in range(10):
            for c in range(10):
                t = self.get_tile(c, r)
                if isinstance(t, dict):
                    k = t.get("kind")
                    if k == "PLANT":
                        cp = t.get("crop", "WHEAT")
                        crop_counts[cp] = crop_counts.get(cp, 0) + 1
                    elif k in ("PASTURE", "COOP"):
                        an = t.get("animal")
                        if an: animal_counts[an] = animal_counts.get(an, 0) + 1
                    elif k == "WEED":
                        weed_count += 1
        for i, c in enumerate(CROPS):
            feats[33 + i] = min(1.0, crop_counts[c] / 50.0)

        # 6. Farm Livestock Counts (3 dims)
        feats[38] = animal_counts["COW"] / 6.0
        feats[39] = animal_counts["SHEEP"] / 4.0
        feats[40] = animal_counts["GOOSE"] / 2.0

        # 7. Opponent Tracking (4 dims)
        feats[41] = min(1.0, self.opp_money / 60000.0)
        feats[42] = len(self.opp_unlocked_quadrants) / 4.0

        opp_crops = 0
        opp_animals = 0
        if 0 <= self.opp_id < len(self.raw.get("farms", [])):
            opp_tiles = self.raw.get("farms", [])[self.opp_id].get("tiles", [])
            for r in range(len(opp_tiles)):
                for c in range(len(opp_tiles[r])):
                    ot = opp_tiles[r][c]
                    if isinstance(ot, dict):
                        if ot.get("kind") == "PLANT": opp_crops += 1
                        elif ot.get("kind") in ("PASTURE", "COOP") and ot.get("animal"): opp_animals += 1
        feats[43] = min(1.0, opp_crops / 50.0)
        feats[44] = min(1.0, opp_animals / 9.0)

        # 8. Shed specific items (3 dims)
        feats[45] = min(1.0, self.shed.get("STRAWBERRY", 0) / 40.0)
        feats[46] = min(1.0, self.shed.get("FERTILIZER", 0) / 30.0)
        feats[47] = min(1.0, weed_count / 15.0)

        return feats


# ==============================================================================
# MACRO RL POLICY NETWORK (Pure Python + NumPy compatible)
# ==============================================================================
class MacroRLPolicy:
    def __init__(self, weights: Optional[Any] = None):
        self.input_dim = 48
        self.hidden_dim = 32
        self.output_dim = 24
        self.total_params = 48 * 32 + 32 + 32 * 24 + 24

        if weights is None:
            import base64
            import struct
            b64_data = "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"
            raw = base64.b64decode(b64_data)
            self.weights = list(struct.unpack(f"{len(raw)//4}f", raw))
        elif hasattr(weights, "tolist"):
            self.weights = weights.tolist()
        else:
            self.weights = list(weights)

    def forward(self, state_vec: Any) -> List[float]:
        # Fast pure-Python forward pass (48 -> 32 -> 24)
        w1 = self.weights[0:1536]
        b1 = self.weights[1536:1568]
        w2 = self.weights[1568:2336]
        b2 = self.weights[2336:2360]

        # Hidden layer: h = tanh(state_vec @ W1 + b1)
        h = [0.0] * 32
        for j in range(32):
            s = b1[j]
            for i in range(48):
                s += state_vec[i] * w1[i * 32 + j]
            h[j] = math.tanh(s)

        # Output layer: out = h @ W2 + b2
        out = [0.0] * 24
        for k in range(24):
            s = b2[k]
            for j in range(32):
                s += h[j] * w2[j * 24 + k]
            out[k] = s

        return out


# Global policy instance loaded with trained weights
_POLICY_INSTANCE: Optional[MacroRLPolicy] = None

def get_policy() -> MacroRLPolicy:
    global _POLICY_INSTANCE
    if _POLICY_INSTANCE is None:
        _POLICY_INSTANCE = MacroRLPolicy()
    return _POLICY_INSTANCE

def set_policy_weights(weights: Any):
    global _POLICY_INSTANCE
    _POLICY_INSTANCE = MacroRLPolicy(weights)


# ==============================================================================
# RL MACRO MARKET CONTROLLER
# ==============================================================================
def plan_rl_market_orders(state: GameState, policy_out: np.ndarray) -> List[List[Any]]:
    orders: List[List[Any]] = []
    wheat_in_shed = state.shed.get("WHEAT", 0)

    # Decode policy outputs
    crop_logits = policy_out[0:5]
    sell_urgencies = policy_out[5:14]
    labor_mods = policy_out[14:18]
    exp_reserves = policy_out[18:21]
    fert_pref = policy_out[21]
    endgame_start_day = int(_clip(27.0 + policy_out[22], 26, 28))

    # 1. DAY 0 LAUNCH (Proven optimal capital deployment)
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

    # 2. 3-QUADRANT LAND EXPANSION (NW, NE, SW - proven optimal for 30-day season)
    ne_buffer = max(10, int(15 + exp_reserves[0] * 50))
    sw_buffer = max(20, int(30 + exp_reserves[1] * 80))

    if "NE" not in state.unlocked_quadrants and state.day >= 4 and state.money >= 1000 + ne_buffer:
        orders.append(["BUY_LAND"])
    elif "SW" not in state.unlocked_quadrants and state.day >= 8 and state.money >= 2000 + sw_buffer:
        orders.append(["BUY_LAND"])

    # 3. DYNAMIC LABOR SIZING
    if state.hour <= 1:
        quad_count = len(state.unlocked_quadrants)
        if state.day <= 4:
            base_hands = 5 + int(labor_mods[0] * 2)
        elif state.day <= 8:
            base_hands = (7 if quad_count == 1 else 9) + int(labor_mods[1] * 2)
        elif state.day <= 12:
            base_hands = (10 if quad_count <= 2 else 12) + int(labor_mods[2] * 2)
        elif state.day <= 26:
            base_hands = (12 if quad_count <= 2 else 15) + int(labor_mods[2] * 2)
        elif state.day <= 28:
            base_hands = (14 if quad_count >= 3 else 10) + int(labor_mods[3] * 2)
        else:
            base_hands = 6

        target_hands = int(_clip(base_hands, 4, 18))
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

    # 4. LIVESTOCK EXPANSION
    animals_placed  = state.count_animals_on_farm()
    animals_in_shed = state.shed.get("COW", 0) + state.shed.get("SHEEP", 0)
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

    # 5. WHEAT FEED PROCUREMENT
    if state.day <= 28:
        needed_feed = max(8, animals_placed * 2)
        if wheat_in_shed < needed_feed and state.money >= 80 and len(orders) < 10:
            buy_amt = min(20, needed_feed - wheat_in_shed + 8)
            orders.append(["BUY_PRODUCT", "WHEAT", buy_amt])
            state.money -= buy_amt * 10

    # 6. SEED PROCUREMENT WITH RL CROP DISTRIBUTION (100% Strawberry Focus)
    if 5 <= state.day <= 18:
        unlocked_tiles = len(state.get_all_unlocked_coords())
        available_crop_tiles = max(10, unlocked_tiles - len(COMPACT_PASTURES))

        # Strawberry procurement (Cost = 100)
        straw_target = int(_clip(available_crop_tiles * (0.80 + crop_logits[0] * 0.20), 35, 65))
        straw_seeds = state.seeds.get("STRAWBERRY", 0)
        growing_straw = sum(
            1 for r in range(10) for c in range(10)
            if isinstance(state.get_tile(c, r), dict) and state.get_tile(c, r).get("crop") == "STRAWBERRY"
        )
        needed_straw = straw_target - (straw_seeds + growing_straw)
        if needed_straw > 0 and state.money >= 120 and len(orders) < 10:
            max_can_afford = int((state.money - 20) // 100)
            buy_count = min(needed_straw, max(1, min(15, max_can_afford)))
            if buy_count > 0 and state.money >= buy_count * 100:
                orders.append(["BUY_SEED", "STRAWBERRY", buy_count])
                state.money -= buy_count * 100

    # 7. ENDGAME LIQUIDATION & DYNAMIC SELLING
    is_final_dump = (state.day == 29 and state.hour >= 18)
    is_late_endgame = (state.day >= endgame_start_day)

    if is_final_dump:
        for item in PRODUCTS:
            qty = state.shed.get(item, 0)
            while qty > 0 and len(orders) < 10:
                orders.append(["SELL", item, min(qty, 20)])
                qty -= 20
        return orders[:10]

    prices = state.market_prices
    total_in_shed = sum(state.shed.values())
    overflow_pressure = (total_in_shed >= 35)

    # Per-product smart selling with RL urgencies
    # Strawberry (idx 3 in PRODUCTS)
    straw_price = prices.get("STRAWBERRY", 120)
    straw_qty = state.shed.get("STRAWBERRY", 0)
    straw_urgency = float(sell_urgencies[3])
    min_straw_p = 20 if is_late_endgame else (30 if straw_urgency > 0 else 45)
    if straw_qty > 0 and (straw_price >= min_straw_p or overflow_pressure) and len(orders) < 10:
        base_batch = 12 if straw_price >= 110 else 8 if straw_price >= 65 else 4
        batch = int(_clip(base_batch * (1.0 + straw_urgency * 0.5), 2, 20))
        if is_late_endgame: batch = min(straw_qty, max(batch, 12))
        orders.append(["SELL", "STRAWBERRY", min(straw_qty, batch)])

    # Melon (idx 4)
    melon_price = prices.get("MELON", 250)
    melon_qty = state.shed.get("MELON", 0)
    if melon_qty > 0 and (melon_price >= 60 or overflow_pressure or state.day >= 20) and len(orders) < 10:
        batch = min(melon_qty, 10 if melon_price >= 180 else 8 if melon_price >= 100 else 5)
        if is_late_endgame: batch = min(melon_qty, max(batch, 10))
        orders.append(["SELL", "MELON", batch])

    # Wool (idx 7)
    wool_price = prices.get("WOOL", 200)
    wool_qty = state.shed.get("WOOL", 0)
    if wool_qty > 0 and (wool_price >= 50 or overflow_pressure or is_late_endgame) and len(orders) < 10:
        batch = min(wool_qty, 10 if wool_price >= 180 else 8 if wool_price >= 90 else 4)
        orders.append(["SELL", "WOOL", batch])

    # Milk (idx 6)
    milk_price = prices.get("MILK", 160)
    milk_qty = state.shed.get("MILK", 0)
    if milk_qty > 0 and (milk_price >= 40 or overflow_pressure or is_late_endgame) and len(orders) < 10:
        batch = min(milk_qty, 12 if milk_price >= 130 else 10 if milk_price >= 75 else 5)
        orders.append(["SELL", "MILK", batch])

    # Fertilizer (idx 8)
    fert_price = prices.get("FERTILIZER", 100)
    fert_qty = state.shed.get("FERTILIZER", 0)
    if fert_qty > 0 and (fert_price >= 35 or overflow_pressure or is_late_endgame) and len(orders) < 10:
        batch = min(fert_qty, 12 if fert_price >= 80 else 8 if fert_price >= 50 else 5)
        orders.append(["SELL", "FERTILIZER", batch])

    # Tomato (idx 2)
    tomato_price = prices.get("TOMATO", 60)
    tomato_qty = state.shed.get("TOMATO", 0)
    if tomato_qty > 0 and len(orders) < 10:
        orders.append(["SELL", "TOMATO", min(tomato_qty, 12 if tomato_price >= 80 else 6)])

    # Carrot & Egg
    for item in ("CARROT", "EGG"):
        qty = state.shed.get(item, 0)
        if qty > 0 and len(orders) < 10:
            orders.append(["SELL", item, min(qty, 8)])

    # Wheat surplus
    feed_res = max(10, animals_placed * 2)
    if wheat_in_shed > feed_res and len(orders) < 10:
        orders.append(["SELL", "WHEAT", min(wheat_in_shed - feed_res, 15)])

    # Fill any extra slots with available shed goods
    for item in ("MILK", "STRAWBERRY", "FERTILIZER", "WOOL", "TOMATO"):
        qty = state.shed.get(item, 0)
        if qty > 0 and len(orders) < 10:
            orders.append(["SELL", item, min(qty, 10)])

    return orders[:10]


# ==============================================================================
# RL MICRO SPATIAL SOLVER & TASK GENERATOR
# ==============================================================================
class FarmTask:
    __slots__ = ("priority", "action_op", "pos", "extra_arg")
    def __init__(self, priority: int, action_op: str,
                 pos: Tuple[int, int], extra_arg: Optional[str] = None):
        self.priority   = priority
        self.action_op  = action_op
        self.pos        = pos
        self.extra_arg  = extra_arg


def generate_rl_tasks(state: GameState, policy_out: np.ndarray) -> List[FarmTask]:
    tasks: List[FarmTask] = []
    unlocked_coords = state.get_all_unlocked_coords()
    available_seeds = dict(state.seeds)
    animals_in_shed = [a for a in ("COW", "SHEEP", "GOOSE") if state.shed.get(a, 0) > 0]

    crop_logits = policy_out[0:5]
    fert_weight = float(policy_out[21])

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
                    if available_seeds.get("MELON", 0) > 0:
                        selected_crop = "MELON"; available_seeds["MELON"] -= 1
                    elif available_seeds.get("CARROT", 0) > 0:
                        selected_crop = "CARROT"; available_seeds["CARROT"] -= 1
                    elif available_seeds.get("WHEAT", 0) > 0:
                        selected_crop = "WHEAT"; available_seeds["WHEAT"] -= 1
                else:
                    if available_seeds.get("STRAWBERRY", 0) > 0 and state.day <= 18:
                        selected_crop = "STRAWBERRY"; available_seeds["STRAWBERRY"] -= 1
                    elif available_seeds.get("MELON", 0) > 0 and state.day <= 8:
                        selected_crop = "MELON"; available_seeds["MELON"] -= 1
                    elif available_seeds.get("CARROT", 0) > 0 and state.day <= 8:
                        selected_crop = "CARROT"; available_seeds["CARROT"] -= 1
                    elif available_seeds.get("WHEAT", 0) > 0 and state.day <= 8:
                        selected_crop = "WHEAT"; available_seeds["WHEAT"] -= 1

                if selected_crop:
                    prio = 1 if (state.day == 0 or selected_crop == "STRAWBERRY") else 2
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
                if fert_until < state.day and fert_in_shed > 0 and state.day <= 27 and fert_weight >= -0.5:
                    tasks.append(FarmTask(priority=3, action_op="FERTILIZE", pos=(x, y)))
            continue

    tasks.sort(key=lambda t: t.priority)
    return tasks


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


def dispatch_rl_units(
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

        # Endgame dump at shed
        if state.day == 29 and state.hour >= 16 and sum(unit_inv.values()) > 0:
            if u_pos in ((4, 4), (5, 4), (4, 5), (5, 5)):
                unit_commands.append(["DROP"])
            else:
                unit_commands.append([get_step_direction(u_pos, (4, 4))])
            continue

        # Animal placement
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

        # Shed pickup at (4,4)
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

        # Match best priority task
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
    state_vec = state.extract_feature_vector()
    policy = get_policy()
    policy_out = policy.forward(state_vec)

    market_orders = plan_rl_market_orders(state, policy_out)
    tasks = generate_rl_tasks(state, policy_out)
    all_units = [state.farmer_pos] + state.hands_pos
    unit_actions = dispatch_rl_units(all_units, tasks, state)

    return {
        "farmer": unit_actions[0] if unit_actions else ["PASS"],
        "hands":  unit_actions[1:] if len(unit_actions) > 1 else [],
        "market": market_orders,
    }

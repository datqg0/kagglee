"""
Kaggriculture Local Simulation Engine
------------------------------------
Implements exact simulation mechanics from README.md to benchmark and audit main.py locally.
"""

import math
import copy
from typing import Dict, List, Any, Optional

MARKET_PARAMS = {
    "WHEAT": {"base": 25, "I0": 10000, "T": 400, "below_func": "sqrt", "below_target": 0.80, "above_func": "log", "above_target": 0.20},
    "CARROT": {"base": 35, "I0": 10000, "T": 450, "below_func": "hinge", "below_target": 1.00, "above_func": "sqrt", "above_target": 0.70},
    "TOMATO": {"base": 60, "I0": 10000, "T": 200, "below_func": "hinge", "below_target": 0.40, "above_func": "sqrt", "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": 10000, "T": 100, "below_func": "sqrt", "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON": {"base": 250, "I0": 10000, "T": 300, "below_func": "log", "below_target": 0.20, "above_func": "sq", "above_target": 3.60},
    "EGG": {"base": 50, "I0": 10000, "T": 332, "below_func": "hinge", "below_target": 0.40, "above_func": "log", "above_target": 0.20},
    "MILK": {"base": 160, "I0": 10000, "T": 122, "below_func": "sqrt", "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL": {"base": 200, "I0": 10000, "T": 105, "below_func": "log", "below_target": 0.20, "above_func": "sq", "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": 10000, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]

SEED_PRICES = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
ANIMAL_PRICES = {"GOOSE": 300, "COW": 400, "SHEEP": 500}

def eval_f(func_name: str, x: float, T: float) -> float:
    if func_name == "linear":
        return x
    elif func_name == "sq":
        return x ** 2
    elif func_name == "sqrt":
        return math.sqrt(x)
    elif func_name == "log":
        return math.log(1.0 + x)
    elif func_name == "hinge":
        u = x / T
        return u + 8.0 * (max(0.0, u - 1.0) ** 2)
    return x

def calc_price(item: str, inv: int) -> int:
    params = MARKET_PARAMS.get(item)
    if not params:
        return 1
    base = params["base"]
    I0 = params["I0"]
    T = params["T"]
    
    if inv == I0:
        return base
    elif inv < I0:
        # Scarcity
        diff = I0 - inv
        f_val = eval_f(params["below_func"], diff, T)
        f_T = eval_f(params["below_func"], T, T)
        amp = (params["below_target"] * base) / (f_T if f_T != 0 else 1.0)
        p = base + amp * f_val
    else:
        # Glut
        diff = inv - I0
        f_val = eval_f(params["above_func"], diff, T)
        f_T = eval_f(params["above_func"], T, T)
        amp = (params["above_target"] * base) / (f_T if f_T != 0 else 1.0)
        p = base - amp * f_val
        
    return max(1, round(p))


class Simulation:
    def __init__(self, agent0_fn, agent1_fn):
        self.agents = [agent0_fn, agent1_fn]
        self.step = 0
        self.day = 0
        self.hour = 0
        self.market_inv = {k: 10000 for k in MARKET_PARAMS}
        self.town_shops = ["BAKERY", "YARN_STORE"]
        
        self.farms = []
        self.privates = []
        for _ in range(2):
            self.farms.append({
                "money": 3000.0,
                "tiles": [[None]*10 for _ in range(10)],
                "farmer": [4, 4],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0
            })
            for r in range(10):
                for c in range(10):
                    if r >= 5 or c >= 5:
                        self.farms[-1]["tiles"][r][c] = "LOCKED"
            self.privates.append({
                "shed": {},
                "seeds": {},
                "inventories": [{}]
            })

    def run_step(self):
        prices = {k: calc_price(k, self.market_inv[k]) for k in MARKET_PARAMS}
        
        # Build observations
        obs = []
        for p in range(2):
            obs.append({
                "player": p,
                "step": self.step,
                "day": self.day,
                "hour": self.hour,
                "farms": copy.deepcopy(self.farms),
                "market": {"inventory": dict(self.market_inv), "prices": dict(prices)},
                "town": {"unlocked_shops": list(self.town_shops)},
                "private": copy.deepcopy(self.privates[p])
            })
        
        # Get actions
        actions = []
        for p in range(2):
            try:
                act = self.agents[p](obs[p])
            except Exception as e:
                # print(f"Agent {p} exception at step {self.step}: {e}")
                act = {"farmer": ["PASS"], "hands": [], "market": []}
            actions.append(act)
        
        # 1. Process Market Orders
        for p in range(2):
            farm = self.farms[p]
            priv = self.privates[p]
            market_ops = actions[p].get("market", [])[:10]
            for op in market_ops:
                if not op:
                    continue
                cmd = op[0]
                if cmd == "HIRE":
                    cost = FIBONACCI[farm["hires_today"]] if farm["hires_today"] < len(FIBONACCI) else 233
                    if farm["money"] >= cost:
                        farm["money"] -= cost
                        farm["hires_today"] += 1
                        # Spawn hand adjacent to shed
                        spawn_pos = [5, 4] if len(farm["hands"]) == 0 else [4, 5] if len(farm["hands"]) == 1 else [5, 5]
                        farm["hands"].append(spawn_pos)
                        priv["inventories"].append({})
                elif cmd == "BUY_LAND":
                    unlocked = farm["unlocked_quadrants"]
                    if "NE" not in unlocked and farm["money"] >= 1000:
                        farm["money"] -= 1000
                        unlocked.append("NE")
                        for r in range(5):
                            for c in range(5, 10):
                                farm["tiles"][r][c] = None
                    elif "SW" not in unlocked and farm["money"] >= 2000:
                        farm["money"] -= 2000
                        unlocked.append("SW")
                        for r in range(5, 10):
                            for c in range(5):
                                farm["tiles"][r][c] = None
                    elif "SE" not in unlocked and farm["money"] >= 4000:
                        farm["money"] -= 4000
                        unlocked.append("SE")
                        for r in range(5, 10):
                            for c in range(5, 10):
                                farm["tiles"][r][c] = None
                elif cmd == "BUY_ANIMAL":
                    animal = op[1]
                    qty = op[2] if len(op) > 2 else 1
                    cost = ANIMAL_PRICES.get(animal, 300) * qty
                    if farm["money"] >= cost:
                        farm["money"] -= cost
                        priv["shed"][animal] = priv["shed"].get(animal, 0) + qty
                elif cmd == "BUY_SEED":
                    crop = op[1]
                    qty = op[2] if len(op) > 2 else 1
                    cost = SEED_PRICES.get(crop, 10) * qty
                    if farm["money"] >= cost:
                        farm["money"] -= cost
                        priv["seeds"][crop] = priv["seeds"].get(crop, 0) + qty
                elif cmd == "BUY_PRODUCT":
                    item = op[1]
                    qty = op[2] if len(op) > 2 else 1
                    p_price = calc_price(item, self.market_inv[item])
                    total_c = p_price * qty
                    if farm["money"] >= total_c:
                        farm["money"] -= total_c
                        priv["shed"][item] = priv["shed"].get(item, 0) + qty
                        self.market_inv[item] = max(1, self.market_inv[item] - qty)
                elif cmd == "SELL":
                    item = op[1]
                    qty = op[2] if len(op) > 2 else 1
                    in_shed = priv["shed"].get(item, 0)
                    actual_sell = min(in_shed, qty)
                    if actual_sell > 0:
                        priv["shed"][item] -= actual_sell
                        s_price = calc_price(item, self.market_inv.get(item, 10000))
                        revenue = s_price * actual_sell
                        farm["money"] += revenue
                        if item in self.market_inv:
                            self.market_inv[item] += actual_sell

        # 2. Process Spatial Unit Actions
        for p in range(2):
            farm = self.farms[p]
            priv = self.privates[p]
            units = [farm["farmer"]] + farm["hands"]
            u_acts = [actions[p].get("farmer", ["PASS"])] + actions[p].get("hands", [])
            
            for u_idx, pos in enumerate(units):
                if u_idx >= len(u_acts) or not u_acts[u_idx]:
                    continue
                act = u_acts[u_idx]
                cmd = act[0]
                inv = priv["inventories"][u_idx]
                
                # Movement
                if cmd == "NORTH" and pos[1] > 0:
                    pos[1] -= 1
                elif cmd == "SOUTH" and pos[1] < 9:
                    pos[1] += 1
                elif cmd == "WEST" and pos[0] > 0:
                    pos[0] -= 1
                elif cmd == "EAST" and pos[0] < 9:
                    pos[0] += 1
                
                # Shed Interaction (adjacent to shed: (4,4), (4,5), (5,4), (5,5))
                is_shed_adj = pos in ([4, 4], [4, 5], [5, 4], [5, 5])
                if cmd == "PICKUP" and is_shed_adj:
                    item = act[1]
                    n = act[2] if len(act) > 2 else 1
                    avail = priv["shed"].get(item, 0)
                    take = min(avail, n)
                    if take > 0:
                        priv["shed"][item] -= take
                        inv[item] = inv.get(item, 0) + take
                elif cmd == "DROP" and is_shed_adj:
                    for k, v in list(inv.items()):
                        priv["shed"][k] = priv["shed"].get(k, 0) + v
                        inv[k] = 0
                
                # Tile Interactions
                x, y = pos[0], pos[1]
                tile = farm["tiles"][y][x]
                if tile != "LOCKED":
                    if cmd == "BUILD_PASTURE" and tile is None:
                        farm["tiles"][y][x] = {
                            "kind": "PASTURE", "animal": None, "placed_day": self.day,
                            "yield_units": 0, "fed_today": False, "cared_today": False,
                            "fertilizer_available": False, "pending_care_bonus": 0
                        }
                    elif cmd == "PLACE" and isinstance(tile, dict) and tile.get("kind") == "PASTURE" and not tile.get("animal"):
                        animal = act[1] if len(act) > 1 else "COW"
                        if inv.get(animal, 0) > 0:
                            inv[animal] -= 1
                            tile["animal"] = animal
                            tile["placed_day"] = self.day
                    elif cmd == "PLANT" and tile is None:
                        crop = act[1] if len(act) > 1 else "WHEAT"
                        if priv["seeds"].get(crop, 0) > 0:
                            priv["seeds"][crop] -= 1
                            farm["tiles"][y][x] = {
                                "kind": "PLANT", "crop": crop, "planted_day": self.day,
                                "watered_today": False, "consecutive_unwatered": 1,
                                "yield_units": 0, "max_lifespan_step": (self.day + 10) * 24
                            }
                    elif cmd == "WATER" and isinstance(tile, dict) and tile.get("kind") == "PLANT":
                        if not tile.get("watered_today", False):
                            tile["watered_today"] = True
                            tile["consecutive_unwatered"] = 0
                            # Bonus watering
                            tile["yield_units"] = tile.get("yield_units", 0) + 1
                    elif cmd == "FEED" and isinstance(tile, dict) and tile.get("kind") == "PASTURE" and tile.get("animal"):
                        if inv.get("WHEAT", 0) > 0 and not tile.get("fed_today", False):
                            inv["WHEAT"] -= 1
                            tile["fed_today"] = True
                    elif cmd == "CARE" and isinstance(tile, dict) and tile.get("kind") == "PASTURE" and tile.get("animal"):
                        if not tile.get("cared_today", False):
                            tile["cared_today"] = True
                            tile["pending_care_bonus"] += 1
                    elif cmd == "COLLECT_FERTILIZER" and isinstance(tile, dict) and tile.get("fertilizer_available", False):
                        tile["fertilizer_available"] = False
                        inv["FERTILIZER"] = inv.get("FERTILIZER", 0) + 1
                    elif cmd == "HARVEST":
                        if isinstance(tile, dict):
                            if tile.get("kind") == "PLANT" and tile.get("yield_units", 0) > 0:
                                crop = tile.get("crop", "WHEAT")
                                y_qty = tile["yield_units"]
                                inv[crop] = inv.get(crop, 0) + y_qty
                                farm["tiles"][y][x] = None  # One-time harvested
                            elif tile.get("kind") == "PASTURE" and tile.get("yield_units", 0) > 0:
                                prod = "WOOL" if tile.get("animal") == "SHEEP" else "MILK"
                                y_qty = tile["yield_units"]
                                inv[prod] = inv.get(prod, 0) + y_qty
                                tile["yield_units"] = 0
                    elif cmd == "DIG" and isinstance(tile, dict):
                        if tile.get("kind") == "WEED":
                            farm["tiles"][y][x] = None

        # 3. Town Shops & Town Center Consumption (every 4 turns)
        if self.step % 4 == 0:
            for shop in self.town_shops:
                if shop == "BAKERY":
                    self.market_inv["WHEAT"] = max(1, self.market_inv["WHEAT"] - 1)
                    self.market_inv["EGG"] = max(1, self.market_inv["EGG"] - 1)
                elif shop == "YARN_STORE":
                    self.market_inv["WOOL"] = max(1, self.market_inv["WOOL"] - 2)

        # 4. End of Day Refresh
        if self.hour == 23:
            for p in range(2):
                farm = self.farms[p]
                priv = self.privates[p]
                # Dump inventories into shed
                for inv in priv["inventories"]:
                    for k, v in list(inv.items()):
                        priv["shed"][k] = priv["shed"].get(k, 0) + v
                        inv[k] = 0
                # Reset hands & farmer
                farm["hands"] = []
                priv["inventories"] = [{}]
                farm["farmer"] = [4, 4]
                farm["hires_today"] = 0
                
                # Animal daily ticks
                for r in range(10):
                    for c in range(10):
                        t = farm["tiles"][r][c]
                        if isinstance(t, dict) and t.get("kind") == "PASTURE" and t.get("animal"):
                            t["fertilizer_available"] = True
                            if t.get("fed_today"):
                                animal = t.get("animal")
                                interval = 3 if animal == "SHEEP" else 2 if animal == "COW" else 1
                                if (self.day - t.get("placed_day", 0)) % interval == 0:
                                    base_yield = 1 + (t.get("pending_care_bonus", 0) if t.get("cared_today") else 0)
                                    t["yield_units"] = min(6, t.get("yield_units", 0) + base_yield)
                                    t["pending_care_bonus"] = 0
                            t["fed_today"] = False
                            t["cared_today"] = False
                        elif isinstance(t, dict) and t.get("kind") == "PLANT":
                            t["watered_today"] = False

            self.day += 1
            self.hour = 0
        else:
            self.hour += 1

        self.step += 1

    def run_all(self):
        for _ in range(720):
            self.run_step()
        return [f["money"] for f in self.farms]

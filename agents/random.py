import random

CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
CROP_COSTS = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
FARMER_OPS = ["NORTH", "SOUTH", "EAST", "WEST", "PASS", "WATER", "HARVEST", "FERTILIZE", "DIG", "FEED", "CARE", "COLLECT_FERTILIZER"]

def agent(obs):
    farms = obs.get("farms", [])
    player = obs.get("player", 0)
    private = obs.get("private", {}) or {}
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    farm = farms[player]
    seeds = private.get("seeds", {})
    shed = private.get("shed", {})

    market = []
    for item, count in shed.items():
        if count > 0 and random.random() < 0.2:
            market.append(["SELL", item, count])

    affordable = [c for c in CROPS if CROP_COSTS[c] <= farm["money"]]
    if affordable and random.random() < 0.1:
        market.append(["BUY_SEED", random.choice(affordable), 1])

    available_seeds = [c for c, n in seeds.items() if n > 0]
    if available_seeds and random.random() < 0.3:
        farmer = ["PLANT", random.choice(available_seeds)]
    else:
        farmer = [random.choice(FARMER_OPS)]

    hands_actions = [[random.choice(FARMER_OPS)] for _ in farm.get("hands", [])]
    return {"farmer": farmer, "hands": hands_actions, "market": market}

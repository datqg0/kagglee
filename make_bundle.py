import json

def build():
    with open('kaggriculture_engine.py', 'r', encoding='utf-8') as f:
        engine_py = f.read()

    with open('runner_core.py', 'r', encoding='utf-8') as f:
        runner_py = f.read()

    with open('main.py', 'r', encoding='utf-8') as f:
        main_py = f.read()

    with open('abc.py', 'r', encoding='utf-8') as f:
        abc_py = f.read()

    with open('rl_agent.py', 'r', encoding='utf-8') as f:
        rl_py = f.read()

    with open('edf.py', 'r', encoding='utf-8') as f:
        edf_py = f.read()

    with open('miss.py', 'r', encoding='utf-8') as f:
        miss_py = f.read()

    starter_py = """def agent(obs):
    farms = obs.get("farms", [])
    player = obs.get("player", 0)
    private = obs.get("private", {}) or {}
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    farm = farms[player]
    fx, fy = farm["farmer"]
    tile = farm["tiles"][fy][fx]
    day = obs.get("day", 0)
    seeds = private.get("seeds", {})
    shed = private.get("shed", {})

    market = []
    if shed.get("CARROT", 0) > 0:
        market.append(["SELL", "CARROT", shed["CARROT"]])
    if seeds.get("CARROT", 0) == 0 and farm["money"] >= 20:
        market.append(["BUY_SEED", "CARROT", 1])

    farmer = ["PASS"]
    if tile is None and seeds.get("CARROT", 0) > 0:
        farmer = ["PLANT", "CARROT"]
    elif isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == "CARROT":
        age = day - tile["planted_day"]
        if age >= 3:
            farmer = ["HARVEST"]
        elif not tile.get("watered_today"):
            farmer = ["WATER"]
    return {"farmer": farmer, "hands": [], "market": market}
"""

    random_py = """import random

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
"""

    pass_py = """def agent(obs):
    return {"farmer": ["PASS"], "hands": [], "market": []}
"""

    presets = {
        'miss': miss_py,
        'edf': edf_py,
        'rl': rl_py,
        'main': main_py,
        'abc': abc_py,
        'starter': starter_py,
        'random': random_py,
        'pass': pass_py
    }

    with open('engine_bundle.js', 'w', encoding='utf-8') as f:
        f.write('window.KAGGRICULTURE_ENGINE_PY = ' + json.dumps(engine_py) + ';\n')
        f.write('window.KAGGRICULTURE_RUNNER_CORE_PY = ' + json.dumps(runner_py) + ';\n')
        f.write('window.AGENT_PRESETS = ' + json.dumps(presets) + ';\n')

    print("Generated engine_bundle.js successfully with presets:", list(presets.keys()))

if __name__ == '__main__':
    build()

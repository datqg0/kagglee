import json

with open("103201132.json", "r", encoding="utf-8") as f:
    data = json.load(f)

steps = data.get("steps", [])

for day in range(10):
    start_step = day * 24
    end_step = (day + 1) * 24
    p1_start = steps[start_step][1]["observation"]["farms"][1]
    
    buys = {}
    sales = {}
    plants = {}
    hires = 0
    
    for s in range(start_step, end_step):
        act = steps[s][1].get("action", {})
        for o in act.get("market", []):
            op = o[0]
            if op == "SELL":
                sales[o[1]] = sales.get(o[1], 0) + (o[2] if len(o) > 2 else 1)
            elif op.startswith("BUY"):
                it = o[1] if len(o) > 1 else op
                buys[it] = buys.get(it, 0) + (o[2] if len(o) > 2 else 1)
            elif op == "HIRE":
                hires += 1
        
        f_act = act.get("farmer", ["PASS"])
        if f_act[0] == "PLANT":
            plants[f_act[1]] = plants.get(f_act[1], 0) + 1
        for h in act.get("hands", []):
            if h[0] == "PLANT":
                plants[h[1]] = plants.get(h[1], 0) + 1
                
    print(f"DAY {day}: Money=${p1_start['money']:.1f}, Unlocked={p1_start['unlocked_quadrants']}, Hires={hires}")
    print(f"  Buys: {buys}")
    print(f"  Plants: {plants}")
    print(f"  Sales: {sales}")

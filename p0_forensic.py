import json

with open("103201132.json", "r", encoding="utf-8") as f:
    data = json.load(f)

steps = data.get("steps", [])

for day in range(30):
    start_step = day * 24
    end_step = (day + 1) * 24
    p0_start = steps[start_step][0]["observation"]["farms"][0]
    
    buys = {}
    sales = {}
    plants = {}
    hires = 0
    actions = {}
    
    for s in range(start_step, end_step):
        act = steps[s][0].get("action", {})
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
        f_op = f_act[0]
        actions[f_op] = actions.get(f_op, 0) + 1
        if f_op == "PLANT":
            plants[f_act[1]] = plants.get(f_act[1], 0) + 1
        for h in act.get("hands", []):
            h_op = h[0]
            actions[h_op] = actions.get(h_op, 0) + 1
            if h_op == "PLANT":
                plants[h[1]] = plants.get(h[1], 0) + 1
                
    # Count plants/animals at start of day
    tiles = p0_start.get("tiles", [])
    anims = {}
    plants_cnt = {}
    weeds = 0
    for r in tiles:
        for t in r:
            if t == "WEED":
                weeds += 1
            elif isinstance(t, dict):
                if t.get("kind") == "WEED":
                    weeds += 1
                elif t.get("kind") == "PLANT":
                    c = t.get("crop")
                    plants_cnt[c] = plants_cnt.get(c, 0) + 1
                elif t.get("kind") in ("COOP", "PASTURE"):
                    a = t.get("animal")
                    if a:
                        anims[a] = anims.get(a, 0) + 1
                        
    print(f"DAY {day:2d}: Money=${p0_start['money']:7.1f} | Unlocked={p0_start['unlocked_quadrants']} | Hires={hires:2d} | Animals={anims} | Plants={plants_cnt} | Weeds={weeds}")
    if buys:
        print(f"         Buys: {buys}")
    if sales:
        print(f"         Sales: {sales}")
    if plants:
        print(f"         Planted: {plants}")

import json

with open("replay.json", "r", encoding="utf-8") as f:
    data = json.load(f)

steps = data.get("steps", [])

# Let's inspect Day 14 and 15 (step 336..383)
for s in range(336, 384, 4):
    p0 = steps[s][0]
    obs = p0["observation"]
    f0 = obs["farms"][0]
    priv = obs["private"]
    act = p0["action"]
    
    seeds = priv.get("seeds", {})
    farmer_act = act.get("farmer")
    hands_act = act.get("hands", [])
    
    acts = [farmer_act] + hands_act
    act_types = {}
    for a in acts:
        if a:
            op = a[0]
            act_types[op] = act_types.get(op, 0) + 1
            
    # Count plants in farm tiles
    straw_count = 0
    empty_unlocked = 0
    for r in range(10):
        for c in range(10):
            t = f0["tiles"][r][c]
            if t is None:
                empty_unlocked += 1
            elif isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                straw_count += 1
                
    print(f"Step {s:3d} (D{obs['day']}, H{obs['hour']:02d}): Money=${f0['money']:.1f}, Straw_growing={straw_count}, Empty_tiles={empty_unlocked}, Seeds={seeds}, Actions={act_types}")

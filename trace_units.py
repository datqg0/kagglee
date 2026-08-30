import json

with open("replay.json", "r", encoding="utf-8") as f:
    data = json.load(f)

steps = data.get("steps", [])

# Let's inspect Day 8 (step 192..215)
for s in range(192, 216):
    p0 = steps[s][0]
    obs = p0["observation"]
    f0 = obs["farms"][0]
    priv = obs["private"]
    act = p0["action"]
    
    farmer_pos = f0["farmer"]
    hands_pos = f0["hands"]
    farmer_act = act.get("farmer")
    hands_act = act.get("hands", [])
    
    # Count action types this turn
    acts = [farmer_act] + hands_act
    act_types = {}
    for a in acts:
        if a:
            op = a[0]
            act_types[op] = act_types.get(op, 0) + 1
            
    print(f"Step {s:3d} (D8, H{obs['hour']:02d}): Farmer={farmer_pos}, Hands={len(hands_pos)}, Seeds={priv.get('seeds')}, Actions={act_types}")

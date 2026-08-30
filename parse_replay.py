import json

with open("103201132.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Keys:", list(data.keys()))
if "rewards" in data:
    print("Final Rewards:", data["rewards"])

steps = data.get("steps", [])
print(f"Total steps: {len(steps)}")

# Let's inspect step 0, step 100, step 300, step 500, step 719
checkpoints = [0, 24, 72, 144, 240, 360, 480, 600, 719]

for cp in checkpoints:
    if cp < len(steps):
        step_data = steps[cp]
        print(f"\n--- STEP {cp} (Day {cp//24}, Hour {cp%24}) ---")
        for p_idx in [0, 1]:
            p = step_data[p_idx]
            obs = p.get("observation", {})
            farms = obs.get("farms", [])
            if p_idx < len(farms):
                farm = farms[p_idx]
                money = farm.get("money")
                tiles = farm.get("tiles", [])
                
                # Count plants, animals, weeds
                plants = 0
                animals = 0
                weeds = 0
                empty = 0
                locked = 0
                crops_count = {}
                animals_count = {}
                for row in tiles:
                    for t in row:
                        if t == "LOCKED":
                            locked += 1
                        elif t is None:
                            empty += 1
                        elif isinstance(t, dict):
                            k = t.get("kind")
                            if k == "PLANT":
                                plants += 1
                                c = t.get("crop")
                                crops_count[c] = crops_count.get(c, 0) + 1
                            elif k == "WEED":
                                weeds += 1
                            elif k in ("COOP", "PASTURE"):
                                a = t.get("animal")
                                if a:
                                    animals += 1
                                    animals_count[a] = animals_count.get(a, 0) + 1
                hands_count = len(farm.get("hands", []))
                print(f"Player {p_idx}: Money=${money:.1f}, Hands={hands_count}, Animals={animals} {animals_count}, Plants={plants} {crops_count}, Weeds={weeds}")
            
            # Print actions submitted at this step
            act = p.get("action", {})
            if act:
                print(f"  Action P{p_idx}: Farmer={act.get('farmer')}, Market={act.get('market')}, Hands_count={len(act.get('hands', []))}")

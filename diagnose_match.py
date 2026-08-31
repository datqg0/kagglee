from kaggle_environments import make

env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42}, debug=True)
env.run(['apex_agent.py', 'submission_v3_standalone.py'])

for day in range(30):
    step = day * 24
    s = env.steps[step]
    f0 = s[0]['observation']['farms'][0]
    f1 = s[0]['observation']['farms'][1]
    p0_tiles = sum(1 for r in f0['tiles'] for t in r if isinstance(t, dict))
    p1_tiles = sum(1 for r in f1['tiles'] for t in r if isinstance(t, dict))
    print(f"Day {day:02d} | P0(Apex): ${f0['money']:7,.0f} (tiles={p0_tiles:2d}, land={len(f0['unlocked_quadrants'])}) | P1(V3): ${f1['money']:7,.0f} (tiles={p1_tiles:2d}, land={len(f1['unlocked_quadrants'])})")

final_s = env.steps[-1]
print("\nFinal Result:")
print("P0 (Apex):", final_s[0]['reward'])
print("P1 (V3):", final_s[1]['reward'])

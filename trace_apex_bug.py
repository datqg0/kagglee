from kaggle_environments import make

env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42}, debug=True)
env.run(['apex_agent.py', 'submission_v3_standalone.py'])

for step in range(10*24, 15*24):
    day = step // 24
    hour = step % 24
    s = env.steps[step]
    f0 = s[0]['observation']['farms'][0]
    p0_act = s[0]['action']
    if hour == 0 or hour == 23:
        weeds = sum(1 for r in f0['tiles'] for t in r if isinstance(t, dict) and t.get('kind') == 'WEED')
        plants = sum(1 for r in f0['tiles'] for t in r if isinstance(t, dict) and t.get('kind') == 'PLANT')
        animals = sum(1 for r in f0['tiles'] for t in r if isinstance(t, dict) and t.get('animal'))
        shed_wheat = s[0]['observation']['private']['shed'].get('WHEAT', 0)
        shed_load = sum(s[0]['observation']['private']['shed'].values())
        print(f"Step {step:03d} (D{day:02d}H{hour:02d}) | Money: ${f0['money']:6,.0f}, Plants: {plants:2d}, Animals: {animals:2d}, Weeds: {weeds:2d}, Shed Wheat: {shed_wheat:2d}, Shed Load: {shed_load:2d}")

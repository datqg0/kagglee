import official_kaggriculture
from kaggle_environments import make

def run_bench():
    print("=== BENCHMARKING edf.py (1000-Rule Expert System) ===")

    # 1. EDF vs MAIN
    env1 = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42}, debug=True)
    env1.run(['edf.py', 'main.py'])
    m0 = env1.steps[-1][0]['observation']['farms'][0]['money']
    m1 = env1.steps[-1][0]['observation']['farms'][1]['money']
    diff1 = m0 - m1
    win1 = "WIN" if diff1 > 0 else "LOSS"
    print(f"1. EDF vs MAIN:  EDF=${m0:,.0f} vs MAIN=${m1:,.0f} -> {win1} (Delta: {diff1:+,.0f})")

    # 2. EDF vs ABC
    env2 = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42}, debug=True)
    env2.run(['edf.py', 'abc.py'])
    m0 = env2.steps[-1][0]['observation']['farms'][0]['money']
    m1 = env2.steps[-1][0]['observation']['farms'][1]['money']
    diff2 = m0 - m1
    win2 = "WIN" if diff2 > 0 else "LOSS"
    print(f"2. EDF vs ABC:   EDF=${m0:,.0f} vs ABC=${m1:,.0f}  -> {win2} (Delta: {diff2:+,.0f})")

    # 3. EDF vs RL
    env3 = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42}, debug=True)
    env3.run(['edf.py', 'rl_agent.py'])
    m0 = env3.steps[-1][0]['observation']['farms'][0]['money']
    m1 = env3.steps[-1][0]['observation']['farms'][1]['money']
    diff3 = m0 - m1
    win3 = "WIN" if diff3 > 0 else "LOSS"
    print(f"3. EDF vs RL:    EDF=${m0:,.0f} vs RL=${m1:,.0f}   -> {win3} (Delta: {diff3:+,.0f})")

    # 4. EDF Solo on Seed 42
    env4 = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42}, debug=True)
    env4.run(['edf.py', 'pass'])
    m0 = env4.steps[-1][0]['observation']['farms'][0]['money']
    print(f"4. EDF Solo:     EDF=${m0:,.0f} (Seed 42)")

if __name__ == '__main__':
    run_bench()

import official_kaggriculture
from kaggle_environments import make

def run_bench():
    print("=================================================================")
    print("👑 TOURNAMENT BENCHMARK: miss.py (Neuro-Symbolic Hybrid Agent)")
    print("   Architecture: 1,000 Rules (Symbolic) + RL Policy (Neural)")
    print("=================================================================")

    # 1. MISS vs MAIN
    env1 = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42}, debug=True)
    env1.run(['miss.py', 'main.py'])
    m0 = env1.steps[-1][0]['observation']['farms'][0]['money']
    m1 = env1.steps[-1][0]['observation']['farms'][1]['money']
    diff1 = m0 - m1
    win1 = "WIN (+$" + f"{diff1:,.0f})" if diff1 > 0 else "LOSS (-$" + f"{-diff1:,.0f})"
    print(f"1. MISS vs MAIN: MISS=${m0:,.0f} vs MAIN=${m1:,.0f} -> {win1}")

    # 2. MISS vs ABC
    env2 = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42}, debug=True)
    env2.run(['miss.py', 'abc.py'])
    m0 = env2.steps[-1][0]['observation']['farms'][0]['money']
    m1 = env2.steps[-1][0]['observation']['farms'][1]['money']
    diff2 = m0 - m1
    win2 = "WIN (+$" + f"{diff2:,.0f})" if diff2 > 0 else "LOSS (-$" + f"{-diff2:,.0f})"
    print(f"2. MISS vs ABC:  MISS=${m0:,.0f} vs ABC=${m1:,.0f}  -> {win2}")

    # 3. MISS vs EDF
    env3 = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42}, debug=True)
    env3.run(['miss.py', 'edf.py'])
    m0 = env3.steps[-1][0]['observation']['farms'][0]['money']
    m1 = env3.steps[-1][0]['observation']['farms'][1]['money']
    diff3 = m0 - m1
    win3 = "WIN (+$" + f"{diff3:,.0f})" if diff3 > 0 else "LOSS (-$" + f"{-diff3:,.0f})"
    print(f"3. MISS vs EDF:  MISS=${m0:,.0f} vs EDF=${m1:,.0f}  -> {win3}")

    # 4. MISS vs RL
    env4 = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42}, debug=True)
    env4.run(['miss.py', 'rl_agent.py'])
    m0 = env4.steps[-1][0]['observation']['farms'][0]['money']
    m1 = env4.steps[-1][0]['observation']['farms'][1]['money']
    diff4 = m0 - m1
    win4 = "WIN (+$" + f"{diff4:,.0f})" if diff4 > 0 else "LOSS (-$" + f"{-diff4:,.0f})"
    print(f"4. MISS vs RL:   MISS=${m0:,.0f} vs RL=${m1:,.0f}   -> {win4}")

    # 5. MISS Solo on Seed 42
    env5 = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 42}, debug=True)
    env5.run(['miss.py', 'pass'])
    m0 = env5.steps[-1][0]['observation']['farms'][0]['money']
    print(f"5. MISS Solo:    MISS=${m0:,.0f} (Seed 42)")

if __name__ == '__main__':
    run_bench()

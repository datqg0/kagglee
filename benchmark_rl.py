"""
High-Speed Parallel Benchmark Suite for rl_agent.py
---------------------------------------------------
Runs 100 tournament matches across 10 CPU cores:
1. rl_agent.py vs abc.py (40 seeds: 500-539)
2. rl_agent.py vs main.py (40 seeds: 600-639)
3. rl_agent.py solo vs pass (20 seeds: 700-719)
"""

import time
import statistics
from concurrent.futures import ProcessPoolExecutor
import official_kaggriculture as engine
from match_runner import load_agent, Struct, MockEnv


def run_single_match(args):
    a0_name, a1_name, seed = args
    a0 = load_agent(a0_name)
    a1 = load_agent(a1_name)

    env = MockEnv({"seed": seed})
    env.info = {"seed": seed}
    state = [
        Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0)),
        Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0))
    ]
    engine._initialize(state, env)
    agents = [a0, a1]

    for step in range(720):
        day = step // 24
        hour = step % 24
        for i in range(2):
            state[i].observation.step = step
            state[i].observation.player = i
            obs_obj = state[i].observation
            obs = {
                "player": i, "step": step, "day": day, "hour": hour,
                "farms": obs_obj.farms, "market": obs_obj.market,
                "town": obs_obj.town, "private": obs_obj.private
            }
            state[i].action = agents[i](obs)
        engine.interpreter(state, env)

    m0 = state[0].observation.farms[0]["money"]
    m1 = state[1].observation.farms[1]["money"]
    return seed, a0_name, a1_name, m0, m1


def run_tournament():
    print("=" * 72)
    print("  KAGGRICULTURE PARALLEL TOURNAMENT (100 MATCHES)")
    print("=" * 72)

    t0 = time.time()
    workers = 10

    with ProcessPoolExecutor(max_workers=workers) as executor:
        # 1. RL vs ABC (40 matches)
        print("\n>>> TOURNAMENT 1: rl_agent.py vs abc.py (40 Matches, seeds 500-539)")
        tasks_abc = []
        for idx, seed in enumerate(range(500, 540)):
            if idx % 2 == 0:
                tasks_abc.append(("rl_agent.py", "abc.py", seed))
            else:
                tasks_abc.append(("abc.py", "rl_agent.py", seed))

        results_abc = list(executor.map(run_single_match, tasks_abc))

        rl_scores_abc = []
        abc_scores = []
        rl_wins_abc = 0
        abc_wins = 0
        ties_abc = 0

        for seed, a0_name, a1_name, m0, m1 in sorted(results_abc, key=lambda r: r[0]):
            if a0_name == "rl_agent.py":
                rl_m, abc_m = m0, m1
            else:
                abc_m, rl_m = m0, m1

            rl_scores_abc.append(rl_m)
            abc_scores.append(abc_m)
            outcome = "RL WIN" if rl_m > abc_m else "ABC WIN" if abc_m > rl_m else "TIE"
            if rl_m > abc_m: rl_wins_abc += 1
            elif abc_m > rl_m: abc_wins += 1
            else: ties_abc += 1

            print(f"  Seed {seed:4d}: RL=${rl_m:7,.0f} | ABC=${abc_m:7,.0f} | {outcome}")

        rl_avg_abc = statistics.mean(rl_scores_abc)
        abc_avg = statistics.mean(abc_scores)
        winrate_abc = (rl_wins_abc / len(results_abc)) * 100.0
        print(f"\n--- SUMMARY: RL vs ABC ---")
        print(f"  RL Avg:   ${rl_avg_abc:,.0f}")
        print(f"  ABC Avg:  ${abc_avg:,.0f} (Delta: +${rl_avg_abc - abc_avg:,.0f})")
        print(f"  Win Rate: {winrate_abc:.1f}% (RL={rl_wins_abc}, ABC={abc_wins}, TIE={ties_abc})")

        # 2. RL vs MAIN (40 matches)
        print("\n>>> TOURNAMENT 2: rl_agent.py vs main.py (40 Matches, seeds 600-639)")
        tasks_main = []
        for idx, seed in enumerate(range(600, 640)):
            if idx % 2 == 0:
                tasks_main.append(("rl_agent.py", "main.py", seed))
            else:
                tasks_main.append(("main.py", "rl_agent.py", seed))

        results_main = list(executor.map(run_single_match, tasks_main))

        rl_scores_main = []
        main_scores = []
        rl_wins_main = 0
        main_wins = 0
        ties_main = 0

        for seed, a0_name, a1_name, m0, m1 in sorted(results_main, key=lambda r: r[0]):
            if a0_name == "rl_agent.py":
                rl_m, main_m = m0, m1
            else:
                main_m, rl_m = m0, m1

            rl_scores_main.append(rl_m)
            main_scores.append(main_m)
            outcome = "RL WIN" if rl_m > main_m else "MAIN WIN" if main_m > rl_m else "TIE"
            if rl_m > main_m: rl_wins_main += 1
            elif main_m > rl_m: main_wins += 1
            else: ties_main += 1

            print(f"  Seed {seed:4d}: RL=${rl_m:7,.0f} | MAIN=${main_m:7,.0f} | {outcome}")

        rl_avg_main = statistics.mean(rl_scores_main)
        main_avg = statistics.mean(main_scores)
        winrate_main = (rl_wins_main / len(results_main)) * 100.0
        print(f"\n--- SUMMARY: RL vs MAIN ---")
        print(f"  RL Avg:   ${rl_avg_main:,.0f}")
        print(f"  MAIN Avg: ${main_avg:,.0f} (Delta: +${rl_avg_main - main_avg:,.0f})")
        print(f"  Win Rate: {winrate_main:.1f}% (RL={rl_wins_main}, MAIN={main_wins}, TIE={ties_main})")

        # 3. SOLO VS PASS (20 matches)
        print("\n>>> TOURNAMENT 3: Solo Maximum Wealth Benchmark (20 Matches vs pass)")
        tasks_solo = [("rl_agent.py", "agents/pass.py", seed) for seed in range(700, 720)]
        results_solo = list(executor.map(run_single_match, tasks_solo))

        solo_scores = []
        for seed, _, _, m0, _ in sorted(results_solo, key=lambda r: r[0]):
            solo_scores.append(m0)
            print(f"  Seed {seed:4d}: Solo RL=${m0:7,.0f}")

        solo_avg = statistics.mean(solo_scores)
        solo_min = min(solo_scores)
        solo_max = max(solo_scores)
        print(f"\n--- SUMMARY: SOLO PERFORMANCE ---")
        print(f"  Average Revenue: ${solo_avg:,.0f}")
        print(f"  Min Revenue:     ${solo_min:,.0f}")
        print(f"  Max Revenue:     ${solo_max:,.0f}")
        print(f"\nAll 100 matches completed in {time.time() - t0:.1f}s!")


if __name__ == "__main__":
    run_tournament()

"""
20-Match Simulation & Evaluation Suite for Kaggriculture
--------------------------------------------------------
Runs 20 full official matches across diverse opponents, seeds, and sides.
"""

import time
import copy
import statistics
import official_kaggriculture as engine
from match_runner import load_agent, Struct, MockEnv


def run_match(agent0_src: str, agent1_src: str, seed: int = 42):
    agent0_fn = load_agent(agent0_src)
    agent1_fn = load_agent(agent1_src)
    agents = [agent0_fn, agent1_fn]

    env = MockEnv()
    env.info = {"seed": seed}

    state = [
        Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0)),
        Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0))
    ]
    
    engine._initialize(state, env)

    t0 = time.time()

    for step in range(env.configuration["episodeSteps"]):
        for i in range(2):
            state[i].observation.step = step
            state[i].observation.player = i

        obs_dicts = []
        for i in range(2):
            obs_obj = state[i].observation
            obs_dict = {
                "player": i,
                "step": step,
                "day": step // 24,
                "hour": step % 24,
                "farms": copy.deepcopy(getattr(obs_obj, "farms", [])),
                "market": copy.deepcopy(getattr(obs_obj, "market", {})),
                "town": copy.deepcopy(getattr(obs_obj, "town", {})),
                "private": copy.deepcopy(getattr(obs_obj, "private", {}))
            }
            obs_dicts.append(obs_dict)

        for i in range(2):
            try:
                act = agents[i](obs_dicts[i])
                state[i].action = act
            except Exception as e:
                print(f"Error in agent {i} at step {step}: {e}")
                state[i].action = {"farmer": ["PASS"], "hands": [], "market": []}

        engine.interpreter(state, env)

    duration = time.time() - t0
    final_m0 = state[0].observation.farms[0]["money"]
    final_m1 = state[1].observation.farms[1]["money"]

    return {
        "m0": final_m0,
        "m1": final_m1,
        "duration": duration,
        "seed": seed
    }


def main():
    print("=" * 72)
    print("  KAGGRICULTURE 20-MATCH COMPREHENSIVE SIMULATION & BENCHMARK SUITE")
    print("=" * 72)

    # 20 Diverse Match Configurations
    schedule = [
        # vs RANDOM (10 games)
        ("main.py", "random", 1001, "P0 vs random"),
        ("random", "main.py", 1002, "P1 vs random"),
        ("main.py", "random", 1003, "P0 vs random"),
        ("random", "main.py", 1004, "P1 vs random"),
        ("main.py", "random", 1005, "P0 vs random"),
        ("random", "main.py", 1006, "P1 vs random"),
        ("main.py", "random", 1007, "P0 vs random"),
        ("random", "main.py", 1008, "P1 vs random"),
        ("main.py", "random", 1009, "P0 vs random"),
        ("random", "main.py", 1010, "P1 vs random"),

        # vs STARTER (6 games)
        ("main.py", "starter", 2001, "P0 vs starter"),
        ("starter", "main.py", 2002, "P1 vs starter"),
        ("main.py", "starter", 2003, "P0 vs starter"),
        ("starter", "main.py", 2004, "P1 vs starter"),
        ("main.py", "starter", 2005, "P0 vs starter"),
        ("starter", "main.py", 2006, "P1 vs starter"),

        # vs PASS (2 games)
        ("main.py", "pass", 3001, "P0 vs pass"),
        ("pass", "main.py", 3002, "P1 vs pass"),

        # SELF-PLAY (2 games)
        ("main.py", "main.py", 4001, "main vs main (Self-Play)"),
        ("main.py", "main.py", 4002, "main vs main (Self-Play)"),
    ]

    main_scores = []
    opp_scores = []
    wins = 0
    non_self_play_count = 0

    for idx, (a0, a1, seed, desc) in enumerate(schedule, 1):
        res = run_match(a0, a1, seed)
        is_self_play = (a0 == "main.py" and a1 == "main.py")

        if a0 == "main.py" and not is_self_play:
            main_m = res["m0"]
            opp_m = res["m1"]
            pos = "P0"
            opp_name = a1
        elif a1 == "main.py" and not is_self_play:
            main_m = res["m1"]
            opp_m = res["m0"]
            pos = "P1"
            opp_name = a0
        else:
            # Self play
            main_m = res["m0"]
            opp_m = res["m1"]
            pos = "P0+P1"
            opp_name = "main.py"

        if not is_self_play:
            non_self_play_count += 1
            win = main_m > opp_m
            if win:
                wins += 1
            outcome = "WIN  (+$" + f"{int(main_m - opp_m):,})" if win else "LOSS"
            main_scores.append(main_m)
            opp_scores.append(opp_m)
            print(f"[{idx:02d}/20] Seed {seed:4d} | {desc:24s} | main.py ({pos}): ${int(main_m):>7,} | {opp_name:>7s}: ${int(opp_m):>5,} | {outcome} ({res['duration']:.2f}s)")
        else:
            print(f"[{idx:02d}/20] Seed {seed:4d} | {desc:24s} | P0: ${int(main_m):>7,} | P1: ${int(opp_m):>7,} | COMBINED ${int(main_m+opp_m):,} ({res['duration']:.2f}s)")

    print("\n" + "=" * 72)
    print("                      20-MATCH BENCHMARK REPORT                      ")
    print("=" * 72)
    print(f"Competitive Matches  : {non_self_play_count} games")
    print(f"Win Rate             : {wins / non_self_play_count * 100:.1f}% ({wins}/{non_self_play_count})")
    print(f"Average Final Money  : ${int(statistics.mean(main_scores)):,}")
    print(f"Median Final Money   : ${int(statistics.median(main_scores)):,}")
    print(f"Peak Final Money     : ${int(max(main_scores)):,}")
    print(f"Lowest Final Money   : ${int(min(main_scores)):,}")
    print(f"Opponent Avg Money   : ${int(statistics.mean(opp_scores)):,}")
    print(f"Average Win Margin   : +${int(statistics.mean(main_scores) - statistics.mean(opp_scores)):,}")
    print("=" * 72)


if __name__ == "__main__":
    main()

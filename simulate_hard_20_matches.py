import time
import copy
from match_runner import load_agent, Struct, MockEnv
import official_kaggriculture as engine

def run_single_match(agent0_name, agent1_name, seed):
    agent0_fn = load_agent(agent0_name)
    agent1_fn = load_agent(agent1_name)
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
        day = step // 24
        hour = step % 24
        for i in range(2):
            state[i].observation.step = step
            state[i].observation.player = i

        obs_dicts = []
        for i in range(2):
            obs_obj = state[i].observation
            obs_dict = {
                "player": i,
                "step": step,
                "day": day,
                "hour": hour,
                "farms": copy.deepcopy(getattr(obs_obj, "farms", [])),
                "market": copy.deepcopy(getattr(obs_obj, "market", {})),
                "town": copy.deepcopy(getattr(obs_obj, "town", {})),
                "private": copy.deepcopy(getattr(obs_obj, "private", {}))
            }
            obs_dicts.append(obs_dict)

        for i in range(2):
            act = agents[i](obs_dicts[i])
            state[i].action = act

        engine.interpreter(state, env)

    dur = time.time() - t0
    m0 = state[0].observation.farms[0]["money"]
    m1 = state[1].observation.farms[1]["money"]
    return {"m0": m0, "m1": m1, "dur": dur}

def run_hard_20_benchmark():
    print("=" * 78)
    print("  KAGGRICULTURE 20-MATCH HARD OPPONENTS & SELF-PLAY BENCHMARK SUITE")
    print("=" * 78)

    matches = []
    # 10 matches vs challenger_expert.py (seeds 6001-6010, alternating P0/P1)
    for idx, s in enumerate(range(6001, 6011)):
        p0_main = (idx % 2 == 0)
        a0 = "main.py" if p0_main else "challenger_expert.py"
        a1 = "challenger_expert.py" if p0_main else "main.py"
        matches.append((f"Seed {s}", a0, a1, s, "vs Expert Challenger"))

    # 10 self-play mirror matches (seeds 5001-5010)
    for s in range(5001, 5011):
        matches.append((f"Seed {s}", "main.py", "main.py", s, "Self-Play Mirror"))

    competitive_scores = []
    opponent_scores = []
    wins = 0
    losses = 0
    ties = 0

    for i, (label, a0, a1, seed, match_type) in enumerate(matches, 1):
        is_self_play = (a0 == "main.py" and a1 == "main.py")
        res = run_single_match(a0, a1, seed)

        if not is_self_play:
            if a0 == "main.py":
                main_m, opp_m, pos, opp_name = res["m0"], res["m1"], "P0", a1
            else:
                main_m, opp_m, pos, opp_name = res["m1"], res["m0"], "P1", a0

            competitive_scores.append(main_m)
            opponent_scores.append(opp_m)
            if main_m > opp_m:
                wins += 1
                outcome = f"WIN  (+${main_m - opp_m:,.0f})"
            elif main_m < opp_m:
                losses += 1
                outcome = f"LOSS (-${opp_m - main_m:,.0f})"
            else:
                ties += 1
                outcome = "TIE"

            print(f"[{i:02d}/20] {label} | {pos} vs {opp_name:<20} | main.py: ${main_m:>7,.0f} | Opp: ${opp_m:>7,.0f} | {outcome} ({res['dur']:.2f}s)")
        else:
            p0_m, p1_m = res["m0"], res["m1"]
            print(f"[{i:02d}/20] {label} | main vs main (Self-Play)   | P0: ${p0_m:>7,.0f} | P1: ${p1_m:>7,.0f} | COMBINED ${p0_m + p1_m:>7,.0f} ({res['dur']:.2f}s)")

    print("\n" + "=" * 78)
    print("                 HARD OPPONENTS BENCHMARK REPORT                 ")
    print("=" * 78)
    if competitive_scores:
        n_comp = len(competitive_scores)
        sorted_scores = sorted(competitive_scores)
        avg_m = sum(competitive_scores) / n_comp
        med_m = sorted_scores[n_comp // 2]
        peak_m = max(competitive_scores)
        min_m = min(competitive_scores)
        opp_avg = sum(opponent_scores) / n_comp

        print(f"Vs Challenger Expert : {n_comp} games")
        print(f"Win Rate             : {wins / n_comp * 100:.1f}% ({wins}/{n_comp} wins, {losses} losses, {ties} ties)")
        print(f"Average Final Money  : ${avg_m:,.0f}")
        print(f"Median Final Money   : ${med_m:,.0f}")
        print(f"Peak Final Money     : ${peak_m:,.0f}")
        print(f"Lowest Final Money   : ${min_m:,.0f}")
        print(f"Opponent Avg Money   : ${opp_avg:,.0f}")
        print(f"Average Win Margin   : +${avg_m - opp_avg:,.0f}")
    print("=" * 78)

if __name__ == "__main__":
    run_hard_20_benchmark()

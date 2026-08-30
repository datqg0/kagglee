import time
import copy
from match_runner import Struct, MockEnv
import official_kaggriculture as engine
import grandmaster_opponents
import main

def get_agent_callable(name):
    if name == "main.py":
        return main.agent
    elif name == "gm_paarth_patel":
        return grandmaster_opponents.agent_gm_paarth_patel
    elif name == "gm_market_monopolizer":
        return grandmaster_opponents.agent_gm_market_monopolizer
    raise ValueError(f"Unknown agent: {name}")

def run_single_match(agent0_name, agent1_name, seed):
    a0 = get_agent_callable(agent0_name)
    a1 = get_agent_callable(agent1_name)
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
                "player": i, "step": step, "day": day, "hour": hour,
                "farms": copy.deepcopy(getattr(obs_obj, "farms", [])),
                "market": copy.deepcopy(getattr(obs_obj, "market", {})),
                "town": copy.deepcopy(getattr(obs_obj, "town", {})),
                "private": copy.deepcopy(getattr(obs_obj, "private", {}))
            }
            obs_dicts.append(obs_dict)

        state[0].action = a0(obs_dicts[0])
        state[1].action = a1(obs_dicts[1])
        engine.interpreter(state, env)

    dur = time.time() - t0
    m0 = state[0].observation.farms[0]["money"]
    m1 = state[1].observation.farms[1]["money"]
    return {"m0": m0, "m1": m1, "dur": dur}

def run_30_grandmaster_benchmark():
    print("=" * 84)
    print("    KAGGRICULTURE 30-MATCH OBJECTIVE GRANDMASTER BENCHMARK ($80k-$110k BOTS)")
    print("=" * 84)

    matches = []
    # 10 vs Paarth Patel Clone ($103k peak architecture)
    for idx, s in enumerate(range(21001, 21011)):
        p0_main = (idx % 2 == 0)
        a0 = "main.py" if p0_main else "gm_paarth_patel"
        a1 = "gm_paarth_patel" if p0_main else "main.py"
        matches.append((f"Seed {s}", a0, a1, s, "vs GM Paarth Patel ($103k Clone)"))

    # 10 vs GM Market Monopolizer ($90k+ Scalper)
    for idx, s in enumerate(range(22001, 22011)):
        p0_main = (idx % 2 == 0)
        a0 = "main.py" if p0_main else "gm_market_monopolizer"
        a1 = "gm_market_monopolizer" if p0_main else "main.py"
        matches.append((f"Seed {s}", a0, a1, s, "vs GM Market Monopolizer ($90k Scalper)"))

    # 10 Self-Play Mirror Matches
    for s in range(23001, 23011):
        matches.append((f"Seed {s}", "main.py", "main.py", s, "Self-Play Mirror (Elite)"))

    competitive_scores = []
    opponent_scores = []
    wins, losses, ties = 0, 0, 0

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

            print(f"[{i:02d}/30] {label} | {pos} vs {opp_name:<22} | main: ${main_m:>7,.0f} | Opp: ${opp_m:>7,.0f} | {outcome} ({res['dur']:.2f}s)")
        else:
            p0_m, p1_m = res["m0"], res["m1"]
            print(f"[{i:02d}/30] {label} | Self-Play Mirror (Elite)       | P0:   ${p0_m:>7,.0f} | P1:  ${p1_m:>7,.0f} | COMBINED ${p0_m + p1_m:>7,.0f} ({res['dur']:.2f}s)")

    print("\n" + "=" * 84)
    print("                 OBJECTIVE GRANDMASTER TOURNAMENT REPORT                 ")
    print("=" * 84)
    if competitive_scores:
        n_comp = len(competitive_scores)
        sorted_scores = sorted(competitive_scores)
        avg_m = sum(competitive_scores) / n_comp
        med_m = sorted_scores[n_comp // 2]
        peak_m = max(competitive_scores)
        min_m = min(competitive_scores)
        opp_avg = sum(opponent_scores) / n_comp

        print(f"Grandmaster Competitive Matches: {n_comp} games")
        print(f"Win Rate                       : {wins / n_comp * 100:.1f}% ({wins}/{n_comp} wins, {losses} losses, {ties} ties)")
        print(f"main.py Average Final Money    : ${avg_m:,.0f}")
        print(f"main.py Median Final Money     : ${med_m:,.0f}")
        print(f"main.py Peak Final Money       : ${peak_m:,.0f}")
        print(f"main.py Lowest Final Money     : ${min_m:,.0f}")
        print(f"Opponent Average Final Money   : ${opp_avg:,.0f}")
        print(f"Average Margin vs Grandmasters : +${avg_m - opp_avg:,.0f}")
    print("=" * 84)

if __name__ == "__main__":
    run_30_grandmaster_benchmark()

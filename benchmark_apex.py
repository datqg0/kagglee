"""Comprehensive Benchmark for Apex Agent."""
from kaggle_environments import make
import time

opponents = [
    ("submission_v3", "submission_v3_standalone.py"),
    ("dg", "dg.py"),
    ("miss", "miss.py"),
    ("rl_agent", "rl_agent.py"),
    ("edf", "edf.py"),
    ("starter", "starter")
]

seeds = [42, 100, 2026]

print("=" * 75)
print("RUNNING APEX AGENT BENCHMARK TOURNAMENT (Seeds: 42, 100, 2026)")
print("=" * 75)

total_apex_score = 0
total_opp_score = 0
apex_wins = 0
total_games = 0

for opp_name, opp_file in opponents:
    opp_wins = 0
    opp_apex_score = 0
    opp_their_score = 0
    print(f"\n--- APEX vs {opp_name.upper()} ---")
    for seed in seeds:
        # Match A: Apex as P0
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run(["apex_agent.py", opp_file])
        s0, s1 = env.steps[-1][0].reward, env.steps[-1][1].reward
        if s0 > s1: apex_wins += 1
        opp_apex_score += s0
        opp_their_score += s1
        total_games += 1
        print(f"  Seed {seed:4d} | P0(Apex): ${s0:7,.0f} vs P1({opp_name}): ${s1:7,.0f} -> {'WIN' if s0 > s1 else 'LOSS'}")

        # Match B: Apex as P1
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run([opp_file, "apex_agent.py"])
        s0, s1 = env.steps[-1][0].reward, env.steps[-1][1].reward
        if s1 > s0: apex_wins += 1
        opp_apex_score += s1
        opp_their_score += s0
        total_games += 1
        print(f"  Seed {seed:4d} | P0({opp_name}): ${s0:7,.0f} vs P1(Apex): ${s1:7,.0f} -> {'WIN' if s1 > s0 else 'LOSS'}")

    total_apex_score += opp_apex_score
    total_opp_score += opp_their_score
    avg_apex = opp_apex_score / (len(seeds) * 2)
    avg_opp = opp_their_score / (len(seeds) * 2)
    print(f"-> Summary vs {opp_name}: Apex Avg ${avg_apex:,.0f} vs Opp Avg ${avg_opp:,.0f}")

print("\n" + "=" * 75)
print(f"OVERALL TOURNAMENT RESULT:")
print(f"Games Played: {total_games}")
print(f"Apex Win Rate: {apex_wins}/{total_games} ({apex_wins/total_games*100:.1f}%)")
print(f"Apex Avg Score: ${total_apex_score/total_games:,.0f}")
print(f"Opponent Avg Score: ${total_opp_score/total_games:,.0f}")
print("=" * 75)

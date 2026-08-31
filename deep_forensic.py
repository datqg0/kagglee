"""Detailed forensic benchmark comparing old agents vs submission_v3."""
import json
from kaggle_environments import make

agents = {
    "rl_agent": "rl_agent.py",
    "rlagentv2": "rlagentv2.py",
    "miss": "miss.py",
    "dg": "dg.py"
}

v3 = "submission_v3_standalone.py"

print("=" * 60)
print("RUNNING FORENSIC HEAD-TO-HEAD BENCHMARK")
print("=" * 60)

for name, path in agents.items():
    print(f"\n>>> MATCHUP: {name} vs submission_v3")
    
    # Game 1: Old Agent = P0, v3 = P1
    env1 = make("kaggriculture", configuration={"episodeSteps": 720}, debug=False)
    env1.run([path, v3])
    p0_reward_1 = env1.steps[-1][0]["reward"]
    p1_reward_1 = env1.steps[-1][1]["reward"]
    print(f"  Game 1: P0 ({name}) = {p0_reward_1:,.0f}  vs  P1 (v3) = {p1_reward_1:,.0f} -> Winner: {'v3' if p1_reward_1 > p0_reward_1 else name}")
    
    # Game 2: v3 = P0, Old Agent = P1
    env2 = make("kaggriculture", configuration={"episodeSteps": 720}, debug=False)
    env2.run([v3, path])
    p0_reward_2 = env2.steps[-1][0]["reward"]
    p1_reward_2 = env2.steps[-1][1]["reward"]
    print(f"  Game 2: P0 (v3) = {p0_reward_2:,.0f}  vs  P1 ({name}) = {p1_reward_2:,.0f} -> Winner: {'v3' if p0_reward_2 > p1_reward_2 else name}")

print("\n" + "=" * 60)
print("BENCHMARK COMPLETED")
print("=" * 60)

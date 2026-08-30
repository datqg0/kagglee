import sys
import official_kaggriculture
from kaggle_environments import make

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_tournament():
    agents = ["rlagentv2.py", "miss.py", "edf.py", "rl_agent.py", "main.py", "abc.py"]
    seeds = [42, 100, 2026]

    print("==========================================================================")
    print("GRAND TOURNAMENT: ALL AGENTS ROUND-ROBIN BATTLE")
    print(f"   Contenders: {', '.join(agents)}")
    print(f"   Seeds: {seeds}")
    print("==========================================================================")

    scores = {a: {"wins": 0, "losses": 0, "ties": 0, "total_money": 0.0, "matches": 0} for a in agents}

    matchups = [
        ("rlagentv2.py", "miss.py"),
        ("rlagentv2.py", "edf.py"),
        ("rlagentv2.py", "rl_agent.py"),
        ("rlagentv2.py", "main.py"),
        ("rlagentv2.py", "abc.py"),
        ("miss.py", "edf.py"),
        ("miss.py", "main.py"),
        ("edf.py", "main.py"),
    ]

    for a0_file, a1_file in matchups:
        for s in seeds:
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=True)
            env.run([a0_file, a1_file])
            f0 = env.steps[-1][0]["observation"]["farms"][0]["money"]
            f1 = env.steps[-1][0]["observation"]["farms"][1]["money"]

            scores[a0_file]["total_money"] += f0
            scores[a0_file]["matches"] += 1
            scores[a1_file]["total_money"] += f1
            scores[a1_file]["matches"] += 1

            if f0 > f1:
                scores[a0_file]["wins"] += 1
                scores[a1_file]["losses"] += 1
                res_str = f"🏆 {a0_file} WINS (+${f0 - f1:,.0f})"
            elif f1 > f0:
                scores[a1_file]["wins"] += 1
                scores[a0_file]["losses"] += 1
                res_str = f"🏆 {a1_file} WINS (+${f1 - f0:,.0f})"
            else:
                scores[a0_file]["ties"] += 1
                scores[a1_file]["ties"] += 1
                res_str = "🤝 TIE"

            print(f"[Seed {s:4d}] {a0_file:14s} (${f0:,.0f}) vs {a1_file:14s} (${f1:,.0f}) -> {res_str}")

    print("\n==========================================================================")
    print("📊 FINAL LEADERBOARD RANKING:")
    print("==========================================================================")
    sorted_agents = sorted(
        agents,
        key=lambda a: (scores[a]["wins"], scores[a]["total_money"] / max(1, scores[a]["matches"])),
        reverse=True
    )

    print(f"{'Rank':<5} {'Agent':<16} {'Wins':<6} {'Losses':<8} {'Win Rate':<10} {'Avg Money':<12}")
    print("-" * 60)
    for r, a in enumerate(sorted_agents, 1):
        sc = scores[a]
        m = max(1, sc["matches"])
        wr = (sc["wins"] / m) * 100.0
        avg_m = sc["total_money"] / m
        print(f"{r:<5} {a:<16} {sc['wins']:<6} {sc['losses']:<8} {wr:5.1f}%     ${avg_m:,.0f}")

if __name__ == "__main__":
    run_tournament()

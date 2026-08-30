import sys
import official_kaggriculture
from kaggle_environments import make

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_showdown():
    opponents = ["rlagentv2.py", "miss.py", "edf.py", "rl_agent.py", "main.py", "abc.py"]
    seeds = [42, 100, 2026]

    print("==========================================================================")
    print("⚔️ SHOWDOWN: submission.py vs ALL AGENTS")
    print(f"   Seeds: {seeds}")
    print("==========================================================================")

    stats = {
        "submission_wins": 0,
        "submission_losses": 0,
        "submission_ties": 0,
        "opponents": {op: {"sub_wins": 0, "op_wins": 0, "sub_money": 0, "op_money": 0, "games": 0} for op in opponents}
    }

    for op in opponents:
        print(f"\n--- MATCHUP: submission.py vs {op} ---")
        for s in seeds:
            # Game A: submission as P0, opponent as P1
            env_a = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=True)
            env_a.run(["submission.py", op])
            m_sub_a = env_a.steps[-1][0]["observation"]["farms"][0]["money"]
            m_op_a  = env_a.steps[-1][0]["observation"]["farms"][1]["money"]

            # Game B: opponent as P0, submission as P1
            env_b = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s + 500}, debug=True)
            env_b.run([op, "submission.py"])
            m_op_b  = env_b.steps[-1][0]["observation"]["farms"][0]["money"]
            m_sub_b = env_b.steps[-1][0]["observation"]["farms"][1]["money"]

            # Record Game A
            stats["opponents"][op]["sub_money"] += m_sub_a
            stats["opponents"][op]["op_money"]  += m_op_a
            stats["opponents"][op]["games"] += 1
            if m_sub_a > m_op_a:
                stats["submission_wins"] += 1
                stats["opponents"][op]["sub_wins"] += 1
                res_a = f"🏆 submission.py WINS (+${m_sub_a - m_op_a:,.0f})"
            elif m_op_a > m_sub_a:
                stats["submission_losses"] += 1
                stats["opponents"][op]["op_wins"] += 1
                res_a = f"🏆 {op} WINS (+${m_op_a - m_sub_a:,.0f})"
            else:
                stats["submission_ties"] += 1
                res_a = "🤝 TIE"
            print(f"[Seed {s:4d} | P0] submission.py (${m_sub_a:,.0f}) vs {op} (${m_op_a:,.0f}) -> {res_a}")

            # Record Game B
            stats["opponents"][op]["sub_money"] += m_sub_b
            stats["opponents"][op]["op_money"]  += m_op_b
            stats["opponents"][op]["games"] += 1
            if m_sub_b > m_op_b:
                stats["submission_wins"] += 1
                stats["opponents"][op]["sub_wins"] += 1
                res_b = f"🏆 submission.py WINS (+${m_sub_b - m_op_b:,.0f})"
            elif m_op_b > m_sub_b:
                stats["submission_losses"] += 1
                stats["opponents"][op]["op_wins"] += 1
                res_b = f"🏆 {op} WINS (+${m_op_b - m_sub_b:,.0f})"
            else:
                stats["submission_ties"] += 1
                res_b = "🤝 TIE"
            print(f"[Seed {s+500:4d} | P1] {op} (${m_op_b:,.0f}) vs submission.py (${m_sub_b:,.0f}) -> {res_b}")

    print("\n==========================================================================")
    print("📊 OVERALL SHOWDOWN SUMMARY FOR submission.py:")
    print("==========================================================================")
    total_matches = stats["submission_wins"] + stats["submission_losses"] + stats["submission_ties"]
    win_pct = (stats["submission_wins"] / max(1, total_matches)) * 100.0
    print(f"Total Matches: {total_matches} | Wins: {stats['submission_wins']} | Losses: {stats['submission_losses']} | Ties: {stats['submission_ties']} (Win Rate: {win_pct:.1f}%)\n")

    print(f"{'Opponent':<16} {'Sub Wins':<10} {'Op Wins':<10} {'Sub Avg $':<14} {'Op Avg $':<14} {'Head-to-Head':<12}")
    print("-" * 75)
    for op in opponents:
        op_st = stats["opponents"][op]
        g = max(1, op_st["games"])
        sub_avg = op_st["sub_money"] / g
        op_avg  = op_st["op_money"] / g
        h2h = "WINNER" if op_st["sub_wins"] > op_st["op_wins"] else ("LOSER" if op_st["op_wins"] > op_st["sub_wins"] else "TIED")
        print(f"{op:<16} {op_st['sub_wins']:<10} {op_st['op_wins']:<10} ${sub_avg:,.0f}{'':<4} ${op_avg:,.0f}{'':<4} {h2h:<12}")

if __name__ == "__main__":
    run_showdown()

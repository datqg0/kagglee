import sys
import official_kaggriculture
from kaggle_environments import make

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_dg_tests():
    opponents = ["submission.py", "rlagentv2.py", "miss.py", "edf.py", "main.py", "abc.py"]
    seed = 42

    print("==========================================================================")
    print("🔥 EVALUATING dg.py (Deep Grandmaster - 2,500 Base Rules)")
    print(f"   Seed: {seed}")
    print("==========================================================================")

    for op in opponents:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=True)
        env.run(["dg.py", op])
        m_dg = env.steps[-1][0]["observation"]["farms"][0]["money"]
        m_op = env.steps[-1][0]["observation"]["farms"][1]["money"]
        diff = m_dg - m_op
        res = f"WIN (+${diff:,.0f})" if diff > 0 else f"LOSS (-${-diff:,.0f})"
        print(f"dg.py (${m_dg:,.0f}) vs {op:16s} (${m_op:,.0f}) -> {res}")

    # Solo test
    env_solo = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=True)
    env_solo.run(["dg.py", "pass"])
    solo_m = env_solo.steps[-1][0]["observation"]["farms"][0]["money"]
    print(f"\ndg.py Solo Revenue: ${solo_m:,.0f} (720 turns)")

if __name__ == "__main__":
    run_dg_tests()

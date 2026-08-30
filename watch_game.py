"""
Chạy script này để tạo file replay.html — mở bằng trình duyệt để xem animation.
Usage: python watch_game.py [seed]
"""
import sys
import json
import os

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42

from kaggle_environments import make

print(f"Simulating game with seed={seed}...")
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=True)
env.run(["abc.py", "main.py"])

final = env.steps[-1]
print(f"Game over!")
print(f"  abc.py  (P0): ${final[0].reward:.0f}")
print(f"  main.py (P1): ${final[1].reward:.0f}")
winner = "abc.py" if final[0].reward > final[1].reward else "main.py"
print(f"  Winner: {winner}")

# Lưu HTML visualizer
html_path = os.path.join(os.path.dirname(__file__), f"replay_seed{seed}.html")
html_content = env.render(mode="html", width=1200, height=800)
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\nMo file nay trong trinh duyet de xem animation:")
print(f"  {html_path}")

# Also save raw JSON replay for analysis
json_path = os.path.join(os.path.dirname(__file__), f"replay_seed{seed}.json")
with open(json_path, "w") as f:
    json.dump(env.toJSON(), f)
print(f"\nJSON replay da luu: {json_path}")

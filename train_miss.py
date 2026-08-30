"""
Multi-Core Parallel Training Pipeline for miss.py (Neuro-Symbolic Agent)
Uses Natural Evolution Strategies (NES) with Antithetic Sampling over 10 CPU cores.
"""

import os
import sys
import time
import base64
import struct
import random
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple
import numpy as np

import runner_core

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


TOTAL_PARAMS = 48 * 32 + 32 + 32 * 24 + 24  # 2360 params


def evaluate_candidate(weights: np.ndarray, seed_batch: List[int]) -> float:
    with open("miss.py", "r", encoding="utf-8") as f:
        miss_code = f.read()
    with open("main.py", "r", encoding="utf-8") as f:
        main_code = f.read()
    with open("abc.py", "r", encoding="utf-8") as f:
        abc_code = f.read()
    with open("edf.py", "r", encoding="utf-8") as f:
        edf_code = f.read()

    # Encode weights as base64 string
    b64_w = base64.b64encode(weights.astype(np.float32).tobytes()).decode("ascii")
    # Patch candidate weights into miss_code
    target_needle = 'b64_data = "'
    start_pos = miss_code.find(target_needle)
    if start_pos != -1:
        start_val = start_pos + len(target_needle)
        end_val = miss_code.find('"', start_val)
        candidate_code = miss_code[:start_val] + b64_w + miss_code[end_val:]
    else:
        candidate_code = miss_code

    total_score = 0.0

    for s in seed_batch:
        # Match 1: vs main.py (Weight: 2.0)
        res1 = runner_core.run_match_simulation(
            candidate_code, main_code, "MISS", "MAIN", seed=s, episode_steps=720
        )
        p0_m = res1["summary"]["agent0"]["final_money"]
        p1_m = res1["summary"]["agent1"]["final_money"]
        diff1 = p0_m - p1_m
        score1 = p0_m + (diff1 * 0.5)

        # Match 2: vs abc.py (Weight: 2.0)
        res2 = runner_core.run_match_simulation(
            candidate_code, abc_code, "MISS", "ABC", seed=s, episode_steps=720
        )
        p0_m2 = res2["summary"]["agent0"]["final_money"]
        p1_m2 = res2["summary"]["agent1"]["final_money"]
        diff2 = p0_m2 - p1_m2
        score2 = p0_m2 + (diff2 * 0.5)

        # Match 3: vs edf.py (Weight: 1.5)
        res3 = runner_core.run_match_simulation(
            candidate_code, edf_code, "MISS", "EDF", seed=s, episode_steps=720
        )
        p0_m3 = res3["summary"]["agent0"]["final_money"]
        p1_m3 = res3["summary"]["agent1"]["final_money"]
        diff3 = p0_m3 - p1_m3
        score3 = p0_m3 + (diff3 * 0.5)

        # Match 4: Solo revenue potential (Weight: 1.0)
        res4 = runner_core.run_match_simulation(
            candidate_code, "def agent(obs): return {'farmer': ['PASS'], 'hands': [], 'market': []}",
            "MISS", "PASS", seed=s, episode_steps=720
        )
        p0_m4 = res4["summary"]["agent0"]["final_money"]

        match_score = (score1 * 0.35) + (score2 * 0.35) + (score3 * 0.15) + (p0_m4 * 0.15)
        total_score += match_score

    return total_score / len(seed_batch)


def run_evolution():
    pop_size = 12  # 6 antithetic pairs
    sigma = 0.04
    alpha = 0.02
    generations = 8
    num_workers = 10

    # Load initial weights from miss.py
    with open("miss.py", "r", encoding="utf-8") as f:
        code = f.read()
    needle = 'b64_data = "'
    s_idx = code.find(needle) + len(needle)
    e_idx = code.find('"', s_idx)
    raw = base64.b64decode(code[s_idx:e_idx])
    mu = np.frombuffer(raw, dtype=np.float32).copy()

    print(f"================================================================")
    print(f"🚀 Training Neuro-Symbolic Agent miss.py via Parallel NES")
    print(f"   CPU Workers: {num_workers} | Population: {pop_size} | Sigma: {sigma} | LR: {alpha}")
    print(f"================================================================")

    init_score = evaluate_candidate(mu, [42, 100])
    print(f"Initial Baseline Score: {init_score:,.1f}")

    best_score = init_score
    best_mu = mu.copy()

    for gen in range(1, generations + 1):
        t0 = time.time()
        # Antithetic noise pairs
        half_pop = pop_size // 2
        eps = np.random.randn(half_pop, TOTAL_PARAMS).astype(np.float32)
        candidates = []
        for i in range(half_pop):
            candidates.append(mu + sigma * eps[i])
            candidates.append(mu - sigma * eps[i])

        gen_seeds = [1000 + gen * 10 + i for i in range(2)]

        tasks = [(candidates[i], gen_seeds) for i in range(pop_size)]
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(evaluate_candidate, t[0], t[1]) for t in tasks]
            scores = [f.result() for f in futures]

        scores = np.array(scores, dtype=np.float32)
        mean_s = np.mean(scores)
        std_s = np.std(scores) if np.std(scores) > 1e-6 else 1.0
        norm_scores = (scores - mean_s) / std_s

        # Gradient update
        grad = np.zeros(TOTAL_PARAMS, dtype=np.float32)
        for i in range(half_pop):
            pos_score = norm_scores[2 * i]
            neg_score = norm_scores[2 * i + 1]
            grad += (pos_score - neg_score) * eps[i]
        grad /= (2 * half_pop)

        mu += alpha * grad

        eval_score = evaluate_candidate(mu, [42, 100])
        dt = time.time() - t0
        print(f"Gen {gen:2d}/{generations:2d} | Avg Pop: {mean_s:,.0f} | Eval Score: {eval_score:,.0f} | Δ: {eval_score - init_score:+,.0f} | Time: {dt:.1f}s")

        if eval_score > best_score:
            best_score = eval_score
            best_mu = mu.copy()

    # Save best weights into miss.py
    b64_best = base64.b64encode(best_mu.astype(np.float32).tobytes()).decode("ascii")
    with open("miss.py", "r", encoding="utf-8") as f:
        code = f.read()
    s_idx = code.find(needle) + len(needle)
    e_idx = code.find('"', s_idx)
    new_code = code[:s_idx] + b64_best + code[e_idx:]
    with open("miss.py", "w", encoding="utf-8") as f:
        f.write(new_code)

    print(f"\n✅ Training Complete! Embedded best weights (Score: {best_score:,.0f}) into miss.py.")


if __name__ == "__main__":
    run_evolution()

"""
Advanced Multi-Opponent RL Trainer for rlagentv2.py
---------------------------------------------------
Trains deep policy network against:
- main.py
- abc.py
- edf.py (1,000-Rule Expert System)
- miss.py (Neuro-Symbolic Agent)
- solo revenue max
"""

import os
import sys
import time
import base64
import struct
import copy
import random
import numpy as np
from typing import List, Tuple, Dict, Any
from concurrent.futures import ProcessPoolExecutor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import official_kaggriculture as engine
from match_runner import load_agent, Struct, MockEnv
import rl_agent


def evaluate_v2_candidate(args: Tuple[np.ndarray, List[int]]) -> float:
    weights, train_seeds = args

    main_agent = load_agent("main.py")
    abc_agent  = load_agent("abc.py")
    edf_agent  = load_agent("edf.py")
    miss_agent = load_agent("miss.py")
    pass_agent = (lambda obs: {"farmer": ["PASS"], "hands": [], "market": []})

    policy = rl_agent.MacroRLPolicy(weights)

    def custom_agent(obs: Dict[str, Any]) -> Dict[str, Any]:
        state = rl_agent.GameState(obs)
        state_vec = state.extract_feature_vector()
        policy_out = policy.forward(state_vec)

        market_orders = rl_agent.plan_rl_market_orders(state, policy_out)
        tasks = rl_agent.generate_rl_tasks(state, policy_out)
        all_units = [state.farmer_pos] + state.hands_pos
        unit_actions = rl_agent.dispatch_rl_units(all_units, tasks, state)

        return {
            "farmer": unit_actions[0] if unit_actions else ["PASS"],
            "hands":  unit_actions[1:] if len(unit_actions) > 1 else [],
            "market": market_orders,
        }

    def sim(a0, a1, seed):
        env = MockEnv({"seed": seed})
        env.info = {"seed": seed}
        state = [
            Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0)),
            Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0))
        ]
        engine._initialize(state, env)
        agents = [a0, a1]

        for step in range(720):
            day = step // 24
            hour = step % 24
            for i in range(2):
                state[i].observation.step = step
                state[i].observation.player = i
                obs_obj = state[i].observation
                obs = {
                    "player": i, "step": step, "day": day, "hour": hour,
                    "farms": obs_obj.farms, "market": obs_obj.market,
                    "town": obs_obj.town, "private": obs_obj.private
                }
                state[i].action = agents[i](obs)
            engine.interpreter(state, env)

        return state[0].observation.farms[0]["money"], state[1].observation.farms[1]["money"]

    total_fitness = 0.0
    for seed in train_seeds:
        # 1. Solo Revenue
        m_solo, _ = sim(custom_agent, pass_agent, seed)

        # 2. vs main.py (P0 & P1)
        m_v_main0, main1 = sim(custom_agent, main_agent, seed)
        main0, m_v_main1 = sim(main_agent, custom_agent, seed + 100)

        # 3. vs abc.py (P0 & P1)
        m_v_abc0, abc1 = sim(custom_agent, abc_agent, seed)
        abc0, m_v_abc1 = sim(abc_agent, custom_agent, seed + 100)

        # 4. vs edf.py (P0 & P1)
        m_v_edf0, edf1 = sim(custom_agent, edf_agent, seed)
        edf0, m_v_edf1 = sim(edf_agent, custom_agent, seed + 100)

        # 5. vs miss.py (P0 & P1)
        m_v_miss0, miss1 = sim(custom_agent, miss_agent, seed)
        miss0, m_v_miss1 = sim(miss_agent, custom_agent, seed + 100)

        win_bonus = (
            (4000 if m_v_main0 > main1 else 0) + (4000 if m_v_main1 > main0 else 0) +
            (4000 if m_v_abc0 > abc1 else 0)   + (4000 if m_v_abc1 > abc0 else 0) +
            (4000 if m_v_edf0 > edf1 else 0)   + (4000 if m_v_edf1 > edf0 else 0) +
            (5000 if m_v_miss0 > miss1 else 0) + (5000 if m_v_miss1 > miss0 else 0)
        )

        avg_vs_main = (m_v_main0 + m_v_main1) / 2.0
        avg_vs_abc  = (m_v_abc0 + m_v_abc1) / 2.0
        avg_vs_edf  = (m_v_edf0 + m_v_edf1) / 2.0
        avg_vs_miss = (m_v_miss0 + m_v_miss1) / 2.0

        fitness = (
            0.15 * m_solo +
            0.20 * avg_vs_main +
            0.20 * avg_vs_abc +
            0.20 * avg_vs_edf +
            0.25 * avg_vs_miss +
            win_bonus
        )
        total_fitness += fitness

    return total_fitness / len(train_seeds)


def run_training():
    num_params = 48 * 32 + 32 + 32 * 24 + 24
    pop_size = 12       # 6 antithetic pairs
    sigma = 0.035       # Perturbation scale
    lr = 0.018          # Learning rate
    generations = 10
    num_workers = 8

    # Start from current rl_agent.py weights
    policy = rl_agent.get_policy()
    mu = np.array(policy.weights, dtype=np.float32).copy()

    print("=================================================================")
    print(f"🔥 Training RL Agent V2 (Multi-Opponent NES)")
    print(f"   Opponents: main, abc, edf, miss, pass")
    print(f"   Workers: {num_workers} | Pop Size: {pop_size} | Generations: {generations}")
    print("=================================================================")

    init_eval = evaluate_v2_candidate((mu, [42]))
    print(f"Initial Baseline Fitness: {init_eval:,.1f}\n")

    best_mu = mu.copy()
    best_fitness = init_eval

    for gen in range(1, generations + 1):
        t0 = time.time()
        half_pop = pop_size // 2
        eps = np.random.randn(half_pop, num_params).astype(np.float32)

        candidates = []
        for i in range(half_pop):
            candidates.append(mu + sigma * eps[i])
            candidates.append(mu - sigma * eps[i])

        gen_seeds = [100 * gen + 42]
        tasks = [(candidates[i], gen_seeds) for i in range(pop_size)]

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            scores = list(executor.map(evaluate_v2_candidate, tasks))

        scores = np.array(scores, dtype=np.float32)
        mean_s = np.mean(scores)
        std_s = np.std(scores) if np.std(scores) > 1e-6 else 1.0
        norm_scores = (scores - mean_s) / std_s

        # NES gradient step
        grad = np.zeros(num_params, dtype=np.float32)
        for i in range(half_pop):
            pos_score = norm_scores[2 * i]
            neg_score = norm_scores[2 * i + 1]
            grad += (pos_score - neg_score) * eps[i]
        grad /= (2 * half_pop)

        mu += lr * grad

        eval_score = evaluate_v2_candidate((mu, [42]))
        dt = time.time() - t0
        delta = eval_score - init_eval
        print(f"Gen {gen:2d}/{generations:2d} | Avg Pop: {mean_s:,.0f} | Eval: {eval_score:,.0f} | Δ: {delta:+,.0f} | {dt:.1f}s")

        if eval_score > best_fitness:
            best_fitness = eval_score
            best_mu = mu.copy()

    # Save to rlagentv2.py
    b64_w = base64.b64encode(best_mu.tobytes()).decode("ascii")
    with open("rl_agent.py", "r", encoding="utf-8") as f:
        src = f.read()

    needle = 'b64_data = "'
    s_idx = src.find(needle) + len(needle)
    e_idx = src.find('"', s_idx)
    new_src = src[:s_idx] + b64_w + src[e_idx:]
    new_src = new_src.replace(
        "Kaggriculture Agent: rl_agent.py",
        "Kaggriculture Agent: rlagentv2.py (Trained vs Main, ABC, EDF, MISS)"
    )

    with open("rlagentv2.py", "w", encoding="utf-8") as f:
        f.write(new_src)

    print("\n=================================================================")
    print(f"🎉 Training Finished! Saved optimized agent as rlagentv2.py")
    print(f"   Best Fitness: {best_fitness:,.1f} (Improvement: {best_fitness - init_eval:+,.1f})")
    print("=================================================================")


if __name__ == "__main__":
    run_training()

"""
High-Performance Parallel RL Training (NES) for Kaggriculture
--------------------------------------------------------------
Multi-core parallel Natural Evolution Strategies (NES) using ProcessPoolExecutor.
Trains across all CPU cores in ~1-2 minutes.
"""

import os
import sys
import time
import copy
import random
import numpy as np
from typing import List, Tuple, Dict, Any
from concurrent.futures import ProcessPoolExecutor

import official_kaggriculture as engine
from match_runner import load_agent, Struct, MockEnv
import rl_agent


def evaluate_single_candidate(args: Tuple[np.ndarray, List[int]]) -> float:
    """Evaluates a single weight vector across multiple seeds in a separate worker process."""
    weights, train_seeds = args

    # Local agent functions inside worker process
    main_agent = load_agent("main.py")
    abc_agent  = load_agent("abc.py")
    pass_agent = (lambda obs: {"farmer": ["PASS"], "hands": [], "market": []})

    policy = rl_agent.MacroRLPolicy(weights)

    def custom_rl_agent(obs: Dict[str, Any]) -> Dict[str, Any]:
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

    def sim_match(a0, a1, seed):
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
        # Solo
        rl_solo, _ = sim_match(custom_rl_agent, pass_agent, seed)
        # vs Main
        rl_main_0, main_1 = sim_match(custom_rl_agent, main_agent, seed)
        main_0, rl_main_1 = sim_match(main_agent, custom_rl_agent, seed + 50)
        # vs ABC
        rl_abc_0, abc_1 = sim_match(custom_rl_agent, abc_agent, seed)
        abc_0, rl_abc_1 = sim_match(abc_agent, custom_rl_agent, seed + 50)

        solo_term = rl_solo
        comp_main = (rl_main_0 + rl_main_1) / 2.0
        comp_abc = (rl_abc_0 + rl_abc_1) / 2.0

        win_bonus_main = (5000 if rl_main_0 > main_1 else 0) + (5000 if rl_main_1 > main_0 else 0)
        win_bonus_abc = (5000 if rl_abc_0 > abc_1 else 0) + (5000 if rl_abc_1 > abc_0 else 0)

        match_fitness = (
            0.30 * solo_term +
            0.35 * comp_main +
            0.35 * comp_abc +
            win_bonus_main + win_bonus_abc
        )
        total_fitness += match_fitness

    return total_fitness / len(train_seeds)


def train_parallel(
    generations: int = 10,
    pop_size: int = 10,
    sigma: float = 0.15,
    learning_rate: float = 0.06,
    workers: int = 10
):
    print("=" * 72, flush=True)
    print(f"  PARALLEL MULTI-CORE RL TRAINING ({workers} CPU Cores Active)", flush=True)
    print("=" * 72, flush=True)

    base_policy = rl_agent.MacroRLPolicy()
    num_params = base_policy.total_params
    print(f"Total Policy Parameters: {num_params}", flush=True)

    weights = np.zeros(num_params, dtype=np.float32)
    best_weights = weights.copy()
    best_fitness = -1e9

    t_start = time.time()

    with ProcessPoolExecutor(max_workers=workers) as executor:
        for gen in range(1, generations + 1):
            gen_t0 = time.time()
            current_seeds = [(100 * gen + s) for s in range(3)]

            half_pop = pop_size // 2
            epsilons = np.random.randn(half_pop, num_params).astype(np.float32)

            tasks = []
            candidates = []
            for i in range(half_pop):
                w_pos = weights + sigma * epsilons[i]
                w_neg = weights - sigma * epsilons[i]
                candidates.append(w_pos)
                candidates.append(w_neg)
                tasks.append((w_pos, current_seeds))
                tasks.append((w_neg, current_seeds))

            # Run all candidate evaluations in parallel across CPU cores
            results = list(executor.map(evaluate_single_candidate, tasks))

            for idx, fit in enumerate(results):
                if fit > best_fitness:
                    best_fitness = fit
                    best_weights = candidates[idx].copy()

            fitness_arr = np.array(results, dtype=np.float32)
            mean_fit = np.mean(fitness_arr)
            std_fit = np.std(fitness_arr) + 1e-6
            norm_fitness = (fitness_arr - mean_fit) / std_fit

            grad = np.zeros(num_params, dtype=np.float32)
            for i in range(half_pop):
                grad += (norm_fitness[2 * i] - norm_fitness[2 * i + 1]) * epsilons[i]
            grad = grad / (2 * half_pop * sigma)

            weights = (weights + learning_rate * grad) * 0.995

            gen_time = time.time() - gen_t0
            print(f"Gen {gen:2d}/{generations} | Mean Fit: {mean_fit:,.0f} | Best Fit: {best_fitness:,.0f} | Time: {gen_time:.1f}s", flush=True)

    total_time = time.time() - t_start
    print(f"\nTraining completed in {total_time:.1f}s ({total_time/60:.2f} mins).", flush=True)
    print(f"Achieved Top Fitness: {best_fitness:,.0f}", flush=True)

    np.save("weights.npy", best_weights)
    embed_weights_into_agent(best_weights)
    return best_weights


def embed_weights_into_agent(weights: np.ndarray):
    import base64
    raw_bytes = weights.astype(np.float32).tobytes()
    b64_str = base64.b64encode(raw_bytes).decode("ascii")

    agent_path = "rl_agent.py"
    with open(agent_path, "r", encoding="utf-8") as f:
        content = f.read()

    old_init = """        if weights is None:
            # High-performance baseline initialization
            self.weights = np.zeros(self.total_params, dtype=np.float32)"""

    new_init = f'''        if weights is None:
            # Embedded trained RL weights
            import base64
            b64_data = "{b64_str}"
            raw = base64.b64decode(b64_data)
            self.weights = np.frombuffer(raw, dtype=np.float32).copy()'''

    if old_init in content:
        content = content.replace(old_init, new_init)
        with open(agent_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Successfully embedded trained weights into rl_agent.py!", flush=True)
    else:
        # Fallback replacement if already modified
        import re
        content = re.sub(
            r'b64_data = "[A-Za-z0-9+/=]+"',
            f'b64_data = "{b64_str}"',
            content
        )
        with open(agent_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated existing embedded weights in rl_agent.py!", flush=True)


if __name__ == "__main__":
    train_parallel(generations=10, pop_size=10, sigma=0.15, learning_rate=0.06, workers=10)

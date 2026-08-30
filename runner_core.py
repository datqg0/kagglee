"""
Simulation Core Engine for Kaggriculture
Can be run in Python and Pyodide WebAssembly.
"""

import sys
import json
import time
import copy
import random
from typing import Callable, Any, Dict, List, Optional
import kaggriculture_engine as engine


class Struct(dict):
    def __init__(self, **entries):
        super().__init__(**entries)
        for k, v in entries.items():
            if isinstance(v, dict) and not isinstance(v, Struct):
                self[k] = Struct(**v)
            else:
                self[k] = v

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


class MockEnv:
    def __init__(self, configuration=None):
        default_cfg = {
            "episodeSteps": 720,
            "seed": None,
            "actTimeout": 1,
            "runTimeout": 1200,
            "boardSize": 10,
            "startingMoney": 3000,
            "maxMarketOrdersPerTurn": 10,
            "turnsPerDay": 24,
            "shedCapacity": 100,
            "weedSpawnChance": 0.005,
            "townShopUnlockInterval": 3,
            "townShopSellInterval": 4,
            "townCenterSellInterval": 24,
            "farmHandCostMult": 1,
            "marketParams": {}
        }
        if configuration:
            default_cfg.update(configuration)
        self.configuration = Struct(**default_cfg)
        self.info = {}
        self.done = False


def compile_agent(agent_src: str, agent_name: str = "custom") -> Callable:
    """Compiles agent code string into a callable function agent(obs)."""
    # Check built-in agent names
    if agent_src in engine.agents:
        return engine.agents[agent_src]
    
    # Otherwise compile Python code string
    local_ns = {}
    try:
        compiled = compile(agent_src, f"<{agent_name}>", "exec")
        exec(compiled, local_ns, local_ns)
    except Exception as e:
        raise RuntimeError(f"Syntax/Compilation error in agent '{agent_name}': {e}")
    
    if "agent" not in local_ns or not callable(local_ns["agent"]):
        raise AttributeError(f"Agent '{agent_name}' must define a function named 'agent(obs)'")
    
    return local_ns["agent"]


def run_match_simulation(
    agent0_code: str,
    agent1_code: str,
    agent0_name: str = "Player 1",
    agent1_name: str = "Player 2",
    seed: Optional[int] = None,
    episode_steps: int = 720,
    starting_money: int = 3000,
    board_size: int = 10,
    progress_fn: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Runs a complete Kaggriculture match and returns full replay structure & analytics.
    """
    agent0_fn = compile_agent(agent0_code, agent0_name)
    agent1_fn = compile_agent(agent1_code, agent1_name)
    agents = [agent0_fn, agent1_fn]
    agent_names = [agent0_name, agent1_name]

    if seed is None:
        seed = random.randint(1, 99999999)

    cfg = {
        "episodeSteps": episode_steps,
        "seed": seed,
        "boardSize": board_size,
        "startingMoney": starting_money,
        "turnsPerDay": 24,
        "shedCapacity": 100,
        "weedSpawnChance": 0.005,
        "townShopUnlockInterval": 3,
        "townShopSellInterval": 4,
        "townCenterSellInterval": 24,
        "maxMarketOrdersPerTurn": 10,
        "farmHandCostMult": 1,
        "marketParams": {}
    }

    env = MockEnv(cfg)
    
    # Initialize game state
    state = [
        Struct(action={}, reward=0, status="ACTIVE", info={}, observation=Struct(step=0)),
        Struct(action={}, reward=0, status="ACTIVE", info={}, observation=Struct(step=0))
    ]

    engine._initialize(state, env)

    steps_log = []
    daily_timeline = []
    agent_errors = [[], []]

    # Analytics trackers
    stats = {
        "p0": {"money_history": [], "hires": 0, "market_orders": 0, "harvests": 0, "quadrants": 1},
        "p1": {"money_history": [], "hires": 0, "market_orders": 0, "harvests": 0, "quadrants": 1}
    }

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
                "player": i,
                "step": step,
                "day": day,
                "hour": hour,
                "farms": copy.deepcopy(getattr(obs_obj, "farms", [])),
                "market": copy.deepcopy(getattr(obs_obj, "market", {})),
                "town": copy.deepcopy(getattr(obs_obj, "town", {})),
                "private": copy.deepcopy(getattr(obs_obj, "private", {}))
            }
            obs_dicts.append(obs_dict)

        # Call agents
        for i in range(2):
            try:
                act = agents[i](obs_dicts[i])
                if not isinstance(act, dict):
                    act = {"farmer": ["PASS"], "hands": [], "market": []}
                state[i].action = act
            except Exception as e:
                err_msg = f"Step {step} (Day {day} Turn {hour}): {str(e)}"
                if len(agent_errors[i]) < 10:
                    agent_errors[i].append(err_msg)
                state[i].action = {"farmer": ["PASS"], "hands": [], "market": []}

        # Step environment
        engine.interpreter(state, env)

        # Record analytics
        m0 = state[0].observation.farms[0]["money"]
        m1 = state[0].observation.farms[1]["money"]

        for i, (p_key, st) in enumerate([("p0", state[0]), ("p1", state[1])]):
            act = st.action
            if act:
                market_orders = act.get("market", [])
                stats[p_key]["market_orders"] += len(market_orders)
                for order in market_orders:
                    if order and order[0] == "HIRE":
                        stats[p_key]["hires"] += 1
                
                farmer_op = act.get("farmer", ["PASS"])[0] if act.get("farmer") else "PASS"
                if farmer_op == "HARVEST":
                    stats[p_key]["harvests"] += 1
                for hand_act in act.get("hands", []):
                    if hand_act and hand_act[0] == "HARVEST":
                        stats[p_key]["harvests"] += 1

            unlocked = len(st.observation.farms[i].get("unlocked_quadrants", ["NW"]))
            stats[p_key]["quadrants"] = max(stats[p_key]["quadrants"], unlocked)

        # Record step in replay structure (exact Kaggle schema)
        step_record = [
            {
                "action": copy.deepcopy(state[0].action),
                "reward": state[0].reward,
                "info": copy.deepcopy(getattr(state[0], "info", {})),
                "observation": obs_dicts[0],
                "status": state[0].status
            },
            {
                "action": copy.deepcopy(state[1].action),
                "reward": state[1].reward,
                "info": copy.deepcopy(getattr(state[1], "info", {})),
                "observation": obs_dicts[1],
                "status": state[1].status
            }
        ]
        steps_log.append(step_record)

        # Record daily checkpoint
        if hour == 0 or step == env.configuration["episodeSteps"] - 1:
            daily_timeline.append({
                "day": day,
                "p0_money": round(m0, 1),
                "p1_money": round(m1, 1)
            })

        if progress_fn and (step % 24 == 0 or step == env.configuration["episodeSteps"] - 1):
            progress_fn(step + 1, env.configuration["episodeSteps"], day + 1, round(m0, 1), round(m1, 1))

    duration = time.time() - t0

    final_m0 = state[0].observation.farms[0]["money"]
    final_m1 = state[0].observation.farms[1]["money"]

    winner = "P0" if final_m0 > final_m1 else ("P1" if final_m1 > final_m0 else "TIE")
    winner_name = agent_names[0] if winner == "P0" else (agent_names[1] if winner == "P1" else "Tie")

    summary = {
        "agent0": {"name": agent0_name, "final_money": round(final_m0, 1), "errors": agent_errors[0], "stats": stats["p0"]},
        "agent1": {"name": agent1_name, "final_money": round(final_m1, 1), "errors": agent_errors[1], "stats": stats["p1"]},
        "winner": winner,
        "winner_name": winner_name,
        "difference": abs(round(final_m0 - final_m1, 1)),
        "seed": seed,
        "total_steps": len(steps_log),
        "execution_time_sec": round(duration, 3),
        "timeline": daily_timeline
    }

    replay_payload = {
        "configuration": dict(env.configuration),
        "specification": {
            "action": {
                "description": "Per-turn action format",
                "type": "object",
                "default": {"farmer": ["PASS"], "hands": [], "market": []}
            },
            "agents": [2],
            "reward": {"type": ["number", "null"], "default": 0}
        },
        "steps": steps_log
    }

    return {
        "summary": summary,
        "replay": replay_payload
    }


if __name__ == "__main__":
    with open("agents/main.py", "r", encoding="utf-8") as f:
        p0_code = f.read()
    with open("agents/starter.py", "r", encoding="utf-8") as f:
        p1_code = f.read()

    def prog(step, total, day, m0, m1):
        print(f"Day {day:02d} ({step}/{total}) | P0: ${m0:,.0f} | P1: ${m1:,.0f}")

    res = run_match_simulation(p0_code, p1_code, "Grandmaster Agent", "Starter Baseline", seed=42, progress_fn=prog)
    print("\nSimulation Finished!")
    print("Winner:", res["summary"]["winner_name"], f"Diff: ${res['summary']['difference']:,.0f}")

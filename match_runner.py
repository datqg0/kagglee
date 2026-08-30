"""
Official Kaggle Kaggriculture Match Runner
------------------------------------------
Runs a 100% official Kaggle simulation match between two agents and saves the replay JSON.

Usage:
    python match_runner.py main.py starter
    python match_runner.py main.py agent2.py
"""

import sys
import json
import time
import importlib.util
import copy
from typing import Callable, Any, Dict

# Import the official Kaggle simulation module
import official_kaggriculture as engine


def load_agent(agent_src: str) -> Callable:
    """Loads an agent function from a .py file path or built-in name."""
    if agent_src == "starter":
        return engine.agents["starter"]
    elif agent_src == "random":
        return engine.agents["random"]
    elif agent_src == "pass":
        return engine.agents["pass"]
    elif agent_src.endswith(".py"):
        spec = importlib.util.spec_from_file_location("custom_agent", agent_src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "agent"):
            return mod.agent
        else:
            raise AttributeError(f"Module {agent_src} does not define an 'agent(obs)' function.")
    else:
        raise ValueError(f"Unknown agent source: {agent_src}")


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
            "boardSize": 10,
            "startingMoney": 3000,
            "maxMarketOrdersPerTurn": 10,
            "turnsPerDay": 24,
            "shedCapacity": 100,
            "weedSpawnChance": 0.005,
            "townShopUnlockInterval": 3,
            "townShopSellInterval": 4,
            "townCenterSellInterval": 24,
            "marketParams": None
        }
        if configuration:
            default_cfg.update(configuration)
        self.configuration = Struct(**default_cfg)
        self.done = False


def run_match(agent0_src: str, agent1_src: str, output_replay: str = "replay.json"):
    print(f"============================================================")
    print(f" Official Kaggriculture Match: {agent0_src} vs {agent1_src}")
    print(f"============================================================")

    agent0_fn = load_agent(agent0_src)
    agent1_fn = load_agent(agent1_src)
    agents = [agent0_fn, agent1_fn]

    env = MockEnv()
    
    # Initialize game state
    state = [
        Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0)),
        Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0))
    ]
    
    engine._initialize(state, env)
    
    steps_log = []

    t0 = time.time()

    for step in range(env.configuration["episodeSteps"]):
        # Set step and player on observation objects for the engine and agents
        for i in range(2):
            state[i].observation.step = step
            state[i].observation.player = i

        # Convert state observations to standard dictionary
        obs_dicts = []
        for i in range(2):
            obs_obj = state[i].observation
            obs_dict = {
                "player": i,
                "step": step,
                "day": step // 24,
                "hour": step % 24,
                "farms": copy.deepcopy(getattr(obs_obj, "farms", [])),
                "market": copy.deepcopy(getattr(obs_obj, "market", {})),
                "town": copy.deepcopy(getattr(obs_obj, "town", {})),
                "private": copy.deepcopy(getattr(obs_obj, "private", {}))
            }
            obs_dicts.append(obs_dict)

        # Call agents for action
        for i in range(2):
            try:
                act = agents[i](obs_dicts[i])
                state[i].action = act
            except Exception as e:
                print(f"Error executing agent {i} at step {step}: {e}")
                state[i].action = {"farmer": ["PASS"], "hands": [], "market": []}

        # Step official environment
        engine.interpreter(state, env)

        # Record step in replay
        step_record = [
            {"action": copy.deepcopy(state[0].action), "reward": state[0].reward, "observation": obs_dicts[0], "status": state[0].status},
            {"action": copy.deepcopy(state[1].action), "reward": state[1].reward, "observation": obs_dicts[1], "status": state[1].status}
        ]
        steps_log.append(step_record)

        # Print progress every 5 days
        if step % (24 * 5) == 0 and step > 0:
            day = step // 24
            m0 = state[0].observation.farms[0]["money"]
            m1 = state[0].observation.farms[1]["money"]
            print(f"Day {day:02d} | Player 0 ({agent0_src}): ${int(m0):,} | Player 1 ({agent1_src}): ${int(m1):,}")

    duration = time.time() - t0

    # Final step record
    final_m0 = state[0].observation.farms[0]["money"]
    final_m1 = state[0].observation.farms[1]["money"]

    print("\n============================================================")
    print(" MATCH COMPLETED (720 turns)")
    print("============================================================")
    print(f"Player 0 ({agent0_src}) Final Coins : ${int(final_m0):,}")
    print(f"Player 1 ({agent1_src}) Final Coins : ${int(final_m1):,}")
    print(f"Execution Time : {duration:.2f}s")

    if final_m0 > final_m1:
        print(f"Winner: Player 0 ({agent0_src}) (+${int(final_m0 - final_m1):,})")
    elif final_m1 > final_m0:
        print(f"Winner: Player 1 ({agent1_src}) (+${int(final_m1 - final_m0):,})")
    else:
        print("Result: TIE")

    # Save replay JSON
    replay_data = {
        "configuration": env.configuration,
        "steps": steps_log
    }
    with open(output_replay, "w", encoding="utf-8") as f:
        json.dump(replay_data, f)
    print(f"Replay saved to: {output_replay}")


if __name__ == "__main__":
    a0 = sys.argv[1] if len(sys.argv) > 1 else "main.py"
    a1 = sys.argv[2] if len(sys.argv) > 2 else "starter"
    out = sys.argv[3] if len(sys.argv) > 3 else "replay.json"
    run_match(a0, a1, out)

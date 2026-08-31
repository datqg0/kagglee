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


import io
import os
import ast
import base64
import tarfile
import zipfile
import tempfile


def _extract_and_find_entry(raw_bytes: bytes, agent_name: str) -> Callable:
    """Extracts a tar.gz / tar / zip archive into a sandbox directory and locates the agent function."""
    extract_dir = tempfile.mkdtemp(prefix=f"agent_{agent_name}_")
    bio = io.BytesIO(raw_bytes)
    
    # Try tarfile extraction
    is_tar = False
    try:
        if tarfile.is_tarfile(bio):
            bio.seek(0)
            with tarfile.open(fileobj=bio) as tar:
                tar.extractall(extract_dir)
            is_tar = True
    except Exception:
        is_tar = False
        
    # Try zipfile if not tar
    if not is_tar:
        try:
            bio.seek(0)
            if zipfile.is_zipfile(bio):
                bio.seek(0)
                with zipfile.ZipFile(bio) as zf:
                    zf.extractall(extract_dir)
            else:
                bio.seek(0)
                with tarfile.open(fileobj=bio, mode="r:*") as tar:
                    tar.extractall(extract_dir)
        except Exception as e:
            raise RuntimeError(f"Failed to extract archive package for '{agent_name}': {e}")
            
    # Add all directories containing python files to sys.path
    py_files = []
    for root, dirs, files in os.walk(extract_dir):
        has_py = any(f.endswith(".py") for f in files)
        if has_py and root not in sys.path:
            sys.path.insert(0, root)
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
                
    if not py_files:
        raise FileNotFoundError(f"Archive '{agent_name}' contains no .py Python files!")
        
    # Search for best entry file and function
    best_file = None
    best_func_name = "agent"
    
    # Strategy 1: Prioritize files named 'main.py', 'agent.py', or '__main__.py'
    ranked_files = sorted(
        py_files,
        key=lambda p: 0 if os.path.basename(p) == "main.py"
        else 1 if os.path.basename(p) == "agent.py"
        else 2 if os.path.basename(p) == "__main__.py"
        else 3
    )
    
    for filepath in ranked_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            tree = ast.parse(content)
            func_defs = [
                node.name for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            if "agent" in func_defs:
                best_file = filepath
                best_func_name = "agent"
                break
            elif "main" in func_defs:
                best_file = filepath
                best_func_name = "main"
                break
        except Exception:
            continue
            
    # Strategy 2: If not found in primary named files, check any other .py file
    if not best_file:
        for filepath in py_files:
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                tree = ast.parse(content)
                func_defs = [
                    node.name for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                if "agent" in func_defs:
                    best_file = filepath
                    best_func_name = "agent"
                    break
                elif "main" in func_defs:
                    best_file = filepath
                    best_func_name = "main"
                    break
            except Exception:
                continue

    # Fallback to first ranked file
    if not best_file:
        best_file = ranked_files[0]
        best_func_name = "agent"
        
    # Execute the entry file in its directory context
    entry_dir = os.path.dirname(best_file)
    if entry_dir not in sys.path:
        sys.path.insert(0, entry_dir)
        
    local_ns = {
        "__file__": best_file,
        "__name__": "__main__"
    }
    
    with open(best_file, "r", encoding="utf-8", errors="ignore") as f:
        code_str = f.read()
        
    try:
        compiled = compile(code_str, best_file, "exec")
        exec(compiled, local_ns, local_ns)
    except Exception as e:
        raise RuntimeError(f"Error executing entry file '{os.path.basename(best_file)}' in '{agent_name}': {e}")
        
    # Locate callable in namespace
    callable_candidate = None
    if best_func_name in local_ns and callable(local_ns[best_func_name]):
        callable_candidate = local_ns[best_func_name]
    elif "agent" in local_ns and callable(local_ns["agent"]):
        callable_candidate = local_ns["agent"]
    elif "main" in local_ns and callable(local_ns["main"]):
        callable_candidate = local_ns["main"]
    else:
        for k, v in local_ns.items():
            if callable(v) and not k.startswith("_") and k not in ("Struct", "MockEnv"):
                callable_candidate = v
                break
                
    if not callable_candidate:
        raise AttributeError(f"Archive entry file '{os.path.basename(best_file)}' must define an 'agent(obs)' or 'main(obs)' function.")
        
    return callable_candidate


def compile_agent(agent_src: str, agent_name: str = "custom") -> Callable:
    """Compiles agent code string or extracts archive package into a callable function agent(obs)."""
    # Check built-in agent names
    if agent_src in engine.agents:
        return engine.agents[agent_src]
    
    # Check if agent_src is an encoded archive package
    if isinstance(agent_src, str) and (agent_src.startswith("__ARCHIVE_BASE64__:") or agent_src.startswith("data:application/")):
        parts = agent_src.split(":", 2)
        if len(parts) == 3:
            raw_b64 = parts[2]
        else:
            raw_b64 = agent_src.split(",")[-1]
        raw_bytes = base64.b64decode(raw_b64)
        return _extract_and_find_entry(raw_bytes, agent_name)
    
    # Otherwise compile standard Python code string
    local_ns = {}
    try:
        compiled = compile(agent_src, f"<{agent_name}>", "exec")
        exec(compiled, local_ns, local_ns)
    except Exception as e:
        raise RuntimeError(f"Syntax/Compilation error in agent '{agent_name}': {e}")
    
    if "agent" in local_ns and callable(local_ns["agent"]):
        return local_ns["agent"]
    if "main" in local_ns and callable(local_ns["main"]):
        return local_ns["main"]
        
    raise AttributeError(f"Agent '{agent_name}' must define a function named 'agent(obs)' or 'main(obs)'")


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
    env.info["seed"] = seed
    
    # Initialize game state
    state = [
        Struct(action={}, reward=0, status="ACTIVE", info={}, observation=Struct(step=0)),
        Struct(action={}, reward=0, status="ACTIVE", info={}, observation=Struct(step=0))
    ]

    engine._initialize(state, env)

    steps_log = []
    daily_timeline = []
    agent_errors = [[], []]

    # Quant & Analytics trackers
    def create_stats_tracker():
        return {
            "money_history": [],
            "peak_money": 3000,
            "gross_revenue": 0,
            "total_spend": 0,
            "spend_seeds": 0,
            "spend_animals": 0,
            "spend_hires": 0,
            "spend_land": 0,
            "spend_products": 0,
            "net_profit": 0,
            "roi_pct": 0.0,
            "revenue_per_worker_turn": 0.0,
            "revenue_by_product": {p: 0 for p in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]},
            "units_sold": {p: 0 for p in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]},
            "plants": 0, "waters": 0, "harvests": 0, "fertilizes": 0, "digs": 0,
            "coops": 0, "pastures": 0, "seeds_bought": 0, "animals_bought": 0, "feeds": 0, "cares": 0, "fertilizer_collected": 0,
            "market_orders": 0, "hires": 0, "quadrants": 1,
            "movement_turns": 0, "farming_turns": 0, "ranching_turns": 0, "logistics_turns": 0, "idle_turns": 0,
            "total_worker_turns": 0, "worker_efficiency": 0.0,
            "archetype": "Generalist Farmer", "quant_grade": "A"
        }

    stats = {"p0": create_stats_tracker(), "p1": create_stats_tracker()}

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

        # Money and prices before turn execution
        pre_money = [state[0].observation.farms[0]["money"], state[1].observation.farms[1]["money"]]
        pre_market_prices = copy.deepcopy(getattr(state[0].observation.market, "prices", {}))

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

        # Money after turn execution
        post_money = [state[0].observation.farms[0]["money"], state[1].observation.farms[1]["money"]]

        # Track financials and actions
        movement_ops = {"NORTH", "SOUTH", "EAST", "WEST"}
        farming_ops = {"PLANT", "WATER", "HARVEST", "FERTILIZE", "DIG"}
        ranching_ops = {"FEED", "CARE", "COLLECT_FERTILIZER", "BUILD_COOP", "BUILD_PASTURE"}
        logistics_ops = {"PLACE", "PICKUP", "DROP"}

        for i, (p_key, st) in enumerate([("p0", state[0]), ("p1", state[1])]):
            stats[p_key]["peak_money"] = max(stats[p_key]["peak_money"], round(post_money[i], 1))
            act = st.action
            if act:
                market_orders = act.get("market", [])
                stats[p_key]["market_orders"] += len(market_orders)
                for order in market_orders:
                    if not order or not isinstance(order, list): continue
                    m_op = order[0]
                    n_units = order[2] if len(order) > 2 and isinstance(order[2], int) else 1
                    item_name = order[1] if len(order) > 1 and isinstance(order[1], str) else ""

                    if m_op == "HIRE":
                        stats[p_key]["hires"] += 1
                        # Estimate Fibonacci hire cost
                        hire_count_today = state[i].observation.farms[i].get("hires_today", 1)
                        stats[p_key]["spend_hires"] += engine._hire_cost(max(0, hire_count_today - 1))
                    elif m_op == "BUY_LAND":
                        unlocked_count = len(state[i].observation.farms[i].get("unlocked_quadrants", ["NW"]))
                        cost = engine.LAND_PRICES[min(2, max(0, unlocked_count - 1))]
                        stats[p_key]["spend_land"] += cost
                    elif m_op == "BUY_SEED":
                        stats[p_key]["seeds_bought"] += n_units
                        seed_cost = engine.CROPS.get(item_name, {}).get("seed", 20) * n_units
                        stats[p_key]["spend_seeds"] += seed_cost
                    elif m_op == "BUY_ANIMAL":
                        stats[p_key]["animals_bought"] += n_units
                        animal_cost = engine.ANIMALS.get(item_name, {}).get("cost", 400) * n_units
                        stats[p_key]["spend_animals"] += animal_cost
                    elif m_op == "BUY_PRODUCT":
                        prod_price = pre_market_prices.get(item_name, 25) * n_units
                        stats[p_key]["spend_products"] += prod_price
                    elif m_op == "SELL":
                        stats[p_key]["units_sold"][item_name] = stats[p_key]["units_sold"].get(item_name, 0) + n_units
                        # Realized revenue
                        approx_price = pre_market_prices.get(item_name, 1)
                        rev = approx_price * n_units
                        stats[p_key]["revenue_by_product"][item_name] = stats[p_key]["revenue_by_product"].get(item_name, 0) + rev
                        stats[p_key]["gross_revenue"] += rev

                # Unit actions telemetry
                unit_acts = []
                if act.get("farmer"): unit_acts.append(act["farmer"])
                for hand_act in act.get("hands", []):
                    if hand_act: unit_acts.append(hand_act)

                for u_act in unit_acts:
                    if not u_act or not isinstance(u_act, list): continue
                    u_op = u_act[0]
                    stats[p_key]["total_worker_turns"] += 1

                    if u_op in movement_ops: stats[p_key]["movement_turns"] += 1
                    elif u_op in farming_ops: stats[p_key]["farming_turns"] += 1
                    elif u_op in ranching_ops: stats[p_key]["ranching_turns"] += 1
                    elif u_op in logistics_ops: stats[p_key]["logistics_turns"] += 1
                    elif u_op == "PASS": stats[p_key]["idle_turns"] += 1

                    if u_op == "HARVEST": stats[p_key]["harvests"] += 1
                    elif u_op == "PLANT": stats[p_key]["plants"] += 1
                    elif u_op == "WATER": stats[p_key]["waters"] += 1
                    elif u_op == "FERTILIZE": stats[p_key]["fertilizes"] += 1
                    elif u_op == "FEED": stats[p_key]["feeds"] += 1
                    elif u_op == "CARE": stats[p_key]["cares"] += 1
                    elif u_op == "DIG": stats[p_key]["digs"] += 1
                    elif u_op == "COLLECT_FERTILIZER": stats[p_key]["fertilizer_collected"] += 1
                    elif u_op == "BUILD_COOP": stats[p_key]["coops"] += 1
                    elif u_op == "BUILD_PASTURE": stats[p_key]["pastures"] += 1

            unlocked = len(state[i].observation.farms[i].get("unlocked_quadrants", ["NW"]))
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
        m0 = post_money[0]
        m1 = post_money[1]
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

    # Finalize microeconomic KPIs
    for i, p_key in enumerate(["p0", "p1"]):
        st_p = stats[p_key]
        final_bal = [final_m0, final_m1][i]
        st_p["total_spend"] = st_p["spend_seeds"] + st_p["spend_animals"] + st_p["spend_hires"] + st_p["spend_land"] + st_p["spend_products"]
        st_p["net_profit"] = round(final_bal - starting_money, 1)
        st_p["roi_pct"] = round((st_p["net_profit"] / st_p["total_spend"] * 100), 1) if st_p["total_spend"] > 0 else 0.0
        tot_turns = st_p["total_worker_turns"]
        st_p["revenue_per_worker_turn"] = round(st_p["gross_revenue"] / tot_turns, 2) if tot_turns > 0 else 0.0
        
        prod_turns = st_p["farming_turns"] + st_p["ranching_turns"] + st_p["logistics_turns"]
        st_p["worker_efficiency"] = round((prod_turns / tot_turns * 100), 1) if tot_turns > 0 else 0.0

        # Archetype classification
        rev_by_prod = st_p["revenue_by_product"]
        gross = max(1, st_p["gross_revenue"])
        livestock_rev = rev_by_prod.get("MILK", 0) + rev_by_prod.get("WOOL", 0) + rev_by_prod.get("EGG", 0)
        crop_rev = rev_by_prod.get("STRAWBERRY", 0) + rev_by_prod.get("MELON", 0) + rev_by_prod.get("TOMATO", 0) + rev_by_prod.get("CARROT", 0) + rev_by_prod.get("WHEAT", 0)
        
        if livestock_rev >= 0.55 * gross:
            st_p["archetype"] = "🐮 Livestock & Dairy Industrialist"
        elif (rev_by_prod.get("STRAWBERRY", 0) + rev_by_prod.get("MELON", 0)) >= 0.45 * gross:
            st_p["archetype"] = "🍓 High-Yield Cash Crop Master"
        elif (rev_by_prod.get("WHEAT", 0) + rev_by_prod.get("CARROT", 0)) >= 0.5 * gross:
            st_p["archetype"] = "🌾 High-Speed Staple Scaler"
        elif gross > 10000:
            st_p["archetype"] = "🚜 Diversified Agribusiness"
        else:
            st_p["archetype"] = "🌱 Subsistence Farming"

        # Quant Performance Grade
        if final_bal >= 85000 and st_p["roi_pct"] >= 180:
            st_p["quant_grade"] = "S+ (Apex Grandmaster)"
        elif final_bal >= 70000 and st_p["roi_pct"] >= 140:
            st_p["quant_grade"] = "S (Elite Quant)"
        elif final_bal >= 50000:
            st_p["quant_grade"] = "A+ (Master)"
        elif final_bal >= 30000:
            st_p["quant_grade"] = "A (Advanced)"
        elif final_bal >= 10000:
            st_p["quant_grade"] = "B (Intermediate)"
        else:
            st_p["quant_grade"] = "C (Novice)"

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

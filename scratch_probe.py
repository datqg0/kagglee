import copy, time
import official_kaggriculture as engine
from match_runner import load_agent, Struct, MockEnv

def probe_match(a0_path, a1_path, seed=42):
    a0 = load_agent(a0_path)
    a1 = load_agent(a1_path)
    agents = [a0, a1]

    env = MockEnv({"seed": seed})
    env.info = {"seed": seed}

    state = [
        Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0)),
        Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0))
    ]
    engine._initialize(state, env)

    # Trackers
    total_sales_val = [0, 0]
    total_spent_val = [0, 0]
    idle_worker_turns = [0, 0]
    total_worker_turns = [0, 0]
    harvest_counts = [{}, {}]
    sales_by_item = [{}, {}]

    for step in range(720):
        day = step // 24
        hour = step % 24

        for i in range(2):
            state[i].observation.step = step
            state[i].observation.player = i

        obs_dicts = []
        for i in range(2):
            obs_obj = state[i].observation
            obs_dict = {
                "player": i, "step": step, "day": day, "hour": hour,
                "farms": copy.deepcopy(getattr(obs_obj, "farms", [])),
                "market": copy.deepcopy(getattr(obs_obj, "market", {})),
                "town": copy.deepcopy(getattr(obs_obj, "town", {})),
                "private": copy.deepcopy(getattr(obs_obj, "private", {}))
            }
            obs_dicts.append(obs_dict)

        for i in range(2):
            try:
                act = agents[i](obs_dicts[i])
                state[i].action = act
            except Exception as e:
                state[i].action = {"farmer": ["PASS"], "hands": [], "market": []}

        # Track actions before engine step
        for i in range(2):
            act = state[i].action
            f_act = act.get("farmer", ["PASS"])
            h_acts = act.get("hands", [])
            all_u = [f_act] + h_acts
            total_worker_turns[i] += len(all_u)
            for u in all_u:
                op = u[0] if u else "PASS"
                if op == "PASS":
                    idle_worker_turns[i] += 1
                elif op == "HARVEST":
                    pass # will count in result

            m_acts = act.get("market", [])
            for m in m_acts:
                m_op = m[0] if m else ""
                if m_op == "SELL":
                    item = m[1]
                    qty = m[2] if len(m) > 2 else 1
                    sales_by_item[i][item] = sales_by_item[i].get(item, 0) + qty

        engine.interpreter(state, env)

    print(f"=== PROBE RESULTS (Seed {seed}) ===")
    for i, name in enumerate([a0_path, a1_path]):
        farm = state[i].observation.farms[i]
        priv = state[i].observation.private
        print(f"\nPlayer {i} ({name}):")
        print(f"  Final Money: ${farm['money']}")
        print(f"  Unlocked Quadrants: {farm.get('unlocked_quadrants', [])}")
        print(f"  Shed Remaining: {priv.get('shed', {})}")
        print(f"  Seeds Remaining: {priv.get('seeds', {})}")
        # Count standing plants and animals
        tiles = farm.get("tiles", [])
        plants = {}
        animals = {}
        weeds = 0
        unharvested_units = 0
        for r in range(10):
            for c in range(10):
                t = tiles[r][c]
                if isinstance(t, dict):
                    k = t.get("kind")
                    if k == "PLANT":
                        crop = t.get("crop")
                        plants[crop] = plants.get(crop, 0) + 1
                        unharvested_units += t.get("yield_units", 0)
                    elif k in ("PASTURE", "COOP"):
                        a = t.get("animal")
                        if a: animals[a] = animals.get(a, 0) + 1
                        unharvested_units += t.get("yield_units", 0)
                    elif k == "WEED":
                        weeds += 1
        print(f"  Standing Plants: {plants}")
        print(f"  Standing Animals: {animals}")
        print(f"  Weeds on Farm: {weeds}")
        print(f"  Unharvested Units on Board: {unharvested_units}")
        print(f"  Idle Worker Turns: {idle_worker_turns[i]} / {total_worker_turns[i]} ({idle_worker_turns[i]*100//max(1,total_worker_turns[i])}%)")
        print(f"  Total Items Sold: {sales_by_item[i]}")

if __name__ == '__main__':
    probe_match('abc.py', 'main.py', seed=42)
    probe_match('abc.py', 'pass', seed=100)

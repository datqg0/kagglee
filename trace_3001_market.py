from match_runner import load_agent, Struct, MockEnv
import official_kaggriculture as engine
import copy

def audit_seed_3001():
    agent0_fn = load_agent("main.py")
    agent1_fn = load_agent("pass")
    agents = [agent0_fn, agent1_fn]
    env = MockEnv()
    env.info = {"seed": 3001}

    state = [
        Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0)),
        Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0))
    ]
    engine._initialize(state, env)

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

        # Track hour 0 market actions to see how many hires crowd out sells
        if hour == 0 and day in (13, 15, 20, 25):
            obs = obs_dicts[0]
            priv = obs.get("private", {})
            print(f"Day {day:02d} H00 PRE: Money=${obs['farms'][0]['money']:>8,.1f} | Shed={priv.get('shed')}")

        for i in range(2):
            act = agents[i](obs_dicts[i])
            state[i].action = act

        if hour == 0 and day in (13, 15, 20, 25):
            act0 = state[0].action
            print(f"Day {day:02d} H00 MARKET ORDERS: {act0.get('market')}")

        engine.interpreter(state, env)

        if hour == 23 and day in (12, 13, 15, 20, 24, 29):
            f0 = state[0].observation.farms[0]
            priv = state[0].observation.private
            prices = state[0].observation.market.get("prices", {})
            print(f"Day {day:02d} EOD: Money=${f0['money']:>8,.1f} | Prices(Straw={prices.get('STRAWBERRY')},Milk={prices.get('MILK')},Wool={prices.get('WOOL')}) | Shed={priv.get('shed')}")

audit_seed_3001()

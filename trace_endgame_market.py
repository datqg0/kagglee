from match_runner import load_agent, Struct, MockEnv
import official_kaggriculture as engine
import copy

def trace_d29(seed=1009):
    agent0_fn = load_agent("main.py")
    agent1_fn = load_agent("random")
    agents = [agent0_fn, agent1_fn]
    env = MockEnv()
    env.info = {"seed": seed}

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

        for i in range(2):
            act = agents[i](obs_dicts[i])
            state[i].action = act

        engine.interpreter(state, env)

        if day == 29 and hour >= 18:
            f0 = state[0].observation.farms[0]
            priv = state[0].observation.private
            act = state[0].action
            print(f"Step {step} (D29, H{hour:02d}): Money=${f0['money']:,.1f} | Market_act={act.get('market')} | Shed={priv.get('shed')}")

trace_d29(1009)

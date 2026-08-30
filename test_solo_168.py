import copy
from match_runner import load_agent, Struct, MockEnv
import official_kaggriculture as engine

def solo_seed_168093662():
    seed = 168093662
    for opp_name in ["random", "starter", "challenger_expert.py"]:
        env = MockEnv()
        env.info = {"seed": seed}
        state = [
            Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0)),
            Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0))
        ]
        engine._initialize(state, env)
        a0 = load_agent("main.py")
        a1 = load_agent(opp_name)
        
        for step in range(env.configuration["episodeSteps"]):
            for i in range(2):
                state[i].observation.step = step
                state[i].observation.player = i
            obs_dicts = []
            for i in range(2):
                obs_obj = state[i].observation
                obs_dicts.append({
                    "player": i, "step": step, "day": step // 24, "hour": step % 24,
                    "farms": copy.deepcopy(getattr(obs_obj, "farms", [])),
                    "market": copy.deepcopy(getattr(obs_obj, "market", {})),
                    "town": copy.deepcopy(getattr(obs_obj, "town", {})),
                    "private": copy.deepcopy(getattr(obs_obj, "private", {}))
                })
            state[0].action = a0(obs_dicts[0])
            state[1].action = a1(obs_dicts[1])
            engine.interpreter(state, env)
        
        m0 = state[0].observation.farms[0]["money"]
        m1 = state[1].observation.farms[1]["money"]
        print(f"Seed {seed} vs {opp_name:<20}: main.py=${m0:,.2f} | Opp=${m1:,.2f}")

solo_seed_168093662()

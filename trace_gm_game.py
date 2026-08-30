from match_runner import load_agent, Struct, MockEnv
import official_kaggriculture as engine
import copy
import grandmaster_opponents
import main

def trace_gm_game():
    seed = 21001
    env = MockEnv()
    env.info = {"seed": seed}
    state = [
        Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0)),
        Struct(action={}, reward=0, status="ACTIVE", observation=Struct(step=0))
    ]
    engine._initialize(state, env)
    
    a0 = main.agent
    a1 = grandmaster_opponents.agent_gm_paarth_patel

    for step in range(120): # first 5 days
        day = step // 24
        hour = step % 24
        for i in range(2):
            state[i].observation.step = step
            state[i].observation.player = i
        obs_dicts = []
        for i in range(2):
            obs_obj = state[i].observation
            obs_dicts.append({
                "player": i, "step": step, "day": day, "hour": hour,
                "farms": copy.deepcopy(getattr(obs_obj, "farms", [])),
                "market": copy.deepcopy(getattr(obs_obj, "market", {})),
                "town": copy.deepcopy(getattr(obs_obj, "town", {})),
                "private": copy.deepcopy(getattr(obs_obj, "private", {}))
            })
        act0 = a0(obs_dicts[0])
        act1 = a1(obs_dicts[1])
        state[0].action = act0
        state[1].action = act1

        if hour == 0 and day in (0, 1, 2, 3, 4):
            print(f"Day {day:02d} H00: P0 Act={act0.get('market')} | P1 Act={act1.get('market')}")

        engine.interpreter(state, env)

        if hour == 23 and day in (0, 1, 2, 3, 4):
            f0 = state[0].observation.farms[0]
            f1 = state[1].observation.farms[1]
            p0 = state[0].observation.private
            p1 = state[1].observation.private
            print(f"Day {day:02d} EOD: P0=${f0['money']:>6,.1f} (shed={p0.get('shed')}) | P1=${f1['money']:>6,.1f} (shed={p1.get('shed')})")

trace_gm_game()

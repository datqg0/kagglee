import copy
from match_runner import load_agent, Struct, MockEnv
import official_kaggriculture as engine

def test_seed_168093662():
    seed = 168093662
    print(f"=== TESTING SEED {seed} ===")
    
    agent_main = load_agent("main.py")
    
    # 1. Self-Play (main vs main) on seed 168093662
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
            obs_dicts.append({
                "player": i, "step": step, "day": day, "hour": hour,
                "farms": copy.deepcopy(getattr(obs_obj, "farms", [])),
                "market": copy.deepcopy(getattr(obs_obj, "market", {})),
                "town": copy.deepcopy(getattr(obs_obj, "town", {})),
                "private": copy.deepcopy(getattr(obs_obj, "private", {}))
            })
        
        for i in range(2):
            state[i].action = agent_main(obs_dicts[i])
        
        engine.interpreter(state, env)
        
        if hour == 23 and day in (0, 4, 8, 12, 16, 20, 24, 29):
            f0 = state[0].observation.farms[0]
            f1 = state[1].observation.farms[1]
            p0 = state[0].observation.private
            p1 = state[1].observation.private
            print(f"Day {day:02d} | P0: ${f0['money']:>8,.1f} (shed={sum(p0.get('shed', {}).values())}) | P1: ${f1['money']:>8,.1f} (shed={sum(p1.get('shed', {}).values())})")

    p0_final = state[0].observation.farms[0]["money"]
    p1_final = state[1].observation.farms[1]["money"]
    town_shops = state[0].observation.town.get("unlocked_shops")
    prices = state[0].observation.market.get("prices")
    print(f"\nFinal Result Seed {seed}:")
    print(f"P0 Money: ${p0_final:,.2f}")
    print(f"P1 Money: ${p1_final:,.2f}")
    print(f"Combined Money: ${p0_final + p1_final:,.2f}")
    print(f"Town Shops: {town_shops}")
    print(f"Final Market Prices: {prices}")

if __name__ == "__main__":
    test_seed_168093662()

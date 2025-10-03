from src.components.properties.ability.speLeviathanComponent import SpeLeviathan


def sim():
    # initial cooldown 2.0s for a quick test
    s = SpeLeviathan(is_active=False, cooldown=2.0, cooldown_timer=0.0, salve_ready=True)
    print("initial -> is_active:", s.is_active, "salve_ready:", s.salve_ready, "cooldown_timer:", s.cooldown_timer)

    ok = s.activate()
    print("after activate -> success:", ok, "is_active:", s.is_active, "salve_ready:", s.salve_ready, "cooldown_timer:", s.cooldown_timer)

    # Simulate the attack consuming the is_active flag (engine should do this)
    if s.is_active:
        print("Simulate attack consumption: resetting is_active to False (engine behavior)")
        s.is_active = False

    # Simulate time passing in steps until salve_ready becomes True again
    dt = 0.5
    t = 0.0
    while not s.salve_ready and t < 10.0:
        s.update(dt)
        t += dt
        print(f"t={t:.1f}s -> cooldown_timer={s.cooldown_timer:.2f}, salve_ready={s.salve_ready}")

    print("final -> is_active:", s.is_active, "salve_ready:", s.salve_ready, "cooldown_timer:", s.cooldown_timer)


if __name__ == '__main__':
    sim()

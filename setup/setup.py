import install_commitizen_universal as install_cz
import setup_team_hooks as setup_hooks

if __name__  == "__main__":
    # Initialize hooks
    install_cz.main()
    setup_hooks.main()
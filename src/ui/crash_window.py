import traceback

def show_crash_popup(e):
    try:
        from src.settings.settings import config_manager
        from src.settings.settings import get_project_version
        if config_manager.get('dev_mode', False):
            print(f"Crash Galad Islands: {type(e).__name__}: {e}")
            print(traceback.format_exc())
        import threading
        import tkinter as tk
        import webbrowser
        from urllib.parse import quote_plus

        def popup():
            def open_github_issue():
                version = get_project_version()
                titre = quote_plus("Crash Galad Islands: " + type(e).__name__)
                body = quote_plus(
                    f"## Description du bug\n\nOups ! Le jeu a crashé : {type(e).__name__}: {e}\n\nTraceback:\n{traceback.format_exc()}\n\nVersion: {version}\nMerci de décrire ce que tu faisais juste avant le crash !")
                url = f"https://github.com/Fydyr/Galad-Islands/issues/new?title={titre}&body={body}"
                webbrowser.open_new(url)
            root = tk.Tk()
            root.title("Erreur Galad Islands")
            root.geometry("500x260")
            msg = "Oups ! On dirait que le jeu s'est transformé en Kamikaze !\n\n" + \
                f"{type(e).__name__}: {e}"
            label = tk.Label(root, text=msg, fg="#d32f2f", font=(
                "Arial", 12), wraplength=480, justify="left")
            label.pack(pady=20)
            btn = tk.Button(root, text="Signaler le bug sur GitHub", command=open_github_issue,
                            bg="#1976d2", fg="white", font=("Arial", 11, "bold"))
            btn.pack(pady=10)
            btn2 = tk.Button(root, text="Fermer",
                             command=root.destroy, font=("Arial", 10))
            btn2.pack(pady=5)
            root.mainloop()

        t = threading.Thread(target=popup)
        t.start()
    except Exception:
        print("Erreur critique lors de l'affichage de la popup tkinter !")
        print(f"Crash Galad Islands: {type(e).__name__}: {e}")
        print(traceback.format_exc())

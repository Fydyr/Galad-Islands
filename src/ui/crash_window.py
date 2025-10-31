import traceback
import locale
import os

def show_crash_popup(e):
    try:
        from src.settings.settings import config_manager
        from src.settings.settings import get_project_version
        
        # Essayer d'accéder à la configuration de langue
        try:
            language = config_manager.get('language', 'auto')
            dev_mode = config_manager.get('dev_mode', False)
        except Exception as config_error:
            # Easter egg activé : problème de configuration = Tour de Babel !
            language = 'babel'
            dev_mode = False
        
        if dev_mode:
            print(f"Crash Galad Islands: {type(e).__name__}: {e}")
            print(traceback.format_exc())
        
        import threading
        import tkinter as tk
        import webbrowser
        from urllib.parse import quote_plus

        def popup():
            # Détermination de la langue
            if language == 'babel': # Cette easter egg s'affiche si le message d'error ne parvient pas à récupérer la langue
                # Easter egg : Tour de Babel - confusion des langues
                messages = {
                    'title': "Galad Islands Error",
                    'main_msg': "Who built the Tower of Babel?\n\nNobody! God confused their languages!\n\nAnd now... i don't even know what language to use!\n\n",
                    'traceback_label': "Technical details :",
                    'github_button': "Report Bug",
                    'close_button': "Close",
                    'github_title': "Crash Galad Islands: ",
                    'github_body': "## Bug Description\n\nOops! The game crashed: {type}: {msg}\n\nTraceback:\n{traceback}\n\nVersion: {version}\nPlease describe what you were doing just before the crash!"
                }
            elif language == 'fr':
                messages = {
                    'title': "Erreur Galad Islands",
                    'main_msg': "Oups ! On dirait que le jeu s'est transformé en Kamikaze !\n\n",
                    'traceback_label': "Détails techniques de l'erreur :",
                    'github_button': "Signaler le bug sur GitHub",
                    'close_button': "Fermer",
                    'github_title': "Crash Galad Islands: ",
                    'github_body': "## Bug description\n\nOups ! Le jeu a crashé : {type}: {msg}\n\nTraceback:\n{traceback}\n\nVersion: {version}\nMerci de décrire ce que tu faisais juste before le crash !"
                }
            elif language == 'en':
                messages = {
                    'title': "Galad Islands Error",
                    'main_msg': "Oops! It looks like the game turned into a Kamikaze!\n\n",
                    'traceback_label': "Technical error details:",
                    'github_button': "Report bug on GitHub", 
                    'close_button': "Close",
                    'github_title': "Galad Islands Crash: ",
                    'github_body': "## Bug Description\n\nOops! The game crashed: {type}: {msg}\n\nTraceback:\n{traceback}\n\nVersion: {version}\nPlease describe what you were doing just before the crash!"
                }
            else:  # auto ou autre
                try:
                    system_lang = locale.getlocale()[0]
                    is_french = system_lang and system_lang.startswith('fr')
                except:
                    is_french = False
                
                if is_french:
                    messages = {
                        'title': "Erreur Galad Islands",
                        'main_msg': "Oups ! On dirait que le jeu s'est transformé en Kamikaze !\n\n",
                        'traceback_label': "Détails techniques de l'erreur :",
                        'github_button': "Signaler le bug sur GitHub",
                        'close_button': "Fermer",
                        'github_title': "Crash Galad Islands: ",
                        'github_body': "## Bug description\n\nOups ! Le jeu a crashé : {type}: {msg}\n\nTraceback:\n{traceback}\n\nVersion: {version}\nMerci de décrire ce que tu faisais juste before le crash !"
                    }
                else:
                    messages = {
                        'title': "Galad Islands Error",
                        'main_msg': "Oops! It looks like the game turned into a Kamikaze!\n\n",
                        'traceback_label': "Technical error details:",
                        'github_button': "Report bug on GitHub", 
                        'close_button': "Close",
                        'github_title': "Galad Islands Crash: ",
                        'github_body': "## Bug Description\n\nOops! The game crashed: {type}: {msg}\n\nTraceback:\n{traceback}\n\nVersion: {version}\nPlease describe what you were doing just before the crash!"
                    }
            
            def open_github_issue():
                version = get_project_version()
                titre = quote_plus(messages['github_title'] + type(e).__name__)
                body = quote_plus(
                    messages['github_body'].format(
                        type=type(e).__name__, 
                        msg=str(e), 
                        traceback=traceback.format_exc(), 
                        version=version
                    )
                )
                url = f"https://github.com/Fydyr/Galad-Islands/issues/new?title={titre}&body={body}"
                webbrowser.open_new(url)
            
            root = tk.Tk()
            root.title(messages['title'])
            root.geometry("700x500")
            
            # Message principal
            msg = messages['main_msg'] + f"{type(e).__name__}: {e}"
            label = tk.Label(root, text=msg, fg="#d32f2f", font=(
                "Arial", 12), wraplength=680, justify="left")
            label.pack(pady=(20, 10))
            
            # Étiquette pour la zone de traceback
            traceback_label = tk.Label(root, text=messages['traceback_label'], font=("Arial", 10, "bold"))
            traceback_label.pack(pady=(0, 5))
            
            # Zone de texte pour le traceback
            text_frame = tk.Frame(root)
            text_frame.pack(pady=(0, 20), padx=20, fill=tk.BOTH, expand=True)
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget = tk.Text(text_frame, height=15, wrap=tk.WORD, yscrollcommand=scrollbar.set, font=("Courier", 11))
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=text_widget.yview)
            
            # Insérer le traceback complet
            tb_text = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            text_widget.insert(tk.END, tb_text if tb_text else "No traceback available")
            text_widget.config(state=tk.DISABLED)  # Rendre le texte non éditable
            
            # Cadre pour les boutons
            button_frame = tk.Frame(root)
            button_frame.pack(pady=(0, 20))
            
            btn = tk.Button(button_frame, text=messages['github_button'], command=open_github_issue,
                            bg="#1976d2", fg="white", font=("Arial", 11, "bold"))
            btn.pack(side=tk.LEFT, padx=(0, 10))
            
            btn2 = tk.Button(button_frame, text=messages['close_button'],
                             command=root.destroy, font=("Arial", 10))
            btn2.pack(side=tk.LEFT)
            
            root.mainloop()

        t = threading.Thread(target=popup)
        t.start()
    except Exception:
        print("Erreur critique lors de l'affichage de la popup tkinter !")
        print(f"Crash Galad Islands: {type(e).__name__}: {e}")
        print(traceback.format_exc())

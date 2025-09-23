# options_window.py
# Fenêtre des options pour Galad Islands

import tkinter as tk
import pygame
import settings

def show_options_window():
	"""Affiche la fenêtre des options du jeu"""
	win = tk.Tk()
	win.title("Options - Galad Islands")
	win.minsize(650, 500)  # Taille minimale pour la fenêtre
	win.geometry("800x600")
	win.configure(bg="#1e1e1e")
	win.resizable(True, True)

	# Titre
	title = tk.Label(win, text="Options du jeu", fg="#FFD700", bg="#1e1e1e", font=("Arial", 18, "bold"))
	title.pack(pady=15, side="top", fill="x")

	# Frame pour les boutons du bas
	bottom_button_frame = tk.Frame(win, bg="#1e1e1e")
	bottom_button_frame.pack(side="bottom", fill="x", pady=20)

	# Frame principale pour le contenu défilable
	main_frame = tk.Frame(win, bg="#1e1e1e")
	main_frame.pack(side="top", fill="both", expand=True)

	# Canvas pour le défilement et son contenu
	main_canvas = tk.Canvas(main_frame, bg="#1e1e1e", highlightthickness=0)
	main_canvas.pack(side="left", fill="both", expand=True)

	# Scrollbar
	scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=main_canvas.yview)
	scrollbar.pack(side="right", fill="y")
	main_canvas.configure(yscrollcommand=scrollbar.set)

	# Frame de contenu à l'intérieur du Canvas
	content_frame = tk.Frame(main_canvas, bg="#1e1e1e")
	content_window = main_canvas.create_window((0, 0), window=content_frame, anchor="nw")

	def _on_frame_configure(event=None):
		main_canvas.configure(scrollregion=main_canvas.bbox("all"))
		# Ajuster la largeur du content_frame à celle du canvas
		main_canvas.itemconfig(content_window, width=main_canvas.winfo_width())

	content_frame.bind("<Configure>", _on_frame_configure)
	main_canvas.bind("<Configure>", _on_frame_configure)

	# Support molette souris (Windows/Mac/Linux)
	def _on_mousewheel(event):
		if event.num == 4:
			main_canvas.yview_scroll(-1, 'units')
		elif event.num == 5:
			main_canvas.yview_scroll(1, 'units')
		else:
			main_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

	# Bind global pour la molette (plus simple et robuste)
	# Utiliser win.bind_all pour capter les événements même si le focus n'est pas strictement
	# sur le canvas (corrige les problèmes sur Windows / Linux / macOS).
	win.bind_all('<MouseWheel>', _on_mousewheel)
	win.bind_all('<Button-4>', _on_mousewheel)
	win.bind_all('<Button-5>', _on_mousewheel)

	# Garantir que le canvas reçoit le focus quand la souris y entre (utile pour quelques gestionnaires)
	main_canvas.bind('<Enter>', lambda e: main_canvas.focus_set())
	main_canvas.bind('<Leave>', lambda e: win.focus_set())

	# Section résolution
	resolution_frame = tk.Frame(content_frame, bg="#2a2a2a", relief="raised", bd=1)
	resolution_frame.pack(pady=10, padx=20, fill="x")

	tk.Label(resolution_frame, text="🖥️ Résolution d'écran", fg="#FFD700", bg="#2a2a2a", font=("Arial", 14, "bold")).pack(pady=10)
	
	# Résolution actuelle
	current_width, current_height = settings.config_manager.get_resolution()
	# Cast safe
	try:
		current_w = int(current_width)
		current_h = int(current_height)
	except (ValueError, TypeError):
		current_w = int(settings.SCREEN_WIDTH)
		current_h = int(settings.SCREEN_HEIGHT)
	current_tile_size = settings.calculate_adaptive_tile_size_for_resolution(current_w, current_h)
	current_res_text = f"Actuelle: {current_w}x{current_h} (Tuiles: {current_tile_size}px)"
	current_label = tk.Label(resolution_frame, text=current_res_text, fg="#90EE90", bg="#2a2a2a", font=("Arial", 12))
	current_label.pack(pady=5)

	# Liste des résolutions disponibles
	resolutions = settings.get_all_resolutions()

	selected_resolution = tk.StringVar(value=f"{current_w}x{current_h}")

	tk.Label(resolution_frame, text="Choisir une nouvelle résolution :", fg="#DDDDDD", bg="#2a2a2a", font=("Arial", 12)).pack(pady=(10, 5))

	# Frame pour les boutons radio
	radio_container = tk.Frame(resolution_frame, bg="#2a2a2a")
	radio_container.pack(pady=5, padx=10, fill="x")

	# Boutons radio pour chaque résolution
	for width, height, description in resolutions:
		tile_size = settings.calculate_adaptive_tile_size_for_resolution(width, height)
		visible_tiles_x = width // tile_size
		visible_tiles_y = height // tile_size
		
		radio_text = f"{description} - Tuiles: {tile_size}px ({visible_tiles_x}x{visible_tiles_y} visibles)"
		
		radio = tk.Radiobutton(
			radio_container,
			text=radio_text,
			variable=selected_resolution,
			value=f"{width}x{height}",
			fg="#DDDDDD",
			bg="#2a2a2a",
			selectcolor="#444444",
			font=("Arial", 10),
			activebackground="#3a3a3a",
			activeforeground="#FFFFFF"
		)
		radio.pack(anchor="w", pady=2)

	# Section affichage
	display_frame = tk.Frame(content_frame, bg="#2a2a2a", relief="raised", bd=1)
	display_frame.pack(pady=10, padx=20, fill="x")
	tk.Label(display_frame, text="🖼️ Mode d'affichage", fg="#FFD700", bg="#2a2a2a", font=("Arial", 14, "bold")).pack(pady=5)

	window_mode = tk.StringVar(value=settings.config_manager.get("window_mode", "windowed"))

	def set_window_mode_cb():
		mode = window_mode.get()
		settings.set_window_mode(mode)
		print(f"Mode d'affichage changé pour : {mode}")

	modes = [("Fenêtré", "windowed"), ("Plein écran", "fullscreen")]
	for text, mode in modes:
		tk.Radiobutton(
			display_frame,
			text=text,
			variable=window_mode,
			value=mode,
			command=set_window_mode_cb,
			fg="#DDDDDD", bg="#2a2a2a", selectcolor="#444444",
			font=("Arial", 10), activebackground="#3a3a3a", activeforeground="#FFFFFF"
		).pack(anchor="w", padx=20)

	# Section audio
	audio_frame = tk.Frame(content_frame, bg="#2a2a2a", relief="raised", bd=1)
	audio_frame.pack(pady=10, padx=20, fill="x")

	tk.Label(audio_frame, text="🔊 Audio", fg="#FFD700", bg="#2a2a2a", font=("Arial", 14, "bold")).pack(pady=5)
	
	def update_volume_label(value):
		volume_label.config(text=f"Volume musique: {int(float(value) * 100)}%")
		
	def set_music_volume_cb(value):
		volume = float(value)
		pygame.mixer.music.set_volume(volume)
		settings.set_music_volume(volume)
		update_volume_label(value)

	initial_volume = settings.config_manager.get('volume_music', 0.5) or 0.5
	volume_label = tk.Label(audio_frame, text=f"Volume musique: {int(initial_volume * 100)}%", fg="#CCCCCC", bg="#2a2a2a", font=("Arial", 10))
	volume_label.pack(pady=2)

	volume_slider = tk.Scale(audio_frame, from_=0, to=1, resolution=0.01, orient="horizontal",
			command=set_music_volume_cb, bg="#2a2a2a", fg="#DDDDDD",
				troughcolor="#555555", highlightbackground="#2a2a2a")
	volume_slider.set(initial_volume)
	volume_slider.pack(pady=5, padx=10, fill="x")

	# Section informations
	info_frame = tk.Frame(win, bg="#2a2a2a", relief="raised", bd=1)
	info_frame.pack(pady=10, padx=20, fill="x")

	tk.Label(info_frame, text="ℹ️ Informations", fg="#FFD700", bg="#2a2a2a", font=("Arial", 14, "bold")).pack(pady=5)
	
	info_text = (
		"• La taille des tuiles s'adapte automatiquement à la résolution\n"
		"• Au minimum 15x10 tuiles sont toujours visibles à l'écran\n"
		"• Les modifications prennent effet immédiatement\n"
	)
	tk.Label(info_frame, text=info_text, fg="#CCCCCC", bg="#2a2a2a", font=("Arial", 10), justify="left").pack(pady=5, padx=10)

	# Boutons d'action
	button_frame = tk.Frame(bottom_button_frame, bg="#1e1e1e")
	button_frame.pack(pady=0) # Pas de padding vertical ici, géré par le conteneur parent

	def apply_resolution():
		selected = selected_resolution.get()
		if selected:
			try:
				width, height = map(int, selected.split('x'))
			except (ValueError, TypeError):
				return

			# Sauvegarder via settings helper
			ok = settings.apply_resolution(width, height)

			if ok:
				# Confirmation utilisateur
				import tkinter.messagebox as msgbox
				success_msg = f"✅ Résolution changée pour {width}x{height}\n\nLes changements prendront effet immédiatement (et sont sauvegardés)."
				msgbox.showinfo("Succès", success_msg)

				# Mettre à jour l'affichage de la résolution actuelle
				new_tile_size = settings.calculate_adaptive_tile_size_for_resolution(width, height)
				current_label.config(text=f"Actuelle: {width}x{height} (Tuiles: {new_tile_size}px)")

				win.destroy()
			else:
				import tkinter.messagebox as msgbox
				msgbox.showerror("Erreur", "Impossible de sauvegarder la configuration.")
			

	def reset_defaults():
		"""Remet les paramètres par défaut"""
		import tkinter.messagebox as msgbox
		if msgbox.askyesno("Confirmation", "Remettre tous les paramètres par défaut ?"):
			ok = settings.reset_defaults()
			if ok:
				msgbox.showinfo("Succès", "Paramètres remis par défaut !")
				win.destroy()
			else:
				msgbox.showerror("Erreur", "Impossible de sauvegarder les paramètres par défaut.")

	tk.Button(button_frame, text="✓ Appliquer & Sauver", command=apply_resolution, 
			 font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", padx=20, pady=5).pack(side="left", padx=5)
	
	
	tk.Button(button_frame, text="🔄 Défaut", command=reset_defaults,
			 font=("Arial", 12), bg="#FF9800", fg="white", padx=20, pady=5).pack(side="left", padx=5)
	
	def close_options():
		# Le save est déjà fait par les helpers mais on s'assure
		settings.config_manager.save_config()
		win.destroy()

	tk.Button(button_frame, text="✖ Fermer", command=close_options, 
			 font=("Arial", 12), bg="#f44336", fg="white", padx=20, pady=5).pack(side="left", padx=5)

	# Centrer la fenêtre
	win.update_idletasks()
	x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
	y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
	win.geometry(f"+{x}+{y}")

	win.mainloop()
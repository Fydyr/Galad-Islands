"""Lightweight Tkinter options window for testing Game Options.

This tool reproduces a subset of `OptionsWindow` but in Tkinter so it can be
launched outside Pygame. It shows available resolutions (builtin + custom),
marks custom entries, allows adding/removing custom resolutions, audio sliders,
language selection and applying/reseting settings to `galad_config.json`.

Run:
    python tools/galad_config.py
"""
from pathlib import Path
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys

# Project config paths 
if os.path.exists(Path(sys.argv[0]).resolve().parent / "galad_config.json"): # when running as compiled app
    CONFIG_PATH = Path(sys.argv[0]).resolve().parent / "galad_config.json"
    RES_PATH = Path(sys.argv[0]).resolve().parent / "galad_resolutions.json"
else:  # when running as script from repo root
    ROOT = Path(__file__).resolve().parents[1]
    CONFIG_PATH = ROOT / "galad_config.json"
    RES_PATH = ROOT / "galad_resolutions.json"


# Import helpers from src (use repo root on sys.path when running normally)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.settings.settings import (
    config_manager, get_available_resolutions, apply_resolution,
    set_window_mode, set_audio_volume, set_camera_sensitivity, reset_to_defaults
)
from src.settings.localization import (
    get_available_languages, get_current_language, set_language, t
)
from src.settings.resolutions import load_custom_resolutions
from src.utils.update_checker import check_for_updates_force
import threading
from src.constants.key_bindings import KEY_BINDING_GROUPS
from src.settings import controls
import pygame  # just to make it run


# Namespace de localisation spécifique à cet outil
TOOL_NS = 'galad_config_tool'


def _T(key: str, default: str | None = None, **kwargs) -> str:
    """Traduction via le gestionnaire central pour l'outil Galad Config Tool.
    - key: clé de traduction
    - default: valeur anglaise par défaut si la clé n'existe pas
    - kwargs: paramètres de formatage
    """
    return t(key, tool=TOOL_NS, default=default, **kwargs)


def load_config():
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text())
        else:
            # Afficher un message d'avertissement bilingue (FR + EN) in une popup Tkinter
            try:
                messagebox.showwarning(
                    _T('warn.config_missing.title', default='Missing configuration file'),
                    _T('warn.config_missing.message', default='Configuration file not found:\n{path}\n\nA new file will be created automatically on first save.', path=CONFIG_PATH)
                )
            except Exception as e:
                print(f"Warning popup failed: {e}")  # Log si Tkinter n'est pas initialisé
    except Exception as e:
        try:
            messagebox.showerror(
                _T('error.config_load.title', default='Configuration error'),
                _T('error.config_load.message', default='Error loading configuration:\n{error}\n\nUsing defaults.', error=str(e))
            )
        except Exception as e:
            print(f"Error popup failed: {e}")  # Log si Tkinter n'est pas initialisé
    return {}


def save_resolutions_list(res_list):
    try:
        RES_PATH.write_text(json.dumps(res_list, indent=4))
        return True
    except Exception as e:
        return False


class GaladConfigApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(_T('window.title', default='Galad Config Tool'))
        self.geometry("900x900")
        self.resizable(True, True)

        # load current settings
        self.config_data = load_config()
        
        # Store initial language for change detection
        self.initial_language = self.config_data.get('language', get_current_language())
        
        # Load custom resolutions with warning if file doesn't exist
        try:
            self.customs = [tuple(r) for r in load_custom_resolutions()]
        except Exception:
            if not RES_PATH.exists():
                messagebox.showinfo(
                    _T('info.custom_res.title', default='Custom resolutions'),
                    _T('info.custom_res.message', default='No custom resolutions file found.\n\nIt will be created automatically when you add your first custom resolution.\n\nLocation: {name}', name=RES_PATH.name)
                )
            self.customs = []

        self._build_ui()
        self._populate_resolutions()
        self._apply_state_from_config()

    def _build_ui(self):
        pad = 8
        root_frm = ttk.Frame(self, padding=pad)
        root_frm.pack(fill=tk.BOTH, expand=True)

        # Notebook for tabs
        self.notebook = ttk.Notebook(root_frm)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Display tab/frame
        frm = ttk.Frame(self.notebook, padding=pad)
        self.notebook.add(frm, text=t('options.display'))

        # Display mode
        self.disp_lab = ttk.Label(frm, text=t('options.display'))
        self.disp_lab.grid(row=0, column=0, sticky=tk.W)
        self.window_mode_var = tk.StringVar(value=self.config_data.get('window_mode', 'windowed'))
        ttk.Radiobutton(frm, text=t('options.window_modes.windowed'), variable=self.window_mode_var, value='windowed').grid(row=1, column=0, sticky=tk.W)
        ttk.Radiobutton(frm, text=t('options.window_modes.fullscreen'), variable=self.window_mode_var, value='fullscreen').grid(row=2, column=0, sticky=tk.W)

        # Resolutions list
        ttk.Separator(frm).grid(row=3, column=0, columnspan=3, sticky='ew', pady=(6, 6))
        self.res_lab = ttk.Label(frm, text=t('options.resolution_section'))
        self.res_lab.grid(row=4, column=0, sticky=tk.W)

        self.res_listbox = tk.Listbox(frm, height=8, width=40)
        self.res_listbox.grid(row=5, column=0, columnspan=2, rowspan=6, sticky='nw', padx=(0, 10))

        # Custom add/remove
        self.w_var = tk.StringVar()
        self.h_var = tk.StringVar()
        ent_w = ttk.Entry(frm, width=6, textvariable=self.w_var)
        ent_h = ttk.Entry(frm, width=6, textvariable=self.h_var)
        ent_w.grid(row=11, column=0, sticky=tk.W)
        ttk.Label(frm, text=' x ').grid(row=11, column=0)
        ent_h.grid(row=11, column=0, sticky=tk.E, padx=(30, 0))

        ttk.Button(frm, text=t('options.add_resolution'), command=self._add_manual).grid(row=12, column=0, sticky=tk.W)
        ttk.Button(frm, text=t('options.add_current_resolution'), command=self._add_current).grid(row=12, column=1, sticky=tk.W)
        ttk.Button(frm, text=t('options.remove_resolution'), command=self._remove_selected).grid(row=12, column=2, sticky=tk.W)

        # Performance settings
        ttk.Separator(frm).grid(row=13, column=0, columnspan=3, sticky='ew', pady=(6, 6))
        ttk.Label(frm, text=t('options.performance')).grid(row=14, column=0, sticky=tk.W)
        
        # Performance mode
        ttk.Label(frm, text=t('options.performance_mode_label')).grid(row=15, column=0, sticky=tk.W)
        self.perf_var = tk.StringVar(value=self.config_data.get('performance_mode', 'auto'))
        perf_combo = ttk.Combobox(frm, values=['auto', 'high', 'medium', 'low'], state="readonly", width=10)
        perf_combo.set(self.perf_var.get())
        perf_combo.bind("<<ComboboxSelected>>", lambda e: self.perf_var.set(perf_combo.get()))
        perf_combo.grid(row=15, column=1, sticky=tk.W)
        
        # VSync
        self.vsync_var = tk.BooleanVar(value=self.config_data.get('vsync', True))
        ttk.Checkbutton(frm, text=t('options.vsync'), variable=self.vsync_var).grid(row=16, column=0, sticky=tk.W, pady=(0, 8))
        
        # FPS Max Slider with visible value
        self.fps_var = tk.IntVar(value=self.config_data.get('max_fps', 60))
        initial_fps = self.fps_var.get()
        if initial_fps == 0:
            label_text = t('options.max_fps_label', fps=t('options.unlimited'))
        else:
            label_text = t('options.max_fps_label', fps=initial_fps)
        self.fps_label = ttk.Label(frm, text=label_text)
        self.fps_label.grid(row=17, column=0, sticky=tk.W)
        def update_fps_label(val):
            fps_val = int(float(val))
            if fps_val == 0:
                self.fps_label.config(text=t('options.max_fps_label', fps=t('options.unlimited')))
            else:
                self.fps_label.config(text=t('options.max_fps_label', fps=fps_val))
        self.fps_scale = ttk.Scale(frm, from_=0, to=240, orient=tk.HORIZONTAL, variable=self.fps_var, command=update_fps_label)
        self.fps_scale.grid(row=17, column=1, columnspan=2, sticky='ew', padx=(10, 0))
        
        # Disable particles
        self.particles_var = tk.BooleanVar(value=self.config_data.get('disable_particles', False))
        ttk.Checkbutton(frm, text=t('options.disable_particles'), variable=self.particles_var).grid(row=18, column=0, sticky=tk.W, pady=(8, 0))
        
        # Disable shadows
        self.shadows_var = tk.BooleanVar(value=self.config_data.get('disable_shadows', False))
        ttk.Checkbutton(frm, text=t('options.disable_shadows'), variable=self.shadows_var).grid(row=19, column=0, sticky=tk.W)

        # Disable AI learning
        self.disable_ai_learning_var = tk.BooleanVar(value=self.config_data.get('disable_ai_learning', False))
        ttk.Checkbutton(frm, text=t('options.disable_ai_learning'), variable=self.disable_ai_learning_var).grid(row=20, column=0, sticky=tk.W, pady=(8, 0))
        
        # AI learning description
        ai_desc_label = ttk.Label(frm, text=t('options.disable_ai_learning_description'), font=("", 8, "italic"), foreground="gray", wraplength=400, justify="left")
        ai_desc_label.grid(row=21, column=0, columnspan=3, sticky=tk.W, pady=(2, 6))

        
        # (Gameplay and Updates options moved to their own tabs)

        # Camera sensitivity (placed after gameplay & updates)
        ttk.Separator(frm).grid(row=26, column=0, columnspan=3, sticky='ew', pady=(6, 6))
        self.camera_var = tk.DoubleVar(value=self.config_data.get('camera_sensitivity', 1.0))
        self.camera_label = ttk.Label(frm, text=t('options.camera_sensitivity', sensitivity=self.camera_var.get()))
        self.camera_label.grid(row=27, column=0, sticky=tk.W)
        self.camera_scale = ttk.Scale(frm, from_=0.2, to=3.0, orient=tk.HORIZONTAL, variable=self.camera_var, command=self._on_camera_changed)
        self.camera_scale.grid(row=28, column=0, columnspan=3, sticky='ew')

        # Language (placed after camera)
        ttk.Separator(frm).grid(row=29, column=0, columnspan=3, sticky='ew', pady=(6, 6))
        ttk.Label(frm, text=t('options.language_section')).grid(row=30, column=0, sticky=tk.W)
        
        # Language dropdown for extensibility
        self.lang_var = tk.StringVar(value=self.config_data.get('language', get_current_language()))
        self.langs_dict = get_available_languages()  # Store for mapping
        lang_names = list(self.langs_dict.values())  # Display names
        current_lang_name = self.langs_dict.get(self.lang_var.get(), lang_names[0] if lang_names else "")
        
        self.lang_combo = ttk.Combobox(frm, values=lang_names, state="readonly", width=15)
        self.lang_combo.set(current_lang_name)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_lang_combo_changed)
        self.lang_combo.grid(row=31, column=0, sticky=tk.W, padx=(0, 10))

        # Language restart note
        self.lang_note_label = ttk.Label(frm, text=t('options.language_restart_note'), font=("", 8, "italic"), foreground="gray")
        self.lang_note_label.grid(row=32, column=0, sticky=tk.W, pady=(2, 0))

        # Ensure the display frame has three columns (keeps layout consistent)
        frm.columnconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)
        frm.columnconfigure(2, weight=1)

        # Action bar (global buttons visible on every tab)
        action_frame = ttk.Frame(root_frm, padding=(6, 8))
        action_frame.pack(fill=tk.X, side=tk.BOTTOM)
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)
        action_frame.columnconfigure(2, weight=1)

        self.default_btn = ttk.Button(action_frame, text=t('options.button_default'), command=self._on_reset)
        self.default_btn.grid(row=0, column=0, sticky=tk.W, padx=(8, 8))

        self.apply_btn = ttk.Button(action_frame, text=t('options.apply'), command=self._on_apply)
        self.apply_btn.grid(row=0, column=1)

        self.close_btn = ttk.Button(action_frame, text=t('options.button_close'), command=self.destroy)
        self.close_btn.grid(row=0, column=2, sticky=tk.E, padx=(8, 8))
        

        # Gameplay tab (moved from Display)
        gameplay_frm = ttk.Frame(self.notebook, padding=pad)
        self.notebook.add(gameplay_frm, text=t('options.gameplay_section'))

        # Show tutorial checkbox and reset button
        self.show_tutorial_var = tk.BooleanVar(value=self.config_data.get('show_tutorial', True))
        ttk.Checkbutton(gameplay_frm, text=t('options.enable_tutorial'), variable=self.show_tutorial_var).grid(row=0, column=0, sticky=tk.W, pady=(4, 4))
        ttk.Button(gameplay_frm, text=_T('button_reset_tutorials', default='Reset tutorials'), command=self._on_reset_tutorials).grid(row=0, column=1, sticky=tk.W, padx=(6, 0))

        # Info label for gameplay tab
        ttk.Label(gameplay_frm, text=_T('gameplay_info', default='Gameplay-related options (tutorials, etc.)'), foreground='gray').grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(4, 10))

        # Updates tab
        updates_frm = ttk.Frame(self.notebook, padding=pad)
        self.notebook.add(updates_frm, text=t('options.updates_section'))

        self.check_updates_var = tk.BooleanVar(value=self.config_data.get('check_updates', False))
        ttk.Checkbutton(updates_frm, text=t('options.check_updates', default='Automatically check for updates'), variable=self.check_updates_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(updates_frm, text=_T('button_check_updates', default='Check now'), command=self._on_check_now).grid(row=0, column=1, sticky=tk.W, padx=(6,0))

        # Info label for updates
        ttk.Label(updates_frm, text=_T('updates_info', default='Update checks and release options'), foreground='gray').grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(4, 10))

        # Audio tab
        audio_frm = ttk.Frame(self.notebook, padding=pad)
        self.notebook.add(audio_frm, text=t('options.audio'))

        ttk.Label(audio_frm, text=t('options.audio')).grid(row=0, column=0, sticky=tk.W)
        self.music_var = tk.DoubleVar(value=self.config_data.get('volume_music', 0.5))
        self.effects_var = tk.DoubleVar(value=self.config_data.get('volume_effects', 0.7))
        self.master_var = tk.DoubleVar(value=self.config_data.get('volume_master', 0.8))

        # Music
        self.music_label = ttk.Label(audio_frm, text=t('options.volume_music_label', volume=int(self.music_var.get() * 100)))
        self.music_label.grid(row=1, column=0, sticky=tk.W)
        self.music_scale = ttk.Scale(audio_frm, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=self.music_var, command=self._on_music_changed)
        self.music_scale.grid(row=2, column=0, columnspan=3, sticky='ew')

        # Effects
        self.effects_label = ttk.Label(audio_frm, text=t('options.volume_effects_label', volume=int(self.effects_var.get() * 100)))
        self.effects_label.grid(row=3, column=0, sticky=tk.W)
        self.effects_scale = ttk.Scale(audio_frm, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=self.effects_var, command=self._on_effects_changed)
        self.effects_scale.grid(row=4, column=0, columnspan=3, sticky='ew')

        # Master volume
        # show master volume with percent for immediate user feedback
        try:
            master_pct = int(round(self.master_var.get() * 100))
        except Exception:
            master_pct = 0
        self.master_label = ttk.Label(audio_frm, text=f"{t('options.master_volume')}: {master_pct}%")
        self.master_label.grid(row=5, column=0, sticky=tk.W)
        self.master_scale = ttk.Scale(audio_frm, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=self.master_var, command=self._on_master_changed)
        self.master_scale.grid(row=6, column=0, columnspan=3, sticky='ew')

        # Controls tab (editable) with scrollbar
        controls_frm = ttk.Frame(self.notebook, padding=pad)
        self.notebook.add(controls_frm, text=t('options.binding_group.control_groups'))
        
        # Create scrollable frame for controls
        canvas = tk.Canvas(controls_frm, height=400)
        scrollbar = ttk.Scrollbar(controls_frm, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.controls_container = self.scrollable_frame
        # build controls UI (comboboxes) in scrollable frame
        self._build_controls_tab(self.scrollable_frame)

        # Configuration tab
        config_frm = ttk.Frame(self.notebook, padding=pad)
        self.notebook.add(config_frm, text=t('options.configuration'))
        
        # Config file selection
        ttk.Label(config_frm, text=t('options.config_file_label')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        
        config_frame = ttk.Frame(config_frm)
        config_frame.grid(row=1, column=0, columnspan=3, sticky='ew', pady=(0, 10))
        config_frame.columnconfigure(0, weight=1)
        
        self.config_path_var = tk.StringVar(value=str(CONFIG_PATH))
        self.config_path_entry = ttk.Entry(config_frame, textvariable=self.config_path_var, width=50)
        self.config_path_entry.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        ttk.Button(config_frame, text=t('options.browse_button'), command=self._browse_config_file).grid(row=0, column=1)
        
        # Resolutions file selection
        ttk.Label(config_frm, text=t('options.resolutions_file_label')).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        
        res_frame = ttk.Frame(config_frm)
        res_frame.grid(row=3, column=0, columnspan=3, sticky='ew', pady=(0, 10))
        res_frame.columnconfigure(0, weight=1)
        
        self.res_path_var = tk.StringVar(value=str(RES_PATH))
        self.res_path_entry = ttk.Entry(res_frame, textvariable=self.res_path_var, width=50)
        self.res_path_entry.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        ttk.Button(res_frame, text=t('options.browse_button'), command=self._browse_res_file).grid(row=0, column=1)
        
        # Apply paths button
        ttk.Button(config_frm, text=t('options.apply_paths'), command=self._apply_paths).grid(row=4, column=0, pady=(10, 0))
        
        # Info label
        self.info_label = ttk.Label(config_frm, text=t('options.default_paths_used'), foreground="green")
        self.info_label.grid(row=5, column=0, columnspan=3, pady=(10, 0))

    def _populate_resolutions(self):
        self.res_listbox.delete(0, tk.END)
        self.res_entries = []
        for w,h,label in get_available_resolutions():
            mark = ''
            if (w,h) in self.customs:
                mark = f" ({t('options.custom_marker')})"
            entry = f"{label}{mark}"
            self.res_entries.append((w,h,entry))
            self.res_listbox.insert(tk.END, entry)

        # Controls tab is rebuilt to reflect current bindings
        try:
            # refresh combobox selections
            for action, combo in getattr(self, 'control_widgets', {}).items():
                current = config_manager.get_key_bindings().get(action)
                if current:
                    combo.set(current[0] if isinstance(current, list) else current)
        except Exception:
            pass

        # Update controls comboboxes labels if needed
        try:
            if hasattr(self, 'control_label_widgets'):
                for act, lbl in self.control_label_widgets.items():
                    # attempt to localize label text if we have the key
                    # label text was stored as (label_key)
                    key = lbl._label_key if hasattr(lbl, '_label_key') else None
                    if key:
                        lbl.configure(text=t(key))
        except Exception:
            pass


    def _apply_state_from_config(self):
        # Select current resolution if present
        cur = (self.config_data.get('screen_width', 800), self.config_data.get('screen_height', 600))
        for idx, (w,h,lab) in enumerate(self.res_entries):
            if (w,h) == cur:
                self.res_listbox.selection_set(idx)
                break

    def _add_manual(self):
        try:
            w = int(self.w_var.get())
            h = int(self.h_var.get())
        except Exception:
            messagebox.showerror(_T('dialog.error.title', default='Error'), t('options.custom_resolution_invalid'))
            return
        self.customs.append((w,h))
        save_resolutions_list([list(x) for x in self.customs])
        self._populate_resolutions()

    def _add_current(self):
        sw = int(self.config_data.get('screen_width', 1920))
        sh = int(self.config_data.get('screen_height', 1080))
        self.customs.append((sw,sh))
        save_resolutions_list([list(x) for x in self.customs])
        self._populate_resolutions()

    def _remove_selected(self):
        sel = self.res_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        w,h,lab = self.res_entries[idx]
        if (w,h) not in self.customs:
            messagebox.showerror(_T('dialog.error.title', default='Error'), t('options.cannot_remove_builtin_resolution'))
            return
        self.customs.remove((w,h))
        save_resolutions_list([list(x) for x in self.customs])
        self._populate_resolutions()

    def _on_music_changed(self, _=None):
        val = self.music_var.get()
        # update label text with current percentage
        try:
            pct = int(round(val * 100))
            self.music_label.configure(text=t('options.volume_music_label', volume=pct))
        except Exception:
            pass

    def _on_effects_changed(self, _=None):
        val = self.effects_var.get()
        try:
            pct = int(round(val * 100))
            self.effects_label.configure(text=t('options.volume_effects_label', volume=pct))
        except Exception:
            pass

    def _on_master_changed(self, _=None):
        # master label doesn't show percent name in current translations, keep default label
        val = self.master_var.get()
        try:
            pct = int(round(val * 100))
            self.master_label.configure(text=f"{t('options.master_volume')}: {pct}%")
        except Exception:
            # if something bad happens keep the basic label
            try:
                self.master_label.configure(text=t('options.master_volume'))
            except Exception:
                pass

    def _on_reset(self):
        reset_to_defaults()
        messagebox.showinfo(_T('dialog.ok.title', default='OK'), _T('msg.reset_done', default='Settings reset to defaults'))
        self.config_data = load_config()
        # refresh UI controls with new defaults if present
        try:
            self.music_var.set(self.config_data.get('volume_music', self.music_var.get()))
            self.effects_var.set(self.config_data.get('volume_effects', self.effects_var.get()))
            self.master_var.set(self.config_data.get('volume_master', self.master_var.get()))
            # update labels
            self._on_music_changed()
            self._on_effects_changed()
        except Exception:
            pass
        self._populate_resolutions()

    def _on_apply(self):
        # apply window mode
        set_window_mode(self.window_mode_var.get())
        # apply resolution from selected list
        sel = self.res_listbox.curselection()
        if sel:
            idx = sel[0]
            w,h,_ = self.res_entries[idx]
            apply_resolution(w,h)
        # audio
        set_audio_volume('music', float(self.music_var.get()))
        set_audio_volume('effects', float(self.effects_var.get()))
        set_audio_volume('master', float(self.master_var.get()))
        # camera sensitivity
        set_camera_sensitivity(float(self.camera_var.get()))
        # performance settings
        config_manager.set("performance_mode", self.perf_var.get())
        config_manager.set("vsync", self.vsync_var.get())
        config_manager.set("disable_particles", self.particles_var.get())
        config_manager.set("disable_shadows", self.shadows_var.get())
        config_manager.set("disable_ai_learning", self.disable_ai_learning_var.get())
        # save audio volumes to config
        try:
            config_manager.set("volume_music", float(self.music_var.get()))
            config_manager.set("volume_effects", float(self.effects_var.get()))
            config_manager.set("volume_master", float(self.master_var.get()))
        except Exception:
            pass

        # max FPS
        config_manager.set("max_fps", self.fps_var.get())
        # save new gameplay & updates options
        try:
            config_manager.set("show_tutorial", bool(self.show_tutorial_var.get()))
            config_manager.set("check_updates", bool(self.check_updates_var.get()))
        except Exception:
            # in case variables aren't present, ignore
            pass
        config_manager.save_config()
        # language
        set_language(self.lang_var.get())
        # save key bindings from controls tab
        try:
            for action, combobox in getattr(self, 'control_widgets', {}).items():
                val = combobox.get()
                if val:
                    config_manager.set_key_binding(action, [val])
            config_manager.save_config()
            controls.refresh_key_bindings()
        except Exception:
            pass
        # refresh UI texts to chosen language
        self._refresh_ui_texts()
        
        # Check if language changed and restart if needed
        current_language = self.lang_var.get()
        if current_language != self.initial_language:
            restart = messagebox.askyesno(
                t('options.language_changed_title'),
                t('options.language_changed_message')
            )
            if restart:
                self.destroy()
                # Restart the application with new language
                import subprocess
                import sys
                subprocess.Popen([sys.executable] + sys.argv)
                return
        
        messagebox.showinfo(_T('dialog.ok.title', default='OK'), _T('msg.apply_done', default='Settings applied'))

    def _on_reset_tutorials(self):
        try:
            config_manager.set("read_tips", [])
            config_manager.save_config()
            messagebox.showinfo(_T('dialog.ok.title', default='OK'), _T('msg.reset_done', default='Tutorial progress has been reset'))
        except Exception as e:
            messagebox.showerror(_T('dialog.error.title', default='Error'), str(e))

    def _on_check_now(self):
        # Run quick update check in a thread to avoid freezing UI
        def _check():
            try:
                res = check_for_updates_force()
                # res is either None or (version, url)
                if res is None:
                    messagebox.showinfo(
                        _T('options.check_updates', default='Check for updates'),
                        _T('options.check_updates_none', default='No update found')
                    )
                else:
                    new_ver, url = res
                    messagebox.showinfo(
                        _T('options.check_updates', default='Check for updates'),
                        _T('options.check_updates_available', default='New version available: {version}\n{url}', version=new_ver, url=url)
                    )
            except Exception as e:
                messagebox.showerror(
                    _T('dialog.error.title', default='Error'),
                    _T('options.check_updates_error', default='Error checking updates: {error}', error=str(e))
                )

        threading.Thread(target=_check, daemon=True).start()

    def _build_controls_tab(self, parent):
        """Create editable controls bindings UI: label + combobox for each action."""
        # possible keys choices (simple list of common tokens)
        possible_keys = [
            'z','s','q','d','a','b','e','tab','space','enter','escape',
            'left','right','up','down','1','2','3','4','5','ctrl','shift','alt'
        ]

        self.control_widgets = {}
        self.control_label_widgets = {}
        self.control_group_labels = {}

        row = 0
        # Show all binding groups
        for group_label, bindings in KEY_BINDING_GROUPS:
            grp_lbl = ttk.Label(parent, text=t(group_label))
            grp_lbl.grid(row=row, column=0, sticky=tk.W, pady=(6, 0))
            self.control_group_labels[group_label] = grp_lbl
            row += 1
            for action, label_key in bindings:
                lbl = ttk.Label(parent, text=t(label_key))
                lbl.grid(row=row, column=0, sticky=tk.W, padx=(6, 0))
                cb = ttk.Combobox(parent, values=possible_keys, width=12)
                current = config_manager.get_key_bindings().get(action)
                if current:
                    cb.set(current[0] if isinstance(current, list) else current)
                cb.grid(row=row, column=1, sticky=tk.W, padx=(6, 0))
                self.control_widgets[action] = cb
                self.control_label_widgets[action] = (lbl, label_key)
                row += 1

        return row

    def _on_lang_changed(self):
        # Apply the language immediately in the UI when selecting
        try:
            set_language(self.lang_var.get())
            self._refresh_ui_texts()
        except Exception:
            pass

    def _on_lang_combo_changed(self, event=None):
        """Handle language selection from dropdown"""
        try:
            # Get selected language name and find corresponding code
            selected_name = self.lang_combo.get()
            selected_code = None
            for code, name in self.langs_dict.items():
                if name == selected_name:
                    selected_code = code
                    break
            
            if selected_code:
                self.lang_var.set(selected_code)
                set_language(selected_code)
                self._refresh_ui_texts()
        except Exception:
            pass

    def _on_camera_changed(self, _=None):
        try:
            self.camera_label.configure(text=t('options.camera_sensitivity', sensitivity=round(self.camera_var.get(), 2)))
        except Exception:
            pass



    def _refresh_ui_texts(self):
        # Update static labels to current translations
        try:
            # Update notebook tab titles
            self.notebook.tab(0, text=t('options.display'))
            for idx in range(len(self.notebook.tabs())):
                title = self.notebook.tab(idx, option='text')
                if 'Audio' in title or title.lower().startswith('audio'):
                    self.notebook.tab(idx, text=t('options.audio'))
                elif 'Control' in title or title.lower().startswith('control'):
                    self.notebook.tab(idx, text=t('options.binding_group.control_groups'))

            # Update Display tab labels
            self.disp_lab.configure(text=t('options.display'))
            self.res_lab.configure(text=t('options.resolution_section'))
            self.camera_label.configure(text=t('options.camera_sensitivity', sensitivity=round(self.camera_var.get(), 2)))
            
            # Update language combobox to reflect current selection
            if hasattr(self, 'lang_combo') and hasattr(self, 'langs_dict'):
                current_lang_code = self.lang_var.get()
                current_lang_name = self.langs_dict.get(current_lang_code, "")
                if current_lang_name and current_lang_name != self.lang_combo.get():
                    self.lang_combo.set(current_lang_name)
            
            # Update language restart note
            if hasattr(self, 'lang_note_label'):
                self.lang_note_label.configure(text=t('options.language_restart_note'))
            
            # Update buttons
            self.default_btn.configure(text=t('options.button_default'))
            self.close_btn.configure(text=t('options.button_close'))
            self.apply_btn.configure(text=t('options.apply'))

            # Update Audio tab labels
            self.music_label.configure(text=t('options.volume_music_label', volume=int(round(self.music_var.get()*100))))
            
            # Update Controls tab - all group labels and action labels
            if hasattr(self, 'control_group_labels'):
                for group_key, label_widget in self.control_group_labels.items():
                    label_widget.configure(text=t(group_key))
            
            if hasattr(self, 'control_label_widgets'):
                for action, (label_widget, label_key) in self.control_label_widgets.items():
                    if 'slot' in label_key:
                        # For control group actions, extract slot number
                        slot_match = None
                        for slot in controls.CONTROL_GROUP_SLOTS:
                            if action.endswith(f"_{slot}"):
                                slot_match = slot
                                break
                        if slot_match:
                            label_widget.configure(text=t(label_key, slot=slot_match))
                        else:
                            label_widget.configure(text=t(label_key))
                    else:
                        label_widget.configure(text=t(label_key))
                        
        except Exception as e:
            messagebox.showwarning("Avertissement", f"Erreur lors de la mise à jour de l'interface:\n{e}")

    def _browse_config_file(self):
        """Ouvrir un dialog pour sélectionner le file galad_config.json"""
        filename = filedialog.askopenfilename(
            title=_T('dialog.config.title', default='Select configuration file'),
            filetypes=[(_T('dialog.filetypes.json', default='JSON files'), "*.json"), (_T('dialog.filetypes.all', default='All files'), "*.*")],
            initialdir=str(CONFIG_PATH.parent),
            initialfile=CONFIG_PATH.name
        )
        if filename:
            self.config_path_var.set(filename)

    def _browse_res_file(self):
        """Ouvrir un dialog pour sélectionner le file galad_resolutions.json"""
        filename = filedialog.askopenfilename(
            title=_T('dialog.res.title', default='Select custom resolutions file'),
            filetypes=[(_T('dialog.filetypes.json', default='JSON files'), "*.json"), (_T('dialog.filetypes.all', default='All files'), "*.*")],
            initialdir=str(RES_PATH.parent),
            initialfile=RES_PATH.name
        )
        if filename:
            self.res_path_var.set(filename)

    def _apply_paths(self):
        """Appliquer les nouveaux chemins de fichiers"""
        global CONFIG_PATH, RES_PATH
        try:
            new_config_path = Path(self.config_path_var.get())
            new_res_path = Path(self.res_path_var.get())
            
            warnings = []
            
            # Check le file de configuration
            if new_config_path.exists():
                CONFIG_PATH = new_config_path
            elif new_config_path.parent.exists():
                CONFIG_PATH = new_config_path
                warnings.append(_T('apply_paths.warn.config_will_create', default='Config: {name} will be created', name=new_config_path.name))
            else:
                warnings.append(_T('apply_paths.warn.config_dir_missing', default='Config: folder {parent} not found', parent=new_config_path.parent))
                
            # Check le file des résolutions
            if new_res_path.exists():
                RES_PATH = new_res_path
            elif new_res_path.parent.exists():
                RES_PATH = new_res_path
                warnings.append(_T('apply_paths.warn.res_will_create', default='Resolutions: {name} will be created', name=new_res_path.name))
            else:
                warnings.append(_T('apply_paths.warn.res_dir_missing', default='Resolutions: folder {parent} not found', parent=new_res_path.parent))
                
            # Recharger les données avec les nouveaux chemins
            self.config_data = load_config()
            try:
                self.customs = [tuple(r) for r in load_custom_resolutions()]
            except Exception:
                self.customs = []
                
            self._populate_resolutions()
            
            if warnings:
                msg = "⚠️ " + _T('apply_paths.warn.prefix', default='Paths applied with warnings:') + "\n" + "\n".join(warnings)
                self.info_label.configure(text=msg, foreground="orange")
            else:
                self.info_label.configure(text="✅ " + _T('apply_paths.ok', default='Paths applied successfully'), foreground="green")
            
        except Exception as e:
            self.info_label.configure(text="❌ " + _T('apply_paths.error', default='Error: {error}', error=str(e)), foreground="red")


if __name__ == '__main__':
    app = GaladConfigApp()
    app.mainloop()

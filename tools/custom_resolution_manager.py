"""Simple resolution manager GUI for Galad Islands.

This standalone tool lets you add, remove and save custom resolutions that the game
can later load and show in its settings menu.

Usage:
    python tools/custom_resolution_manager.py

It reads/writes `galad_resolutions.json` at repository root and reads the current
resolution from `galad_config.json`.
"""
import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "galad_config.json"
RES_PATH = ROOT / "galad_resolutions.json"


def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            return {}
    return {}


def load_resolutions():
    if RES_PATH.exists():
        try:
            return json.loads(RES_PATH.read_text())
        except Exception:
            return []
    return []


def save_resolutions(res_list):
    try:
        RES_PATH.write_text(json.dumps(res_list, indent=4))
        return True
    except Exception as e:
        print("Erreur en sauvegardant:", e)
        return False


class ResolutionManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Galad - Resolution Manager")
        self.geometry("420x360")
        self.res_list = load_resolutions()
        self.config = load_config()

        self._build_ui()
        self._populate_list()

    def _build_ui(self):
        frm = tk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        lbl = tk.Label(frm, text="Résolutions personnalisées", font=(None, 12, 'bold'))
        lbl.pack(anchor=tk.W)

        self.listbox = tk.Listbox(frm, height=10)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(frm)
        btn_frame.pack(fill=tk.X, pady=6)

        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        tk.Entry(btn_frame, width=6, textvariable=self.width_var).pack(side=tk.LEFT)
        tk.Label(btn_frame, text="x").pack(side=tk.LEFT, padx=4)
        tk.Entry(btn_frame, width=6, textvariable=self.height_var).pack(side=tk.LEFT)

        tk.Button(btn_frame, text="Add", command=self._add_manual).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Add current", command=self._add_current).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Remove", command=self._remove_selected).pack(side=tk.LEFT, padx=6)

        save_frame = tk.Frame(frm)
        save_frame.pack(fill=tk.X, pady=6)
        tk.Button(save_frame, text="Save to galad_resolutions.json", command=self._save).pack(side=tk.LEFT)
        tk.Button(save_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT)

        info = tk.Label(frm, text="Les résolutions seront stockées dans galad_resolutions.json\nLe jeu peut être modifié pour charger ce fichier au démarrage des paramètres.", wraplength=380, justify=tk.LEFT)
        info.pack(fill=tk.X, pady=8)

    def _populate_list(self):
        self.listbox.delete(0, tk.END)
        for r in self.res_list:
            self.listbox.insert(tk.END, f"{r[0]} x {r[1]}")

    def _add_manual(self):
        try:
            w = int(self.width_var.get())
            h = int(self.height_var.get())
        except Exception:
            messagebox.showerror("Erreur", "Largeur/Hauteur invalides")
            return
        self.res_list.append([w, h])
        self._populate_list()

    def _add_current(self):
        sw = int(self.config.get("screen_width", 1920))
        sh = int(self.config.get("screen_height", 1080))
        self.res_list.append([sw, sh])
        self._populate_list()

    def _remove_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        del self.res_list[idx]
        self._populate_list()

    def _save(self):
        if save_resolutions(self.res_list):
            messagebox.showinfo("OK", f"Sauvegardé {len(self.res_list)} résolutions dans {RES_PATH}")
        else:
            messagebox.showerror("Erreur", "Impossible de sauvegarder")


if __name__ == "__main__":
    app = ResolutionManagerApp()
    app.mainloop()

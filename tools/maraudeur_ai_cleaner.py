#!/usr/bin/env python3
"""
GUI tool to manage Marauder (Barhamus) AI models.

Features:
- Select the models folder (defaults to user data folder in releases, or <repo>/models in dev)
- Prompt at startup if the default folder doesn't exist
- List existing models in the selected folder
- Delete selected models
- Keep N most recent models
- Delete models older than N days
- Delete ALL models
- Open models folder in file manager

No external dependencies (uses tkinter from standard library).
"""
import os
import sys
import glob
import time
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to sys.path to allow imports from src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.settings.localization import t as game_t # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_default_models_dir() -> Path:
    """Resolve the default folder where AI models are stored.

    - In compiled releases (PyInstaller), we use the OS user data folder:
      - Windows: %APPDATA%/GaladIslands
      - Linux/macOS: ~/.local/share/GaladIslands
    - In development, prefer a local repo folder if it exists.
    """
    app_name = "GaladIslands"
    # Compiled executable (PyInstaller)
    if getattr(sys, "frozen", False):
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", str(Path.home())))
            return base / app_name
        else:
            return Path.home() / ".local" / "share" / app_name
    # Development: try common locations
    candidates = [
        PROJECT_ROOT / "models",
        PROJECT_ROOT / "src" / "models",
        PROJECT_ROOT / "src" / "ia" / "models",
    ]
    for c in candidates:
        if c.exists():
            return c
    return PROJECT_ROOT / "models"

DEFAULT_MODELS_DIR = get_default_models_dir()
CONFIG_PATH = PROJECT_ROOT / ".clean_models_gui.json"

PATTERNS = [
    "barhamus_ai_*.pkl",
    "marauder_ai_*.pkl",
    "maraudeur_ai_*.pkl", # French variant
]


def _ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def find_models(base: Path):
    # If base does not exist, return empty list (caller decides what to do)
    if not base.exists():
        return []
    files = []
    for pat in PATTERNS:
        files.extend(base.glob(pat))
    # Deduplicate and sort by mtime desc
    files = list({p.resolve(): p for p in files}.keys())
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def human_size(nbytes: float) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if nbytes < 1024.0:
            return f"{nbytes:3.1f} {unit}"
        nbytes /= 1024.0
    return f"{nbytes:.1f} PB"


def describe_file(p: Path) -> str:
    st = p.stat()
    mtime = datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    return f"{p.name} \u2014 {human_size(st.st_size)} \u2014 {mtime}"


class CleanerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(self._t("window.title", default="Marauder Models Cleaner"))
        self.geometry("760x520")
        self.minsize(680, 460)

        self.models: list[Path] = []
        self.models_dir: Path = DEFAULT_MODELS_DIR

        self._build_ui()
        self._maybe_prompt_for_folder_at_startup()
        self.refresh()

    def _build_ui(self):
        # Top actions frame
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        ttk.Button(top, text=self._t("btn.choose_folder", default="Choose folder…"), command=self.choose_folder).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text=self._t("btn.refresh", default="Refresh"), command=self.refresh).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text=self._t("btn.open_folder", default="Open folder"), command=self.open_folder).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text=self._t("btn.delete_selected", default="Delete selected"), command=self.delete_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text=self._t("btn.delete_all", default="Delete ALL"), command=self.delete_all).pack(side=tk.LEFT, padx=4)

        # Second row for Keep N and Older than filters
        filters = ttk.Frame(self)
        filters.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0, 8))

        # Keep N
        keep_frame = ttk.Frame(filters)
        keep_frame.pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(keep_frame, text=self._t("label.keep_n", default="Keep most recent N:")).pack(side=tk.LEFT)
        self.keep_n_var = tk.StringVar(value="5")
        ttk.Entry(keep_frame, width=5, textvariable=self.keep_n_var).pack(side=tk.LEFT, padx=4)
        ttk.Button(keep_frame, text=self._t("btn.apply", default="Apply"), command=self.keep_n).pack(side=tk.LEFT)

        # Older than
        older_frame = ttk.Frame(filters)
        older_frame.pack(side=tk.LEFT, padx=12)
        ttk.Label(older_frame, text=self._t("label.delete_older_days", default="Delete older than days:")).pack(side=tk.LEFT)
        self.older_days_var = tk.StringVar(value="7")
        ttk.Entry(older_frame, width=5, textvariable=self.older_days_var).pack(side=tk.LEFT, padx=4)
        ttk.Button(older_frame, text=self._t("btn.apply", default="Apply"), command=self.delete_older_than).pack(side=tk.LEFT)

        # Listbox
        mid = ttk.Frame(self)
        mid.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.listbox = tk.Listbox(mid, selectmode=tk.EXTENDED)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(mid, orient=tk.VERTICAL, command=self.listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scroll.set)

        # Status
        self.status = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    def _t(self, key: str, default: str | None = None, **kwargs) -> str:
        # Use the game's localization manager with tool-specific namespace
        TOOL_NS = "clean_models_gui"
        return game_t(key, tool=TOOL_NS, default=default, **kwargs)

    def _load_config(self) -> dict:
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f) or {}
            except Exception:
                return {}
        return {}

    def _save_config(self, cfg: dict):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _maybe_prompt_for_folder_at_startup(self):
        # Load last used folder from config first
        cfg = self._load_config()
        last_dir = cfg.get("models_dir")
        if last_dir:
            p = Path(last_dir)
            if p.exists():
                self.models_dir = p

        if not self.models_dir.exists():
            # Ask the user to pick an existing folder, or create the default one
            res = messagebox.askyesno(
                self._t("dialog.select_folder.title", default="Select models folder"),
                (
                    self._t("dialog.select_folder.message", default=(
                        "Default models folder not found:\n{path}\n\n"
                        "Do you want to choose an existing folder now?\n"
                        "Click 'No' to create the default folder."
                    ), path=self.models_dir)
                ),
            )
            if res:
                selected = filedialog.askdirectory(
                    title=self._t("dialog.browse.title", default="Select models folder"),
                    initialdir=str(self.models_dir.parent if self.models_dir.parent.exists() else PROJECT_ROOT),
                )
                if selected:
                    self.models_dir = Path(selected)
                else:
                    _ensure_dir(self.models_dir)
            else:
                _ensure_dir(self.models_dir)
        # Persist chosen or created folder
        cfg = self._load_config()
        cfg["models_dir"] = str(self.models_dir)
        self._save_config(cfg)

    def choose_folder(self):
        selected = filedialog.askdirectory(
            title=self._t("dialog.browse.title", default="Select models folder"),
            initialdir=str(self.models_dir if self.models_dir.exists() else PROJECT_ROOT),
        )
        if selected:
            self.models_dir = Path(selected)
            cfg = self._load_config()
            cfg["models_dir"] = str(self.models_dir)
            self._save_config(cfg)
            self.refresh()

    def refresh(self):
        self.models = find_models(self.models_dir)
        self.listbox.delete(0, tk.END)
        for p in self.models:
            self.listbox.insert(tk.END, describe_file(p))
        self.status.set(self._t("status.found_in", default="Found {count} model file(s) in {path}", count=len(self.models), path=self.models_dir))

    def open_folder(self):
        # Ensure the directory exists so the file manager can open it
        _ensure_dir(self.models_dir)
        path = str(self.models_dir)
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f"open '{path}'")
        else:
            os.system(f"xdg-open '{path}' >/dev/null 2>&1 &")

    def get_selected_paths(self):
        indices = self.listbox.curselection()
        return [self.models[i] for i in indices]

    def delete_selected(self):
        items = self.get_selected_paths()
        if not items:
            messagebox.showinfo(self._t("dialog.delete_selected.title", default="Delete selected"), self._t("msg.no_selection", default="No models selected."))
            return
        if not messagebox.askyesno(self._t("dialog.confirm.title", default="Confirm"), self._t("confirm.delete_selected", default="Delete {n} selected model(s)?", n=len(items))):
            return
        deleted = 0
        for p in items:
            try:
                p.unlink(missing_ok=True)
                deleted += 1
            except Exception as e:
                messagebox.showerror(self._t("dialog.error.title", default="Error"), self._t("error.delete_failed", default="Failed to delete {name}: {err}", name=p.name, err=e))
        self.refresh()
        messagebox.showinfo(self._t("dialog.done.title", default="Done"), self._t("msg.deleted_n", default="Deleted {n} file(s).", n=deleted))

    def delete_all(self):
        files = find_models(self.models_dir)
        if not files:
            messagebox.showinfo(self._t("dialog.delete_all.title", default="Delete ALL"), self._t("msg.no_models", default="No models to delete."))
            return
        if not messagebox.askyesno(self._t("dialog.confirm.title", default="Confirm"), self._t("confirm.delete_all", default="Delete ALL ({n}) model file(s)?", n=len(files))):
            return
        for p in files:
            try:
                p.unlink(missing_ok=True)
            except Exception as e:
                messagebox.showerror(self._t("dialog.error.title", default="Error"), self._t("error.delete_failed", default="Failed to delete {name}: {err}", name=p.name, err=e))
        self.refresh()
        messagebox.showinfo(self._t("dialog.done.title", default="Done"), self._t("msg.all_deleted", default="All models deleted."))

    def keep_n(self):
        try:
            n = int(self.keep_n_var.get().strip())
            if n < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(self._t("dialog.invalid_value.title", default="Invalid value"), self._t("error.keep_n_invalid", default="Please enter a valid non-negative integer for N."))
            return
        files = find_models(self.models_dir)
        if len(files) <= n:
            messagebox.showinfo(self._t("dialog.keep_n.title", default="Keep N"), self._t("msg.nothing_to_delete", default="There are {count} models; nothing to delete.", count=len(files)))
            return
        to_delete = files[n:]
        if not messagebox.askyesno(self._t("dialog.confirm.title", default="Confirm"), self._t("confirm.keep_n", default="Keep {n} most recent, delete {m} older model(s)?", n=n, m=len(to_delete))):
            return
        for p in to_delete:
            try:
                p.unlink(missing_ok=True)
            except Exception as e:
                messagebox.showerror(self._t("dialog.error.title", default="Error"), self._t("error.delete_failed", default="Failed to delete {name}: {err}", name=p.name, err=e))
        self.refresh()
        messagebox.showinfo(self._t("dialog.done.title", default="Done"), self._t("msg.keep_n_done", default="Kept {n}, deleted {m}.", n=n, m=len(to_delete)))

    def delete_older_than(self):
        try:
            days = int(self.older_days_var.get().strip())
            if days < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(self._t("dialog.invalid_value.title", default="Invalid value"), self._t("error.days_invalid", default="Please enter a valid non-negative integer for days."))
            return
        cutoff = time.time() - days * 86400
        files = find_models(self.models_dir)
        to_delete = [p for p in files if p.stat().st_mtime < cutoff]
        if not to_delete:
            messagebox.showinfo(self._t("dialog.delete_older.title", default="Delete older than"), self._t("msg.none_older", default="No models older than the specified age."))
            return
        if not messagebox.askyesno(self._t("dialog.confirm.title", default="Confirm"), self._t("confirm.delete_older", default="Delete {n} model(s) older than {days} day(s)?", n=len(to_delete), days=days)):
            return
        for p in to_delete:
            try:
                p.unlink(missing_ok=True)
            except Exception as e:
                messagebox.showerror(self._t("dialog.error.title", default="Error"), self._t("error.delete_failed", default="Failed to delete {name}: {err}", name=p.name, err=e))
        self.refresh()
        messagebox.showinfo(self._t("dialog.done.title", default="Done"), self._t("msg.deleted_old", default="Deleted {n} old model(s).", n=len(to_delete)))


def main():
    app = CleanerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

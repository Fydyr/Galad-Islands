# English translations grouped by category
import importlib
import os

TRANSLATIONS = {}

# Auto-load all category modules in this directory
current_dir = os.path.dirname(__file__)
for filename in os.listdir(current_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        module_name = filename[:-3]  # Remove .py extension
        try:
            module = importlib.import_module(f'.{module_name}', package=__name__)
            if hasattr(module, 'TRANSLATIONS'):
                TRANSLATIONS.update(module.TRANSLATIONS)
        except ImportError:
            # Skip modules that can't be imported (e.g., missing dependencies)
            pass

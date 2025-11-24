# backend/engine/custom_engine_loader.py

import os
import importlib
from backend.utils.logger import get_logger


class CustomEngineLoader:
    """
    CUSTOM ENGINE LOADER – PRO EDITION
    ----------------------------------
    Feladata:
        • minden engine modul automatikus betöltése a /backend/engine könyvtárból
        • engine-registry létrehozása
        • lazy-load (csak amikor szükséges)
        • dependency-k és fallback-ek kezelése
        • FusionEngine, MetaInputBuilder, SelectorEngine integráció

    Használat:
        loader = CustomEngineLoader(config)
        engines = loader.load_all_engines()
        trend_engine = loader.get_engine("trend_engine")
    """

    def __init__(self, config=None, engine_path="backend/engine"):
        self.config = config or {}
        self.engine_path = engine_path
        self.logger = get_logger()

        self.registry = {}     # engine_name -> engine_instance
        self.errors = {}       # engine_name -> error message
        self.loaded = False

    # =====================================================================
    # FÁJL LISTÁZÓ
    # =====================================================================
    def _list_engine_files(self):
        try:
            files = os.listdir(self.engine_path)
            engine_files = [
                f for f in files
                if f.endswith(".py")
                and not f.startswith("__")
                and "custom_engine_loader" not in f
            ]
            return engine_files
        except Exception as e:
            self.logger.error(f"[EngineLoader] Could not list engine directory: {e}")
            return []

    # =====================================================================
    # MODULNÉV KÉPZÉSE
    # =====================================================================
    def _module_path(self, filename):
        """
        "trend_engine.py" → "backend.engine.trend_engine"
        """
        name = filename.replace(".py", "")
        return f"backend.engine.{name}"

    # =====================================================================
    # ENGINE BETÖLTÉSE DINAMIKUS IMPORTTAL
    # =====================================================================
    def _load_engine(self, module_name, class_name):
        try:
            module = importlib.import_module(module_name)
            engine_class = getattr(module, class_name)

            config_section = self.config.get(class_name.replace("Engine", "").lower(), {})
            instance = engine_class(config_section)

            return instance

        except Exception as e:
            self.logger.error(
                f"[EngineLoader] Could not load engine {class_name} from {module_name}: {e}"
            )
            return None

    # =====================================================================
    # CLASS NEVET VAGYOK KÉPZÉSE
    # =====================================================================
    def _guess_class_name(self, module_file):
        """
        "trend_engine.py" → "TrendEngine"
        "weather_engine.py" → "WeatherEngine"
        """
        base = module_file.replace(".py", "")
        parts = base.split("_")
        return "".join([p.capitalize() for p in parts])

    # =====================================================================
    # ÖSSZES ENGINE BETÖLTÉSE
    # =====================================================================
    def load_all_engines(self):
        if self.loaded:
            return self.registry

        engine_files = self._list_engine_files()

        for file in engine_files:
            module_name = self._module_path(file)
            class_name = self._guess_class_name(file)

            engine = self._load_engine(module_name, class_name)

            if engine is None:
                self.errors[class_name] = f"Failed to load {class_name}"
                continue

            self.registry[class_name] = engine

        self.loaded = True

        self.logger.info(
            f"[EngineLoader] Loaded {len(self.registry)} engines, "
            f"{len(self.errors)} errors."
        )

        return self.registry

    # =====================================================================
    # ENGINE LEKÉRÉSE NÉV ALAPJÁN
    # =====================================================================
    def get_engine(self, engine_name):
        """
        Példa: loader.get_engine("TrendEngine")
        """
        if not self.loaded:
            self.load_all_engines()

        if engine_name in self.registry:
            return self.registry[engine_name]

        self.logger.warning(f"[EngineLoader] Engine not found: {engine_name}")
        return None

    # =====================================================================
    # ENGINE FÜGGŐSÉGEK
    # =====================================================================
    def get_dependency(self, engine_name, dependency_name):
        """
        Egy engine függőségének lekérése.
        Példa: "FusionEngine" kér egy "TrendEngine"-t
        """
        engine = self.get_engine(dependency_name)
        if engine:
            return engine

        # fallback
        self.logger.warning(
            f"[EngineLoader] Missing dependency for {engine_name}: "
            f"{dependency_name} → using fallback TemporaryEngine."
        )
        return self.get_engine("TemporaryEngine")

    # =====================================================================
    # ENGINE HIBA LISTA
    # =====================================================================
    def get_errors(self):
        return self.errors

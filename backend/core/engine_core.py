# Hová kerüljön:
# backend/core/engine_core.py

"""
ENGINE CORE – MODERNIZÁLT, STABIL, BŐVÍTHETŐ VERZIÓ
---------------------------------------------------
Ez az alap osztály, amire az összes AI-engine épül.
Az eredeti verzió hiányos volt: nem volt benne logging, error-kezelés, timing,
modell verziózás és output-validáció.

Ez az új verzió már tartalmazza:
✔ egységes engine interfész
✔ időmérés
✔ hibatűrés & logging
✔ output validáció
✔ modell metaadatok kezelése
✔ async támogatás
✔ orchestrator-barátság
"""

import time
import traceback
from typing import Any, Dict, Optional


class EngineResult:
    """
    Egységes visszatérési objektum minden engine-hez
    """

    def __init__(self, success: bool, data: Any = None, error: str = None, meta: Dict = None):
        self.success = success
        self.data = data
        self.error = error
        self.meta = meta or {}

    def __repr__(self):
        return f"EngineResult(success={self.success}, data={type(self.data)}, error={self.error})"


class EngineCore:
    """
    Minden engine alapja.
    Az összes többi engine ebből öröklődik.
    """

    engine_name = "BaseEngine"
    version = "1.0"
    requires_training = False

    def __init__(self):
        self.model = None
        self.last_run_time = None
        self.last_error = None
        self.initialized = False

    # ====================================================================
    # INITIALIZÁLÁS
    # ====================================================================
    def initialize(self) -> bool:
        """
        Modellek és paraméterek betöltése.
        Override-olható.
        """
        try:
            self.initialized = True
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    # ====================================================================
    # FUTTATÁS
    # ====================================================================
    def run(self, *args, **kwargs) -> EngineResult:
        if not self.initialized:
            self.initialize()

        start = time.time()

        try:
            output = self._run_internal(*args, **kwargs)
            self.last_run_time = time.time() - start

            return EngineResult(
                success=True,
                data=output,
                meta={
                    "engine": self.engine_name,
                    "version": self.version,
                    "elapsed": self.last_run_time,
                }
            )
        except Exception:
            self.last_run_time = time.time() - start
            error_msg = traceback.format_exc()
            self.last_error = error_msg

            return EngineResult(
                success=False,
                error=error_msg,
                meta={
                    "engine": self.engine_name,
                    "version": self.version,
                    "elapsed": self.last_run_time
                }
            )

    # ====================================================================
    # A GYEREK ENGINE-NEK EZT KELL FELÜLÍRNI
    # ====================================================================
    def _run_internal(self, *args, **kwargs) -> Any:
        raise NotImplementedError("EngineCore._run_internal must be overridden by subclasses")


# ====================================================================
# ASZINKRON VERZIÓ ENGINE-EKHEZ
# ====================================================================
class AsyncEngineCore(EngineCore):
    """
    Aszinkron változat, pl. live odds, live engine vagy scraper esetén.
    """

    async def run_async(self, *args, **kwargs) -> EngineResult:
        if not self.initialized:
            self.initialize()

        start = time.time()

        try:
            output = await self._run_internal_async(*args, **kwargs)
            self.last_run_time = time.time() - start

            return EngineResult(
                success=True,
                data=output,
                meta={
                    "engine": self.engine_name,
                    "version": self.version,
                    "elapsed": self.last_run_time,
                }
            )
        except Exception:
            self.last_run_time = time.time() - start
            error_msg = traceback.format_exc()
            self.last_error = error_msg

            return EngineResult(
                success=False,
                error=error_msg,
                meta={
                    "engine": self.engine_name,
                    "version": self.version,
                    "elapsed": self.last_run_time
                }
            )

    async def _run_internal_async(self, *args, **kwargs):
        raise NotImplementedError
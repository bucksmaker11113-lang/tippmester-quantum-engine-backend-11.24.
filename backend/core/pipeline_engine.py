# backend/core/pipeline_engine.py

import time
import threading
from backend.utils.logger import get_logger

from backend.core.master_data_loader import MasterDataLoader
from backend.core.fusion_engine import FusionEngine
from backend.core.meta_input_builder import MetaInputBuilder
from backend.core.meta_layer_ensemble_optimizer import MetaLayerEnsembleOptimizer
from backend.core.tip_selector import TipSelector
from backend.core.kombi_engine import KombiEngine
from backend.core.bankroll_engine import BankrollEngine


class PipelineEngine:
    """
    QUANTUM PIPELINE ENGINE – PRO VERSION
    -------------------------------------
    Feladata:
        • Adatbetöltés MasterDataLoader-rel
        • FusionEngine futtatása
        • MetaInputBuilder → meta vektor
        • MetaLayerOptimizer → engine súlyok frissítése
        • TipSelector → végső tipp kiválasztás
        • KombiEngine → kombinált tippek
        • BankrollEngine → tétméretezés
        • Esemény-alapú futtatás (triggered pipeline)
    """

    def __init__(self, config, loaders):
        """
        loaders = {
            "tmx": tmx_scraper,
            "intl": intl_scraper,
            "flash": flash_scraper,
            "sofa": sofa_scraper
        }
        """
        self.config = config
        self.logger = get_logger()

        # Core modules
        self.data_loader = MasterDataLoader(
            config,
            loaders["tmx"],
            loaders["intl"],
            loaders["flash"],
            loaders["sofa"]
        )
        self.fusion = FusionEngine(config)
        self.meta_builder = MetaInputBuilder(config)
        self.meta_optimizer = MetaLayerEnsembleOptimizer(config)
        self.selector = TipSelector(config)
        self.kombi = KombiEngine(config)
        self.bankroll = BankrollEngine(config)

        self.logger.info("[PipelineEngine] Initialized successfully.")

    # ------------------------------------------------------------------
    # MAIN PIPELINE STEP
    # ------------------------------------------------------------------
    def process_match(self, match):
        """
        Egyetlen meccs teljes AI tipp pipeline-ja.
        """

        # 1) Adatok betöltése
        m = self.data_loader.load_match_data(match)

        # 2) FusionEngine – multi-engine összevonás
        fusion_out = self.fusion.fuse(m)

        # 3) Meta Input Builder – meta feature vector
        meta_input = self.meta_builder.build_meta_input(
            fusion_out,
            fusion_out["engine_outputs"],
            m
        )

        # 4) Meta Optimizer – engine súly frissítés
        self.meta_optimizer.update_weights(
            list(fusion_out["engine_outputs"].keys())
        )

        # 5) Tipp kiválasztás
        tip = self.selector.select(
            fusion_out,
            meta_input,
            m
        )
        if not tip:
            return None

        # 6) KombiEngine (ha több tipp)
        kombik = self.kombi.generate_kombi([tip])

        # 7) BankrollEngine – tét meghatározása
        tip["stake"] = self.bankroll.calculate_stake(
            tip["probability"],
            tip["value_score"],
            tip.get("risk", 0.5)
        )

        return {
            "match_id": match["match_id"],
            "tip": tip,
            "kombik": kombik,
            "meta_input_dim": len(meta_input),
            "fusion": fusion_out
        }

    # ------------------------------------------------------------------
    # SCHEDULED DAILY RUN
    # ------------------------------------------------------------------
    def run_daily(self, matches):
        results = []
        for m in matches:
            out = self.process_match(m)
            if out:
                results.append(out)

        return results

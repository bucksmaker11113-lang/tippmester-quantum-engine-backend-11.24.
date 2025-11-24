# backend/engine/deep_value/train_value_model.py

import os
import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
from backend.utils.logger import get_logger
from backend.engine.deep_value.deep_value_engine import DeepValueNet


# ==============================================================
# DATASET WRAPPER
# ==============================================================
class DeepValueDataset(Dataset):
    """
    A TrainingPipeline által elmentett minták betöltése tanításhoz.
    sample = {
        "features": fv,
        "meta_features": mv,
        "label": float(label),
        "ev": float(ev),
        "profit": float(profit)
    }

    Mi itt CSAK a meta_features → label-t tanítjuk!!
    """

    def __init__(self, samples):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        row = self.samples[idx]

        # deep value network → meta feature vector kell
        x = row["meta_features"].astype(np.float32)
        y = float(row["label"])  # label = value target

        return x, y


# ==============================================================
# TRAINER CLASS
# ==============================================================
class DeepValueTrainer:
    """
    Deep Value Model Training – PRO VERSION
    ---------------------------------------
    • Mini-batch training
    • Early stopping
    • LR scheduler
    • Model checkpointing
    • Automatic input_dim detection
    """

    def __init__(self, config, training_pipeline):
        self.config = config
        self.training_pipeline = training_pipeline
        self.logger = get_logger()

        dv_conf = config.get("deep_value", {})

        self.model_path = dv_conf.get(
            "model_path", "backend/data/models/deep_value_model.pth"
        )
        self.batch_size = dv_conf.get("batch_size", 64)
        self.epochs = dv_conf.get("epochs", 20)
        self.lr = dv_conf.get("learning_rate", 0.0007)
        self.input_dim = dv_conf.get("input_dim", 128)
        self.patience = dv_conf.get("early_stopping_patience", 4)

        # Create model
        self.model = DeepValueNet(input_dim=self.input_dim)
        self.device = "cpu"
        self.model.to(self.device)

        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", factor=0.5, patience=2, verbose=True
        )
        self.loss_fn = torch.nn.MSELoss()

    # ==============================================================
    # LOAD DATASET
    # ==============================================================
    def load_training_data(self):
        samples = self.training_pipeline.load_dataset()

        # Csak olyan mintákat használunk, aminek megfelelő a meta_input dimenziója
        valid = [s for s in samples if len(s["meta_features"]) == self.input_dim]

        if len(valid) < 200:
            self.logger.warning("[DeepValueTrainer] FIGYELEM: túl kevés minta (<200).")
        else:
            self.logger.info(f"[DeepValueTrainer] Minták betöltve: {len(valid)} db")

        return valid

    # ==============================================================
    # TRAIN LOOP
    # ==============================================================

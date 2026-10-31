"""
Training Pipeline & Validation Loop for ProkBERT Attention AMR Model
Handles multi-epoch optimization, gradient clipping, early stopping, and checkpointing.
"""

import time
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score, roc_auc_score, hamming_loss, accuracy_score


class GenomicAMRTrainer:
    """End-to-end trainer for ProkBERT + Attention Pooling model."""

    def __init__(
        self,
        model: torch.nn.Module,
        criterion: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        device: Optional[torch.device] = None,
        scheduler: Optional[Any] = None,
        max_grad_norm: float = 1.0,
        checkpoint_dir: str = "models/checkpoints"
    ):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model.to(self.device)
        self.criterion = criterion
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.max_grad_norm = max_grad_norm
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.history: Dict[str, List[float]] = {
            "train_loss": [],
            "val_loss": [],
            "val_macro_f1": [],
            "val_hamming_loss": [],
            "val_subset_acc": []
        }

    def train_epoch(self, dataloader: DataLoader) -> float:
        """Run one training epoch."""
        self.model.train()
        total_loss = 0.0

        for batch in dataloader:
            input_ids = batch["input_ids"].to(self.device)
            attention_mask = batch["attention_mask"].to(self.device)
            bag_mask = batch["bag_mask"].to(self.device)
            labels = batch["labels"].to(self.device)

            self.optimizer.zero_grad()
            outputs = self.model(input_ids, attention_mask, bag_mask)
            logits = outputs["logits"]

            loss = self.criterion(logits, labels)
            loss.backward()

            if self.max_grad_norm > 0:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)

            self.optimizer.step()
            total_loss += loss.item()

        if self.scheduler is not None:
            self.scheduler.step()

        return total_loss / max(len(dataloader), 1)

    def evaluate(self, dataloader: DataLoader) -> Dict[str, float]:
        """Evaluate model on validation or test dataloader."""
        self.model.eval()
        total_loss = 0.0
        all_preds = []
        all_targets = []
        all_probs = []

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                bag_mask = batch["bag_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = self.model(input_ids, attention_mask, bag_mask)
                logits = outputs["logits"]
                probs = outputs["probabilities"]

                loss = self.criterion(logits, labels)
                total_loss += loss.item()

                preds = (probs >= 0.5).float()

                all_probs.append(probs.cpu().numpy())
                all_preds.append(preds.cpu().numpy())
                all_targets.append(labels.cpu().numpy())

        all_probs = np.vstack(all_probs)
        all_preds = np.vstack(all_preds)
        all_targets = np.vstack(all_targets)

        # Multi-label metrics
        macro_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
        micro_f1 = f1_score(all_targets, all_preds, average="micro", zero_division=0)
        h_loss = hamming_loss(all_targets, all_preds)
        subset_acc = accuracy_score(all_targets, all_preds)

        try:
            auc = roc_auc_score(all_targets, all_probs, average="macro")
        except ValueError:
            auc = 0.5

        return {
            "loss": total_loss / max(len(dataloader), 1),
            "macro_f1": float(macro_f1),
            "micro_f1": float(micro_f1),
            "hamming_loss": float(h_loss),
            "subset_accuracy": float(subset_acc),
            "roc_auc": float(auc)
        }

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 15,
        patience: int = 5,
        model_name: str = "best_prokbert_attnpool.pt"
    ) -> Dict[str, List[float]]:
        """Full training loop with early stopping."""
        best_val_f1 = -1.0
        patience_counter = 0
        best_ckpt_path = self.checkpoint_dir / model_name

        print(f"Starting training on {self.device} for {epochs} epochs...")

        for epoch in range(1, epochs + 1):
            t0 = time.time()
            train_loss = self.train_epoch(train_loader)
            val_metrics = self.evaluate(val_loader)
            elapsed = time.time() - t0

            val_loss = val_metrics["loss"]
            val_f1 = val_metrics["macro_f1"]
            val_hloss = val_metrics["hamming_loss"]
            val_subset = val_metrics["subset_accuracy"]

            self.history["train_loss"].append(train_loss)
            self.history["val_loss"].append(val_loss)
            self.history["val_macro_f1"].append(val_f1)
            self.history["val_hamming_loss"].append(val_hloss)
            self.history["val_subset_acc"].append(val_subset)

            print(
                f"Epoch {epoch:02d}/{epochs:02d} [{elapsed:.1f}s] | "
                f"Train Loss: {train_loss:.4f} | "
                f"Val Loss: {val_loss:.4f} | "
                f"Val Macro-F1: {val_f1:.4f} | "
                f"Subset Acc: {val_subset:.3f} | "
                f"Hamming Loss: {val_hloss:.4f}",
                flush=True
            )

            # Checkpoint on best validation Macro-F1
            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                patience_counter = 0
                torch.save(self.model.state_dict(), best_ckpt_path)
                print(f"  --> Saved new best checkpoint to {best_ckpt_path} (Macro-F1: {best_val_f1:.4f})", flush=True)
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"Early stopping triggered after {epoch} epochs (Best Val Macro-F1: {best_val_f1:.4f})", flush=True)
                    break

        # Load best weights before returning
        if best_ckpt_path.exists():
            self.model.load_state_dict(torch.load(best_ckpt_path, map_location=self.device))
            print(f"Loaded best checkpoint weights from {best_ckpt_path}")

        return self.history


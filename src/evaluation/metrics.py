"""
Multi-Label AMR Evaluation Suite & Publication Figure Generator
Computes comprehensive clinical and ML performance metrics,
generates ROC curves, PR curves, Confusion Matrices, and Benchmark Comparisons.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from sklearn.metrics import (
    accuracy_score,
    hamming_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
    roc_curve,
    precision_recall_curve,
    confusion_matrix
)

ANTIBIOTICS = [
    "Ampicillin",
    "Cefotaxime",
    "Ceftazidime",
    "Ciprofloxacin",
    "Gentamicin"
]
CLASS_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


class MultiLabelEvaluator:
    """Computes comprehensive multi-label classification metrics across all classes."""

    def __init__(self, target_names: Optional[List[str]] = None):
        self.target_names = target_names or ANTIBIOTICS

    def find_optimal_thresholds(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray
    ) -> np.ndarray:
        """Find optimal decision threshold per class that maximizes F1 score on validation set."""
        optimal_thresholds = []
        for i in range(y_true.shape[1]):
            best_t = 0.5
            best_f1 = -1.0
            for t in np.linspace(0.15, 0.85, 71):
                f1 = f1_score(y_true[:, i], (y_prob[:, i] >= t).astype(int), zero_division=0)
                if f1 > best_f1:
                    best_f1 = f1
                    best_t = t
            optimal_thresholds.append(round(float(best_t), 3))
        return np.array(optimal_thresholds)

    def evaluate_predictions(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        threshold: Any = 0.5
    ) -> Dict[str, Any]:
        """
        Calculates global and class-wise metrics.
        Args:
            y_true: (N, C) binary ground truth
            y_prob: (N, C) predicted probabilities
            threshold: float or array of shape (C,) class-specific thresholds
        """
        if isinstance(threshold, (list, np.ndarray)):
            thresh_arr = np.array(threshold).reshape(1, -1)
            y_pred = (y_prob >= thresh_arr).astype(int)
        else:
            y_pred = (y_prob >= threshold).astype(int)
        num_classes = y_true.shape[1]

        # Global Multi-Label Metrics
        subset_acc = accuracy_score(y_true, y_pred)
        h_loss = hamming_loss(y_true, y_pred)
        macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
        micro_f1 = f1_score(y_true, y_pred, average="micro", zero_division=0)
        weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

        try:
            macro_auc = roc_auc_score(y_true, y_prob, average="macro")
        except ValueError:
            macro_auc = 0.5

        try:
            macro_pr_auc = average_precision_score(y_true, y_prob, average="macro")
        except ValueError:
            macro_pr_auc = 0.5

        # Class-Wise Metrics
        class_metrics = []
        for i, name in enumerate(self.target_names):
            yt = y_true[:, i]
            yp = y_pred[:, i]
            pr = y_prob[:, i]

            acc = accuracy_score(yt, yp)
            prec = precision_score(yt, yp, zero_division=0)
            rec = recall_score(yt, yp, zero_division=0)
            f1 = f1_score(yt, yp, zero_division=0)

            try:
                auc = roc_auc_score(yt, pr)
            except ValueError:
                auc = 0.5

            try:
                prauc = average_precision_score(yt, pr)
            except ValueError:
                prauc = 0.5

            tn, fp, fn, tp = confusion_matrix(yt, yp, labels=[0, 1]).ravel()
            spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0

            class_metrics.append({
                "Antibiotic": name,
                "Accuracy": acc,
                "Precision": prec,
                "Recall (Sensitivity)": rec,
                "Specificity": spec,
                "F1-Score": f1,
                "ROC-AUC": auc,
                "PR-AUC": prauc,
                "TP": int(tp), "FP": int(fp), "FN": int(fn), "TN": int(tn)
            })

        class_df = pd.DataFrame(class_metrics)

        return {
            "Subset_Accuracy": float(subset_acc),
            "Hamming_Loss": float(h_loss),
            "Macro_F1": float(macro_f1),
            "Micro_F1": float(micro_f1),
            "Weighted_F1": float(weighted_f1),
            "Macro_ROC_AUC": float(macro_auc),
            "Macro_PR_AUC": float(macro_pr_auc),
            "Class_Metrics_Table": class_df
        }

    def plot_roc_curves(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        save_path: Optional[str] = "figures/roc_curves.png"
    ):
        """Plot publication-quality multi-label ROC curves."""
        plt.figure(figsize=(8, 6), dpi=300)
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

        for i, (name, color) in enumerate(zip(self.target_names, CLASS_COLORS)):
            try:
                fpr, tpr, _ = roc_curve(y_true[:, i], y_prob[:, i])
                auc_val = roc_auc_score(y_true[:, i], y_prob[:, i])
                plt.plot(fpr, tpr, color=color, lw=2.2, label=f"{name} (AUC = {auc_val:.3f})")
            except ValueError:
                pass

        plt.plot([0, 1], [0, 1], color="grey", lw=1.5, linestyle="--", label="Chance Baseline")
        plt.xlim([-0.02, 1.02])
        plt.ylim([-0.02, 1.05])
        plt.xlabel("False Positive Rate (1 - Specificity)", fontsize=12, fontweight="bold")
        plt.ylabel("True Positive Rate (Sensitivity)", fontsize=12, fontweight="bold")
        plt.title("Multi-Label AMR ROC Curves (ProkBERT + Attention Pooling)", fontsize=14, fontweight="bold", pad=12)
        plt.legend(loc="lower right", frameon=True, fontsize=10)
        plt.tight_layout()

        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300)
            print(f"Saved ROC curves figure to {save_path}")
        plt.close()

    def plot_precision_recall_curves(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        save_path: Optional[str] = "figures/pr_curves.png"
    ):
        """Plot Precision-Recall curves across all 5 antibiotic classes."""
        plt.figure(figsize=(8, 6), dpi=300)
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

        for i, (name, color) in enumerate(zip(self.target_names, CLASS_COLORS)):
            try:
                prec, rec, _ = precision_recall_curve(y_true[:, i], y_prob[:, i])
                pr_auc = average_precision_score(y_true[:, i], y_prob[:, i])
                plt.plot(rec, prec, color=color, lw=2.2, label=f"{name} (PR-AUC = {pr_auc:.3f})")
            except ValueError:
                pass

        plt.xlim([-0.02, 1.02])
        plt.ylim([-0.02, 1.05])
        plt.xlabel("Recall", fontsize=12, fontweight="bold")
        plt.ylabel("Precision", fontsize=12, fontweight="bold")
        plt.title("Multi-Label AMR Precision-Recall Curves", fontsize=14, fontweight="bold", pad=12)
        plt.legend(loc="lower left", frameon=True, fontsize=10)
        plt.tight_layout()

        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300)
            print(f"Saved PR curves figure to {save_path}")
        plt.close()

    def plot_confusion_matrices(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        save_path: Optional[str] = "figures/confusion_matrices.png"
    ):
        """Plot a 5-panel confusion matrix grid for each antibiotic."""
        fig, axes = plt.subplots(1, 5, figsize=(20, 4), dpi=300)

        for i, (name, ax) in enumerate(zip(self.target_names, axes)):
            cm = confusion_matrix(y_true[:, i], y_pred[:, i], labels=[0, 1])
            sns.heatmap(
                cm,
                annot=True,
                fmt="d",
                cmap="Blues",
                cbar=False,
                ax=ax,
                annot_kws={"size": 14, "weight": "bold"}
            )
            ax.set_title(name, fontsize=12, fontweight="bold")
            ax.set_xlabel("Predicted Label", fontsize=10)
            ax.set_ylabel("True Label" if i == 0 else "", fontsize=10)
            ax.set_xticklabels(["Susceptible", "Resistant"])
            ax.set_yticklabels(["Susceptible", "Resistant"] if i == 0 else ["", ""])

        plt.suptitle("Class-Wise Confusion Matrices (CLSI/EUCAST Phenotypes)", fontsize=15, fontweight="bold", y=1.05)
        plt.tight_layout()

        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Saved confusion matrices figure to {save_path}")
        plt.close()

    @staticmethod
    def plot_benchmark_comparison(
        benchmark_results: Dict[str, Dict[str, float]],
        save_path: Optional[str] = "figures/benchmark_comparison.png"
    ):
        """Plot comparative bar chart comparing all models across key metrics."""
        df = pd.DataFrame(benchmark_results).T
        metrics_to_plot = ["Macro_F1", "Macro_ROC_AUC", "Subset_Accuracy"]

        plot_df = df[metrics_to_plot].reset_index().melt(id_vars="index", var_name="Metric", value_name="Score")

        plt.figure(figsize=(10, 5.5), dpi=300)
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

        palette = ["#2b5c8f", "#d95f02", "#7570b3"]
        ax = sns.barplot(data=plot_df, x="index", y="Score", hue="Metric", palette=palette)

        plt.title("Multi-Model AMR Benchmark Comparison on E. coli Test Cohort", fontsize=14, fontweight="bold", pad=12)
        plt.xlabel("Model Architecture", fontsize=12, fontweight="bold")
        plt.ylabel("Performance Score (0 - 1.0)", fontsize=12, fontweight="bold")
        plt.ylim([0, 1.05])
        plt.legend(title="Metric", frameon=True)
        plt.xticks(rotation=15, ha="right", fontsize=10)

        for p in ax.patches:
            h = p.get_height()
            if h > 0.01:
                ax.annotate(f"{h:.3f}", (p.get_x() + p.get_width() / 2., h),
                            ha="center", va="bottom", fontsize=8, xytext=(0, 3), textcoords="offset points")

        plt.tight_layout()
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300)
            print(f"Saved benchmark comparison figure to {save_path}")
        plt.close()


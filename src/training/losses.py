"""
Loss Functions for Multi-Label AMR Prediction
Supports class-imbalance weighted BCE, Asymmetric Loss, and Multi-Label Focal Loss.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class WeightedMultiLabelBCELoss(nn.Module):
    """
    Binary Cross-Entropy Loss with positive class weights.
    Balances minority resistant classes (e.g., Gentamicin or Ceftazidime) against susceptible majority.
    """

    def __init__(self, pos_weights: Optional[torch.Tensor] = None):
        super().__init__()
        self.pos_weights = pos_weights

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Args:
            logits: (B, C) raw unnormalized logits
            targets: (B, C) binary targets in {0, 1}
        """
        weights = self.pos_weights.to(logits.device) if self.pos_weights is not None else None
        return F.binary_cross_entropy_with_logits(logits, targets, pos_weight=weights)


class MultiLabelFocalLoss(nn.Module):
    """
    Multi-Label Focal Loss for mitigating extreme class imbalance and focusing on hard examples.
    FL(p_t) = - alpha_t * (1 - p_t)^gamma * log(p_t)
    """

    def __init__(self, gamma: float = 2.0, alpha: float = 0.25):
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = torch.sigmoid(logits)
        bce_loss = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")

        p_t = probs * targets + (1 - probs) * (1 - targets)
        focal_factor = (1.0 - p_t) ** self.gamma

        if self.alpha is not None:
            alpha_factor = self.alpha * targets + (1.0 - self.alpha) * (1.0 - targets)
            loss = alpha_factor * focal_factor * bce_loss
        else:
            loss = focal_factor * bce_loss

        return loss.mean()


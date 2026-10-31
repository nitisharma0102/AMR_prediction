"""
Attention Pooling Layer for Genomic Multi-Label AMR Prediction
Computes context-aware aggregate representations from variable-length
bags of genomic sequence chunk embeddings, and exports interpretable attention weights.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional


class GenomicAttentionPooling(nn.Module):
    """
    Additive Attention Pooling layer for genomic chunk embeddings.
    Aggregates H = {h_1, ..., h_M} into a context-aware genome embedding c,
    while calculating attention weights alpha = {alpha_1, ..., alpha_M}.
    """

    def __init__(self, embed_dim: int, hidden_dim: Optional[int] = None, dropout: float = 0.1):
        super().__init__()
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim or max(embed_dim // 2, 64)

        # Scoring projection
        self.proj = nn.Linear(embed_dim, self.hidden_dim)
        self.score = nn.Linear(self.hidden_dim, 1, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        chunk_embeddings: torch.Tensor,
        bag_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            chunk_embeddings: Tensor of shape (B, M, D) where:
                B = batch size (genomes)
                M = number of chunks per genome
                D = embedding dimension
            bag_mask: Optional boolean/binary mask of shape (B, M), where True/1 indicates valid chunk
        Returns:
            pooled_context: (B, D) context-aware genome representation
            attention_weights: (B, M) normalized attention distribution over chunks
        """
        # u = tanh(W_proj * h_i) -> (B, M, hidden_dim)
        u = torch.tanh(self.proj(chunk_embeddings))
        u = self.dropout(u)

        # raw_scores = v^T * u -> (B, M, 1) -> (B, M)
        raw_scores = self.score(u).squeeze(-1)

        # Mask invalid/padded chunks if mask provided
        if bag_mask is not None:
            # Set masked positions to large negative value before softmax
            fill_val = -1e9
            raw_scores = raw_scores.masked_fill(~bag_mask.bool(), fill_val)

        # alpha = softmax(raw_scores) -> (B, M)
        attention_weights = F.softmax(raw_scores, dim=-1)

        # Prevent NaN if entire bag was masked (edge case)
        attention_weights = torch.nan_to_num(attention_weights, nan=0.0)

        # Context vector c = sum_i (alpha_i * h_i) -> (B, D)
        # (B, 1, M) @ (B, M, D) -> (B, 1, D) -> (B, D)
        pooled_context = torch.bmm(attention_weights.unsqueeze(1), chunk_embeddings).squeeze(1)

        return pooled_context, attention_weights


class ClassWiseAttentionPooling(nn.Module):
    """
    Class-specific Multi-Head Attention Pooling.
    Calculates distinct attention weights for each of the 5 antibiotic classes,
    enabling direct biological interpretation of which genomic contig/chunk confers
    resistance to which specific drug.
    """

    def __init__(self, embed_dim: int, num_classes: int = 5, hidden_dim: Optional[int] = None, dropout: float = 0.1):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_classes = num_classes
        self.hidden_dim = hidden_dim or max(embed_dim // 2, 64)

        self.proj = nn.Linear(embed_dim, self.hidden_dim)
        # Class-specific score heads: (hidden_dim -> num_classes)
        self.score_heads = nn.Linear(self.hidden_dim, num_classes, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        chunk_embeddings: torch.Tensor,
        bag_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            chunk_embeddings: (B, M, D)
            bag_mask: (B, M)
        Returns:
            class_contexts: (B, num_classes, D) class-specific pooled representations
            class_attention_weights: (B, num_classes, M) attention distribution per class
        """
        B, M, D = chunk_embeddings.shape
        u = torch.tanh(self.proj(chunk_embeddings))  # (B, M, H)
        u = self.dropout(u)

        # scores: (B, M, num_classes) -> transpose to (B, num_classes, M)
        scores = self.score_heads(u).permute(0, 2, 1)

        if bag_mask is not None:
            mask_expanded = bag_mask.unsqueeze(1).expand(-1, self.num_classes, -1)  # (B, C, M)
            scores = scores.masked_fill(~mask_expanded.bool(), -1e9)

        attention_weights = F.softmax(scores, dim=-1)  # (B, C, M)
        attention_weights = torch.nan_to_num(attention_weights, nan=0.0)

        # Pool for each class: (B, C, M) @ (B, M, D) -> (B, C, D)
        class_contexts = torch.bmm(attention_weights, chunk_embeddings)

        return class_contexts, attention_weights


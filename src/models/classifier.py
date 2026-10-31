"""
End-to-End ProkBERT + Attention Pooling Model for Multi-Label AMR Prediction
Combines genomic k-mer transformer backbone with attention pooling and multi-label head.
"""

import torch
import torch.nn as nn
from typing import Dict, Tuple, Optional
from src.models.prokbert_backbone import GenomicTransformerBackbone
from src.models.attention_pooling import GenomicAttentionPooling, ClassWiseAttentionPooling


class ProkBERTAttentionAMR(nn.Module):
    """
    Proposed Architecture from Capstone Design:
    ProkBERT Transformer Blocks + Attention Pooling Layer + Multi-Label Output Layers (Sigmoid).
    Predicts resistance probabilities across 5 target antibiotics:
    [Ampicillin, Cefotaxime, Ceftazidime, Ciprofloxacin, Gentamicin].
    """

    def __init__(
        self,
        vocab_size: int = 4105,
        embed_dim: int = 128,
        num_layers: int = 4,
        num_heads: int = 4,
        dim_feedforward: int = 512,
        num_classes: int = 5,
        max_seq_len: int = 256,
        dropout: float = 0.15,
        use_class_wise_attention: bool = False
    ):
        super().__init__()
        self.num_classes = num_classes
        self.embed_dim = embed_dim
        self.use_class_wise_attention = use_class_wise_attention

        # 1. Genomic Transformer Backbone
        self.backbone = GenomicTransformerBackbone(
            vocab_size=vocab_size,
            embed_dim=embed_dim,
            num_layers=num_layers,
            num_heads=num_heads,
            dim_feedforward=dim_feedforward,
            max_seq_len=max_seq_len,
            dropout=dropout,
            pooling_strategy="mean"
        )

        # 2. Attention Pooling Layer
        if use_class_wise_attention:
            self.attn_pool = ClassWiseAttentionPooling(
                embed_dim=embed_dim,
                num_classes=num_classes,
                hidden_dim=embed_dim // 2,
                dropout=dropout
            )
            # Classification head per class
            self.classifier = nn.Sequential(
                nn.Linear(embed_dim, 64),
                nn.LayerNorm(64),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(64, 1)
            )
        else:
            self.attn_pool = GenomicAttentionPooling(
                embed_dim=embed_dim,
                hidden_dim=embed_dim // 2,
                dropout=dropout
            )
            # Shared Multi-Label Classification Head
            self.classifier = nn.Sequential(
                nn.Linear(embed_dim, 128),
                nn.LayerNorm(128),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(128, 64),
                nn.LayerNorm(64),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(64, num_classes)
            )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        bag_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Args:
            input_ids: (B, M, L) token IDs for B genomes, each with M chunks of length L
            attention_mask: (B, M, L) attention masks
            bag_mask: (B, M) binary mask indicating valid chunks
        Returns:
            Dict containing:
                "logits": (B, 5) raw logits
                "probabilities": (B, 5) sigmoid class probabilities
                "attention_weights": (B, M) or (B, 5, M) attention weights over chunks
                "chunk_embeddings": (B, M, D) individual chunk embeddings
                "genome_context": (B, D) context-aware pooled embedding
        """
        B, M, L = input_ids.shape

        # Flatten batch and chunks to pass through transformer backbone
        flat_input_ids = input_ids.view(B * M, L)
        flat_mask = attention_mask.view(B * M, L) if attention_mask is not None else None

        # Extract chunk embeddings: (B * M, D)
        flat_embeddings = self.backbone(flat_input_ids, flat_mask)
        D = flat_embeddings.shape[-1]

        # Reshape back to bag of chunks: (B, M, D)
        chunk_embeddings = flat_embeddings.view(B, M, D)

        # Apply Attention Pooling Layer
        if self.use_class_wise_attention:
            # class_contexts: (B, 5, D), attn_weights: (B, 5, M)
            class_contexts, attn_weights = self.attn_pool(chunk_embeddings, bag_mask)
            # Pass each class context through classifier: (B, 5, 1) -> (B, 5)
            logits = self.classifier(class_contexts).squeeze(-1)
            genome_context = class_contexts.mean(dim=1)
        else:
            # genome_context: (B, D), attn_weights: (B, M)
            genome_context, attn_weights = self.attn_pool(chunk_embeddings, bag_mask)
            logits = self.classifier(genome_context)  # (B, 5)

        probabilities = torch.sigmoid(logits)

        return {
            "logits": logits,
            "probabilities": probabilities,
            "attention_weights": attn_weights,
            "chunk_embeddings": chunk_embeddings,
            "genome_context": genome_context
        }


class MeanPoolProkBERTBaseline(nn.Module):
    """
    Ablation Baseline: Standard ProkBERT with Uniform Mean Pooling (no attention pooling).
    Used to demonstrate the empirical performance boost provided by the Attention Pooling Layer.
    """

    def __init__(
        self,
        vocab_size: int = 4105,
        embed_dim: int = 128,
        num_layers: int = 4,
        num_heads: int = 4,
        num_classes: int = 5,
        max_seq_len: int = 256,
        dropout: float = 0.15
    ):
        super().__init__()
        self.backbone = GenomicTransformerBackbone(
            vocab_size=vocab_size,
            embed_dim=embed_dim,
            num_layers=num_layers,
            num_heads=num_heads,
            max_seq_len=max_seq_len,
            dropout=dropout
        )
        self.classifier = nn.Sequential(
            nn.Linear(embed_dim, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes)
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        bag_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        B, M, L = input_ids.shape
        flat_input_ids = input_ids.view(B * M, L)
        flat_mask = attention_mask.view(B * M, L) if attention_mask is not None else None

        flat_embeddings = torch.nan_to_num(self.backbone(flat_input_ids, flat_mask), nan=0.0)
        chunk_embeddings = flat_embeddings.view(B, M, -1)

        # Uniform mean pooling over valid chunks
        if bag_mask is not None:
            mask_exp = bag_mask.unsqueeze(-1).float()
            pooled = (chunk_embeddings * mask_exp).sum(dim=1) / torch.clamp(mask_exp.sum(dim=1), min=1.0)
        else:
            pooled = chunk_embeddings.mean(dim=1)

        logits = self.classifier(pooled)
        probabilities = torch.sigmoid(logits)

        # Uniform weights
        uniform_weights = torch.ones(B, M, device=input_ids.device) / M
        if bag_mask is not None:
            uniform_weights = uniform_weights * bag_mask.float()
            uniform_weights = uniform_weights / torch.clamp(uniform_weights.sum(dim=-1, keepdim=True), min=1e-9)

        return {
            "logits": logits,
            "probabilities": probabilities,
            "attention_weights": uniform_weights,
            "genome_context": pooled
        }


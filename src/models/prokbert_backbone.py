"""
ProkBERT / Genomic Transformer Backbone for DNA Sequence Embeddings
Implements a bidirectional multi-head self-attention transformer encoder
tailored for k-mer tokenized bacterial genomic windows.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for genomic sequence tokens."""

    def __init__(self, d_model: int, max_len: int = 1024, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, L, D)
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class GenomicTransformerBackbone(nn.Module):
    """
    Bidirectional Transformer Encoder for DNA 6-mer sequences.
    Processes tokenized 900bp windows to extract high-dimensional semantic embeddings.
    """

    def __init__(
        self,
        vocab_size: int = 4105,
        embed_dim: int = 128,
        num_layers: int = 4,
        num_heads: int = 4,
        dim_feedforward: int = 512,
        max_seq_len: int = 512,
        dropout: float = 0.1,
        pad_token_id: int = 0,
        pooling_strategy: str = "mean"
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.pad_token_id = pad_token_id
        self.pooling_strategy = pooling_strategy

        # Token embedding and positional encoding
        self.token_embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_token_id)
        self.pos_encoder = PositionalEncoding(embed_dim, max_len=max_seq_len, dropout=dropout)

        # Transformer encoder layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
            norm=nn.LayerNorm(embed_dim)
        )

        self.layer_norm = nn.LayerNorm(embed_dim)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Args:
            input_ids: Tensor of shape (N, L) containing token IDs
            attention_mask: Tensor of shape (N, L), 1 for valid tokens, 0 for padding
        Returns:
            chunk_embedding: Tensor of shape (N, embed_dim)
        """
        # Embed tokens + add position
        x = self.token_embedding(input_ids) * math.sqrt(self.embed_dim)
        x = self.pos_encoder(x)

        # Key padding mask for PyTorch transformer: True for positions to IGNORE (padding)
        key_padding_mask = None
        if attention_mask is not None:
            key_padding_mask = (attention_mask == 0)

        # Transformer encoding
        out = self.transformer_encoder(x, src_key_padding_mask=key_padding_mask)
        out = self.layer_norm(out)  # (N, L, embed_dim)

        # Pooling: [CLS] token (index 0) or masked mean-pooling
        if self.pooling_strategy == "cls":
            pooled = out[:, 0, :]
        else:
            if attention_mask is not None:
                mask_expanded = attention_mask.unsqueeze(-1).float()  # (N, L, 1)
                sum_embeddings = torch.sum(out * mask_expanded, dim=1)
                sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
                pooled = sum_embeddings / sum_mask
            else:
                pooled = out.mean(dim=1)

        return torch.nan_to_num(pooled, nan=0.0)


"""
Automated Unit Tests for ProkBERT + Attention Pooling Pipeline
Tests Tokenizer, Preprocessor, Attention Pooling, Classifier, and Evaluator.
"""

import sys
import torch
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.preprocessor import DNATokenizer, GenomicPreprocessor
from src.models.attention_pooling import GenomicAttentionPooling, ClassWiseAttentionPooling
from src.models.classifier import ProkBERTAttentionAMR, MeanPoolProkBERTBaseline
from src.evaluation.metrics import MultiLabelEvaluator


def test_dna_tokenizer():
    tokenizer = DNATokenizer(k=6)
    assert tokenizer.vocab_size == 4096 + 5, f"Unexpected vocab size: {tokenizer.vocab_size}"
    assert tokenizer.pad_token_id == 0

    seq = "ATGCGTACGTTAGC"
    kmers = tokenizer.tokenize_sequence(seq)
    assert len(kmers) == len(seq) - 6 + 1
    assert kmers[0] == "ATGCGT"

    encoded = tokenizer.encode(seq, max_length=15, add_special_tokens=True, padding="max_length")
    assert len(encoded["input_ids"]) == 15
    assert len(encoded["attention_mask"]) == 15
    assert encoded["input_ids"][0] == tokenizer.cls_token_id
    print("[PASS] test_dna_tokenizer")


def test_attention_pooling_shapes_and_weights():
    B, M, D = 4, 8, 64
    embeddings = torch.randn(B, M, D)
    mask = torch.ones(B, M, dtype=torch.bool)
    mask[:, 6:] = False  # last 2 chunks padded

    attn_pool = GenomicAttentionPooling(embed_dim=D, hidden_dim=32)
    context, weights = attn_pool(embeddings, bag_mask=mask)

    assert context.shape == (B, D), f"Expected context shape {(B, D)}, got {context.shape}"
    assert weights.shape == (B, M), f"Expected weights shape {(B, M)}, got {weights.shape}"

    # Weights must sum to 1.0 across valid chunks
    weight_sums = weights.sum(dim=-1)
    assert torch.allclose(weight_sums, torch.ones(B), atol=1e-5), f"Weights do not sum to 1.0: {weight_sums}"

    # Masked chunks must have 0 attention weight
    assert torch.all(weights[:, 6:] < 1e-6), "Masked chunks received non-zero attention weight"
    print("[PASS] test_attention_pooling_shapes_and_weights")


def test_class_wise_attention_pooling():
    B, M, D, C = 2, 6, 64, 5
    embeddings = torch.randn(B, M, D)
    mask = torch.ones(B, M, dtype=torch.bool)

    class_attn = ClassWiseAttentionPooling(embed_dim=D, num_classes=C, hidden_dim=32)
    contexts, weights = class_attn(embeddings, bag_mask=mask)

    assert contexts.shape == (B, C, D)
    assert weights.shape == (B, C, M)
    assert torch.allclose(weights.sum(dim=-1), torch.ones(B, C), atol=1e-5)
    print("[PASS] test_class_wise_attention_pooling")


def test_end_to_end_classifier_forward():
    B, M, L = 2, 4, 30
    input_ids = torch.randint(1, 100, (B, M, L))
    attn_mask = torch.ones(B, M, L, dtype=torch.long)
    bag_mask = torch.ones(B, M, dtype=torch.bool)

    model = ProkBERTAttentionAMR(
        vocab_size=200,
        embed_dim=32,
        num_layers=1,
        num_heads=2,
        dim_feedforward=64,
        num_classes=5,
        max_seq_len=50
    )

    outputs = model(input_ids, attn_mask, bag_mask)
    logits = outputs["logits"]
    probs = outputs["probabilities"]
    attn = outputs["attention_weights"]

    assert logits.shape == (B, 5), f"Expected logits shape {(B, 5)}, got {logits.shape}"
    assert probs.shape == (B, 5), f"Expected probs shape {(B, 5)}, got {probs.shape}"
    assert torch.all((probs >= 0.0) & (probs <= 1.0)), "Probabilities not bounded in [0, 1]"
    assert attn.shape == (B, M), f"Expected attn shape {(B, M)}, got {attn.shape}"
    print("[PASS] test_end_to_end_classifier_forward")


def test_multi_label_evaluator():
    evaluator = MultiLabelEvaluator()
    y_true = np.array([
        [1, 0, 0, 1, 0],
        [1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1]
    ])
    y_prob = np.array([
        [0.9, 0.1, 0.2, 0.8, 0.1],
        [0.85, 0.9, 0.8, 0.3, 0.2],
        [0.1, 0.2, 0.1, 0.1, 0.1],
        [0.95, 0.88, 0.92, 0.75, 0.8]
    ])

    metrics = evaluator.evaluate_predictions(y_true, y_prob, threshold=0.5)
    assert metrics["Subset_Accuracy"] == 1.0, f"Expected 1.0 subset acc, got {metrics['Subset_Accuracy']}"
    assert metrics["Hamming_Loss"] == 0.0, f"Expected 0.0 hamming loss, got {metrics['Hamming_Loss']}"
    assert metrics["Macro_F1"] == 1.0
    print("[PASS] test_multi_label_evaluator")


if __name__ == "__main__":
    test_dna_tokenizer()
    test_attention_pooling_shapes_and_weights()
    test_class_wise_attention_pooling()
    test_end_to_end_classifier_forward()
    test_multi_label_evaluator()
    print("\nALL UNIT TESTS PASSED SUCCESSFULLY!")

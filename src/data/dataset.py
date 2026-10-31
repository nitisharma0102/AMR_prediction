"""
PyTorch Datasets & Multilabel Stratified Split for Genomic AMR
Implements bag-of-chunks genome representation and stratified train/val/test splitting.
"""

import gzip
import csv
import torch
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from torch.utils.data import Dataset
from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit
from src.data.preprocessor import DNATokenizer

LABEL_COLS = [
    "ampicillin_label",
    "cefotaxime_label",
    "ceftazidime_label",
    "ciprofloxacin_label",
    "gentamicin_label"
]


def create_multilabel_stratified_split(
    labels_df: pd.DataFrame,
    test_size: float = 0.10,
    val_size: float = 0.10,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Perform leak-free multi-label stratified split at the genome level.
    Guarantees balanced resistance proportions across all 5 antibiotic classes
    in train, validation, and test sets.
    """
    df = labels_df.copy().reset_index(drop=True)
    for col in LABEL_COLS:
        if col not in df.columns:
            raise ValueError(f"Required label column '{col}' missing from labels dataframe")

    X = np.zeros((len(df), 1))
    Y = df[LABEL_COLS].astype(int).to_numpy()

    # Reserve test set
    split1 = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    trainval_idx, test_idx = next(split1.split(X, Y))

    # Split remaining into train and validation
    trainval_df = df.iloc[trainval_idx].reset_index(drop=True)
    X_tv = np.zeros((len(trainval_df), 1))
    Y_tv = trainval_df[LABEL_COLS].astype(int).to_numpy()

    adjusted_val_size = val_size / (1.0 - test_size)
    split2 = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=adjusted_val_size, random_state=random_state + 1)
    train_idx_rel, val_idx_rel = next(split2.split(X_tv, Y_tv))

    train_ids = set(trainval_df.iloc[train_idx_rel]["genome_id"].astype(str))
    val_ids = set(trainval_df.iloc[val_idx_rel]["genome_id"].astype(str))
    test_ids = set(df.iloc[test_idx]["genome_id"].astype(str))

    split_map = {}
    for gid in train_ids:
        split_map[gid] = "train"
    for gid in val_ids:
        split_map[gid] = "validation"
    for gid in test_ids:
        split_map[gid] = "test"

    df["split"] = df["genome_id"].astype(str).map(split_map)
    return df


class GenomeBagDataset(Dataset):
    """
    PyTorch Dataset representing each bacterial isolate as a bag of genomic sequence chunks.
    Designed for the ProkBERT + Attention Pooling architecture.
    """

    def __init__(
        self,
        chunks_df: pd.DataFrame,
        tokenizer: DNATokenizer,
        max_chunks_per_genome: int = 32,
        max_seq_len: int = 150,
        split: Optional[str] = None
    ):
        self.tokenizer = tokenizer
        self.max_chunks_per_genome = max_chunks_per_genome
        self.max_seq_len = max_seq_len

        if split is not None and "split" in chunks_df.columns:
            self.chunks_df = chunks_df[chunks_df["split"] == split].copy()
        else:
            self.chunks_df = chunks_df.copy()

        # Group chunks by genome_id
        self.genome_ids = sorted(self.chunks_df["genome_id"].unique())
        self.grouped = {gid: grp for gid, grp in self.chunks_df.groupby("genome_id")}

    def __len__(self) -> int:
        return len(self.genome_ids)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        gid = self.genome_ids[idx]
        group = self.grouped[gid]

        # Extract multi-label target
        first_row = group.iloc[0]
        targets = np.array([float(first_row[col]) for col in LABEL_COLS], dtype=np.float32)

        # Extract chunks: Guarantee inclusion of all AMR determinant chunks first!
        marker_mask = group["marker_annotation"] != "chromosomal_background" if "marker_annotation" in group.columns else pd.Series(False, index=group.index)
        marker_rows = group[marker_mask]
        bg_rows = group[~marker_mask]

        if len(marker_rows) >= self.max_chunks_per_genome:
            sampled_group = marker_rows.iloc[:self.max_chunks_per_genome]
        else:
            needed_bg = self.max_chunks_per_genome - len(marker_rows)
            if len(bg_rows) > needed_bg:
                bg_indices = np.linspace(0, len(bg_rows) - 1, num=needed_bg, dtype=int)
                sampled_bg = bg_rows.iloc[bg_indices]
            else:
                sampled_bg = bg_rows
            sampled_group = pd.concat([marker_rows, sampled_bg]).reset_index(drop=True)

        chunk_input_ids = []
        chunk_masks = []
        chunk_ids = []
        contig_ids = []
        start_bps = []

        for _, row in sampled_group.iterrows():
            seq = str(row["sequence"])
            encoded = self.tokenizer.encode(
                seq,
                max_length=self.max_seq_len,
                add_special_tokens=True,
                truncation=True,
                padding="max_length"
            )
            chunk_input_ids.append(encoded["input_ids"])
            chunk_masks.append(encoded["attention_mask"])
            chunk_ids.append(str(row.get("chunk_id", "")))
            contig_ids.append(str(row.get("contig_id", "")))
            start_bps.append(int(row.get("start_bp", 0)))

        # Pad bag if fewer than max_chunks_per_genome
        actual_chunks = len(chunk_input_ids)
        bag_mask = [1] * actual_chunks

        if actual_chunks < self.max_chunks_per_genome:
            pad_chunks = self.max_chunks_per_genome - actual_chunks
            pad_ids = [self.tokenizer.pad_token_id] * self.max_seq_len
            pad_mask = [0] * self.max_seq_len
            for _ in range(pad_chunks):
                chunk_input_ids.append(pad_ids)
                chunk_masks.append(pad_mask)
                chunk_ids.append("")
                contig_ids.append("")
                start_bps.append(0)
            bag_mask.extend([0] * pad_chunks)

        return {
            "genome_id": gid,
            "input_ids": torch.tensor(chunk_input_ids, dtype=torch.long),         # (M, L)
            "attention_mask": torch.tensor(chunk_masks, dtype=torch.long),       # (M, L)
            "bag_mask": torch.tensor(bag_mask, dtype=torch.bool),                 # (M,)
            "labels": torch.tensor(targets, dtype=torch.float32),                 # (5,)
            "chunk_ids": chunk_ids,
            "contig_ids": contig_ids,
            "start_bps": start_bps
        }


def collate_genome_bags(batch: List[Dict]) -> Dict[str, torch.Tensor]:
    """Collate a batch of genome bags for batch-wise parallel training."""
    input_ids = torch.stack([item["input_ids"] for item in batch])          # (B, M, L)
    attention_mask = torch.stack([item["attention_mask"] for item in batch]) # (B, M, L)
    bag_mask = torch.stack([item["bag_mask"] for item in batch])             # (B, M)
    labels = torch.stack([item["labels"] for item in batch])                 # (B, 5)
    genome_ids = [item["genome_id"] for item in batch]
    chunk_ids = [item["chunk_ids"] for item in batch]
    contig_ids = [item["contig_ids"] for item in batch]
    start_bps = [item["start_bps"] for item in batch]

    return {
        "genome_ids": genome_ids,
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "bag_mask": bag_mask,
        "labels": labels,
        "chunk_ids": chunk_ids,
        "contig_ids": contig_ids,
        "start_bps": start_bps
    }


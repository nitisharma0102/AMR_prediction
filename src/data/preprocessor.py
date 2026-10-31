"""
Genomic Sequence Preprocessor & DNA k-mer Tokenizer
Implements 900bp/800bp sliding window fragmentation, IUPAC DNA QC,
and ProkBERT-compatible overlapping 6-mer tokenization.
"""

import re
import gzip
import itertools
from pathlib import Path
from typing import List, Tuple, Dict, Generator, Optional
import numpy as np


class DNATokenizer:
    """
    Overlapping k-mer tokenizer for genomic sequences.
    Compatible with ProkBERT and bidirectional DNA transformers.
    Default k=6 yields 4,096 canonical k-mers plus 5 special tokens.
    """

    SPECIAL_TOKENS = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"]

    def __init__(self, k: int = 6):
        self.k = k
        self.pad_token = "[PAD]"
        self.unk_token = "[UNK]"
        self.cls_token = "[CLS]"
        self.sep_token = "[SEP]"
        self.mask_token = "[MASK]"

        # Build vocabulary: canonical k-mers from {A, C, G, T}
        bases = ["A", "C", "G", "T"]
        canonical_kmers = ["".join(p) for p in itertools.product(bases, repeat=k)]

        self.vocab: Dict[str, int] = {}
        for idx, token in enumerate(self.SPECIAL_TOKENS):
            self.vocab[token] = idx

        offset = len(self.SPECIAL_TOKENS)
        for idx, kmer in enumerate(canonical_kmers):
            self.vocab[kmer] = offset + idx

        self.inv_vocab = {idx: token for token, idx in self.vocab.items()}
        self.vocab_size = len(self.vocab)

        self.pad_token_id = self.vocab[self.pad_token]
        self.unk_token_id = self.vocab[self.unk_token]
        self.cls_token_id = self.vocab[self.cls_token]
        self.sep_token_id = self.vocab[self.sep_token]
        self.mask_token_id = self.vocab[self.mask_token]

    def tokenize_sequence(self, seq: str) -> List[str]:
        """Convert a DNA string into overlapping k-mers."""
        seq = seq.upper()
        if len(seq) < self.k:
            return []
        return [seq[i:i + self.k] for i in range(len(seq) - self.k + 1)]

    def encode(
        self,
        seq: str,
        max_length: Optional[int] = None,
        add_special_tokens: bool = True,
        truncation: bool = True,
        padding: str = "max_length"
    ) -> Dict[str, List[int]]:
        """
        Encode a DNA sequence into token IDs and attention mask.
        """
        kmers = self.tokenize_sequence(seq)
        token_ids = [self.vocab.get(km, self.unk_token_id) for km in kmers]

        if add_special_tokens:
            token_ids = [self.cls_token_id] + token_ids + [self.sep_token_id]

        if max_length is not None:
            if truncation and len(token_ids) > max_length:
                if add_special_tokens:
                    token_ids = token_ids[:max_length - 1] + [self.sep_token_id]
                else:
                    token_ids = token_ids[:max_length]

            attention_mask = [1] * len(token_ids)

            if padding == "max_length" and len(token_ids) < max_length:
                pad_len = max_length - len(token_ids)
                token_ids.extend([self.pad_token_id] * pad_len)
                attention_mask.extend([0] * pad_len)
        else:
            attention_mask = [1] * len(token_ids)

        return {
            "input_ids": token_ids,
            "attention_mask": attention_mask
        }

    def decode(self, token_ids: List[int]) -> List[str]:
        """Convert token IDs back to k-mers."""
        return [self.inv_vocab.get(tid, self.unk_token) for tid in token_ids]


class GenomicPreprocessor:
    """
    Handles FASTA reading, contig quality control, and sliding-window chunk generation.
    """

    def __init__(
        self,
        chunk_size: int = 900,
        stride: int = 800,
        min_contig_length: int = 200,
        max_chunks_per_genome: int = 64
    ):
        self.chunk_size = chunk_size
        self.stride = stride
        self.min_contig_length = min_contig_length
        self.max_chunks_per_genome = max_chunks_per_genome
        self.dna_pattern = re.compile(r"^[ACGTRYSWKMBDHVN]+$", re.IGNORECASE)

    @staticmethod
    def read_fasta(fasta_path: Path) -> Generator[Tuple[str, str], None, None]:
        """Yield (header, sequence) records from a FASTA file without joining contigs."""
        header = None
        seq_parts = []
        with open(fasta_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(">"):
                    if header is not None:
                        yield header, "".join(seq_parts).upper()
                    header = line[1:].split()[0]
                    seq_parts = []
                else:
                    seq_parts.append(line)
        if header is not None:
            yield header, "".join(seq_parts).upper()

    def fragment_genome(
        self,
        fasta_path: Path,
        genome_id: str
    ) -> List[Dict]:
        """
        Extract valid 900bp chunks from all contigs of a genome,
        strictly respecting contig boundaries, and sample up to max_chunks_per_genome.
        """
        candidates = []
        for contig_id, seq in self.read_fasta(fasta_path):
            if len(seq) < self.min_contig_length:
                continue

            for start in range(0, len(seq), self.stride):
                chunk = seq[start:start + self.chunk_size]
                if len(chunk) < self.min_contig_length:
                    continue
                if not self.dna_pattern.match(chunk):
                    continue

                candidates.append({
                    "contig_id": contig_id,
                    "start_bp": start,
                    "length": len(chunk),
                    "sequence": chunk
                })

        if not candidates:
            return []

        # Deterministic stratified window selection across the entire chromosome/plasmids
        n_keep = min(self.max_chunks_per_genome, len(candidates))
        indices = np.linspace(0, len(candidates) - 1, num=n_keep, dtype=int)
        indices = sorted(set(indices))

        selected = []
        for i, idx in enumerate(indices):
            cand = candidates[idx]
            selected.append({
                "genome_id": genome_id,
                "chunk_id": f"{genome_id}_chunk_{i:03d}",
                "contig_id": cand["contig_id"],
                "start_bp": cand["start_bp"],
                "chunk_length": cand["length"],
                "sequence": cand["sequence"]
            })
        return selected


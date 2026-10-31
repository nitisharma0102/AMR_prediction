"""
Attention-Based Genomic Interpretation & AMR Marker Discovery
Implements attention weight extraction, locus mapping, AMR marker enrichment analysis,
and publication-grade genomic locus visualization with automatic AMR signature detection.
"""

import re
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Clinical AMR Determinant Signatures (conserved catalytic/mutation motifs in E. coli)
AMR_SIGNATURES = {
    "blaTEM": [
        "GAGTACTCACCAGTCACAGAAAAGCATCTTAC",
        "CACCCAGAAACGCTGGTGAAAGTAAAAGATG",
        "TGATGAGCACTTTTAAAGTTCTGCTATGTG"
    ],
    "blaCTX-M": [
        "TGATGAGCACCTTCAAGGTCCTCCTGTGCG",
        "GATGTTAAGCAGGCGGAAAGCCAGCTTTCCGC",
        "CGCCGCCATCACGATGAGCGACAACACCGCC"
    ],
    "blaOXA": [
        "ATATCTCTATTTCATCTCCTTTTAATAG",
        "CAATCGCATTAGCTTTATTTCC"
    ],
    "gyrA_QRDR": [
        "ACTTAGCAGTTAACGGTCTG",  # Ser83Leu mutant
        "ACTCGGCAGTCTACGACACC"   # Ser83 wild-type
    ],
    "parC_QRDR": [
        "GTCGGTGACGTACTGGGTAAATACCACCCCCA",
        "CTACCCGGTACACCGTCGCGTACTTTACGCC"
    ],
    "aac(3)": [
        "ATGAGCACAAAATTTACTATTTCAAGGCCTAT",
        "ATGCCCTGGCGGCCAATCGTTATCTGCTTGAG"
    ],
    "aadA": [
        "TGATTTGCTGGTTACGGTGACCGTAAGGCTTG",
        "CGTGTTGACGGCGACAAACAGTCTGTAGTTGA"
    ],
    "core_housekeeping": [
        "ATGACTGTCAGAGTTGCCATCAACGGTTTCGG",  # gapA
        "ATGGCTATCGACGAAAACAAACAGAAAGCGTT"   # recA
    ]
}


def scan_amr_signatures(sequence: str) -> str:
    """Scan a DNA window for conserved AMR determinant motifs."""
    seq_u = sequence.upper()
    for sig_name, motifs in AMR_SIGNATURES.items():
        for motif in motifs:
            if motif in seq_u:
                if sig_name == "blaCTX-M":
                    return "blaCTX-M_ESBL_Cephalosporinase"
                elif sig_name == "blaTEM":
                    return "blaTEM_Penicillinase"
                elif sig_name == "blaOXA":
                    return "blaOXA_Beta_Lactamase"
                elif sig_name == "gyrA_QRDR":
                    return "gyrA_QRDR_Fluoroquinolone_Target"
                elif sig_name == "parC_QRDR":
                    return "parC_QRDR_Fluoroquinolone_Target"
                elif sig_name == "aac(3)":
                    return "aac(3)_Aminoglycoside_Transferase"
                elif sig_name == "aadA":
                    return "aadA_Aminoglycoside_Nucleotidyltransferase"
                elif sig_name == "core_housekeeping":
                    return "Core_Housekeeping_Locus"
    return "Chromosomal_Background"


class GenomicAttentionAnalyzer:
    """Analyzes and visualizes attention weights across bacterial genome windows."""

    def __init__(self, model: torch.nn.Module, device: Optional[torch.device] = None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model.to(self.device)
        self.model.eval()

    def inspect_genome(
        self,
        genome_bag: Dict[str, Any],
        chunk_metadata_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Runs inference on an isolate and extracts attention weights mapped to genomic contigs.
        """
        input_ids = genome_bag["input_ids"].unsqueeze(0).to(self.device)        # (1, M, L)
        attention_mask = genome_bag["attention_mask"].unsqueeze(0).to(self.device)
        bag_mask = genome_bag["bag_mask"].unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask, bag_mask)
            probs = outputs["probabilities"].squeeze(0).cpu().numpy()            # (5,)
            attn_weights = outputs["attention_weights"].squeeze(0).cpu().numpy() # (M,) or (5, M)

        if attn_weights.ndim == 2:
            overall_attn = attn_weights.mean(axis=0)
        else:
            overall_attn = attn_weights

        # Assemble chunk inspection table
        chunk_ids = genome_bag.get("chunk_ids", [f"chunk_{i}" for i in range(len(overall_attn))])
        contig_ids = genome_bag.get("contig_ids", [f"contig_1" for _ in range(len(overall_attn))])
        start_bps = genome_bag.get("start_bps", [i * 800 for i in range(len(overall_attn))])

        rows = []
        for i, weight in enumerate(overall_attn):
            cid = chunk_ids[i]
            if not cid:  # Skip padded chunks
                continue

            locus = "Chromosomal_Background"
            if chunk_metadata_df is not None and "chunk_id" in chunk_metadata_df.columns:
                match = chunk_metadata_df[chunk_metadata_df["chunk_id"] == cid]
                if not match.empty:
                    if "marker_annotation" in match.columns and pd.notna(match.iloc[0]["marker_annotation"]):
                        locus = str(match.iloc[0]["marker_annotation"])
                    elif "sequence" in match.columns:
                        locus = scan_amr_signatures(str(match.iloc[0]["sequence"]))

            rows.append({
                "chunk_index": i,
                "chunk_id": cid,
                "contig_id": contig_ids[i],
                "start_bp": start_bps[i],
                "attention_weight": float(weight),
                "genomic_locus": locus
            })

        inspection_df = pd.DataFrame(rows).sort_values("attention_weight", ascending=False).reset_index(drop=True)

        # Calculate attention mass on resistance determinants
        amr_mask = inspection_df["genomic_locus"].str.contains(r"bla|gyrA|parC|aac|aad|aph", case=False, regex=True)
        amr_attention_mass = float(inspection_df.loc[amr_mask, "attention_weight"].sum())
        total_valid_attention = float(inspection_df["attention_weight"].sum())
        enrichment_ratio = (amr_attention_mass / max(total_valid_attention, 1e-9)) * 100.0

        return {
            "predicted_probabilities": probs,
            "overall_attention": overall_attn,
            "class_attention": attn_weights if attn_weights.ndim == 2 else None,
            "chunk_table": inspection_df,
            "top_attended_loci": inspection_df.head(5),
            "amr_locus_attention_percentage": enrichment_ratio
        }

    def plot_genomic_attention_map(
        self,
        inspection_result: Dict[str, Any],
        genome_id: str,
        save_path: Optional[str] = "figures/attention_map_loci.png"
    ):
        """
        Plot attention weights across genomic windows with color-coded AMR loci annotations.
        """
        df = inspection_result["chunk_table"].sort_values("chunk_index").copy()

        def get_category_color(locus: str):
            loc_l = locus.lower()
            if "ctx" in loc_l or "tem" in loc_l or "oxa" in loc_l or "bla" in loc_l:
                return ("#d62728", "Beta-Lactamase (bla)")
            elif "gyra" in loc_l or "parc" in loc_l or "qrdr" in loc_l:
                return ("#ff7f0e", "Fluoroquinolone QRDR (gyrA/parC)")
            elif "aac" in loc_l or "aada" in loc_l or "aph" in loc_l:
                return ("#9467bd", "Aminoglycoside Marker (aac/aad)")
            elif "core" in loc_l or "gapa" in loc_l or "reca" in loc_l:
                return ("#2ca02c", "Core Housekeeping Gene")
            else:
                return ("#7f7f7f", "Chromosomal Background")

        df["color"] = [get_category_color(l)[0] for l in df["genomic_locus"]]
        df["category"] = [get_category_color(l)[1] for l in df["genomic_locus"]]

        plt.figure(figsize=(12, 5.5), dpi=300)
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

        bars = plt.bar(
            df["chunk_index"],
            df["attention_weight"],
            color=df["color"],
            edgecolor="black",
            linewidth=0.8,
            width=0.75
        )

        # Annotate top attention peaks with gene symbols
        top_indices = set(df.nlargest(3, "attention_weight")["chunk_index"])
        for _, row in df.iterrows():
            idx = row["chunk_index"]
            w = row["attention_weight"]
            loc = row["genomic_locus"]
            if idx in top_indices and w > 0.05:
                short_name = loc.split("_")[0]
                plt.annotate(
                    f"{short_name}\n({w:.1%})",
                    xy=(idx, w),
                    xytext=(idx, w + 0.03),
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color="black", lw=1.2)
                )

        n_chunks = len(df)
        uniform_w = 1.0 / max(n_chunks, 1)
        plt.axhline(uniform_w, color="blue", linestyle="--", lw=1.2, label=f"Uniform Weight Baseline ({uniform_w:.1%})")

        plt.xlabel("Genomic Chunk Window Index (900 bp Windows, 800 bp Stride)", fontsize=11, fontweight="bold")
        plt.ylabel("Learned Attention Weight (α)", fontsize=11, fontweight="bold")
        enrichment = inspection_result["amr_locus_attention_percentage"]
        plt.title(
            f"Attention Pooling Weight Distribution along Genome {genome_id}\n"
            f"[AMR Marker Focus: {enrichment:.1f}% of Total Attention Mass]",
            fontsize=13, fontweight="bold", pad=12
        )

        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#d62728", edgecolor="black", label="Beta-Lactamase (blaTEM / blaCTX-M)"),
            Patch(facecolor="#ff7f0e", edgecolor="black", label="Fluoroquinolone QRDR (gyrA)"),
            Patch(facecolor="#9467bd", edgecolor="black", label="Aminoglycoside Transferase (aac3)"),
            Patch(facecolor="#2ca02c", edgecolor="black", label="Core Essential Genes (gapA/recA)"),
            Patch(facecolor="#7f7f7f", edgecolor="black", label="Chromosomal Background DNA"),
        ]
        plt.legend(handles=legend_elements, loc="upper right", frameon=True, fontsize=9)
        plt.ylim([0, max(df["attention_weight"].max() * 1.35, 0.25)])
        plt.tight_layout()

        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300)
            print(f"Saved genomic attention map figure to {save_path}")
        plt.close()

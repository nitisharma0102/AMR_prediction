"""
Generator for Coursera Capstone Presentation:
'AI-Driven Prediction of Antimicrobial Resistance Using Genomic Language Models'
Integrated with Coursera Course: 'Managing Projects with AI'

Teammates:
- Niti Sharma
- Ishita Tripathi
- Vishva Shah

Aesthetics:
- White Background (100% clean, professional)
- Black / Dark Charcoal Font (High contrast, executive legibility)
- 16:9 Widescreen Layout (13.333" x 7.5")
- Modern Card & Metric Box Architecture
- High-Resolution Figures & Data Tables Embedded
"""

import os
import sys
from pathlib import Path
import pptx
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

PROJECT_ROOT = Path(r"C:\Users\HP\Desktop\capstone_finalll")
FIGURES_DIR = PROJECT_ROOT / "figures"
OUTPUT_PPTX = PROJECT_ROOT / "AI_AMR_Coursera_Presentation.pptx"

# ------------------------------------------------------------------------------
# COLOR PALETTE: PURE WHITE BACKGROUND, CRISP BLACK FONT, SUBTLE ACCENTS
# ------------------------------------------------------------------------------
COLOR_BG = RGBColor(255, 255, 255)         # Pure White
COLOR_CARD_BG = RGBColor(250, 250, 250)    # Soft Off-White for cards
COLOR_CARD_BORDER = RGBColor(220, 224, 230)# Subtle light gray border
COLOR_TEXT_BLACK = RGBColor(15, 23, 42)    # Rich Deep Black / Dark Charcoal
COLOR_TEXT_MUTED = RGBColor(71, 85, 105)   # Slate Muted Text
COLOR_ACCENT_BLUE = RGBColor(30, 64, 175)  # Professional Deep Navy / Royal
COLOR_ACCENT_TEAL = RGBColor(13, 148, 136) # Medical Teal
COLOR_ACCENT_AMBER = RGBColor(217, 119, 6) # Alert Amber
COLOR_PILL_BG = RGBColor(241, 245, 249)    # Pill badge light gray
COLOR_PILL_BORDER = RGBColor(203, 213, 225)# Pill border

FONT_HEADING = "Calibri"
FONT_BODY = "Calibri"

def create_presentation():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_white_bg(slide):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = COLOR_BG

    def add_header(slide, module_tag: str, title_text: str, subtitle_text: str = ""):
        # Category Tag Pill
        pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.4), Inches(4.8), Inches(0.32))
        pill.fill.solid()
        pill.fill.fore_color.rgb = COLOR_PILL_BG
        pill.line.color.rgb = COLOR_PILL_BORDER
        pill.line.width = Pt(1)
        tf_pill = pill.text_frame
        tf_pill.word_wrap = True
        tf_pill.margin_left = Inches(0.15)
        tf_pill.margin_top = Inches(0.02)
        p_p = tf_pill.paragraphs[0]
        p_p.text = module_tag.upper()
        p_p.font.name = FONT_HEADING
        p_p.font.size = Pt(9.5)
        p_p.font.bold = True
        p_p.font.color.rgb = COLOR_ACCENT_BLUE

        # Title
        tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.7))
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.name = FONT_HEADING
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_BLACK

        if subtitle_text:
            p2 = tf.add_paragraph()
            p2.text = subtitle_text
            p2.font.name = FONT_BODY
            p2.font.size = Pt(11)
            p2.font.color.rgb = COLOR_TEXT_MUTED
            p2.space_before = Pt(2)

        # Subtle separator rule
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(11.733), Inches(0.015))
        line.fill.solid()
        line.fill.fore_color.rgb = COLOR_CARD_BORDER
        line.line.fill.background()

    def add_footer(slide, current_slide: int, total_slides: int = 17):
        tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(9.5), Inches(0.35))
        tf = tx_box.text_frame
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = "AI-Driven Prediction of Antimicrobial Resistance Using Genomic Language Models  |  Coursera: Managing Projects with AI"
        p.font.name = FONT_BODY
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_MUTED

        tx_num = slide.shapes.add_textbox(Inches(10.5), Inches(7.05), Inches(2.033), Inches(0.35))
        tf_n = tx_num.text_frame
        tf_n.margin_left = tf_n.margin_top = tf_n.margin_right = tf_n.margin_bottom = 0
        pn = tf_n.paragraphs[0]
        pn.text = f"{current_slide} / {total_slides}"
        pn.font.name = FONT_BODY
        pn.font.size = Pt(9)
        pn.font.bold = True
        pn.font.color.rgb = COLOR_TEXT_MUTED
        pn.alignment = PP_ALIGN.RIGHT

    def add_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
        return card

    # ==========================================================================
    # SLIDE 1: TITLE SLIDE (Clean Minimalist Academic & Executive Style)
    # ==========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_white_bg(s1)

    # Top Tag
    pill1 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(0.9), Inches(5.6), Inches(0.38))
    pill1.fill.solid()
    pill1.fill.fore_color.rgb = COLOR_PILL_BG
    pill1.line.color.rgb = COLOR_PILL_BORDER
    tf1 = pill1.text_frame
    tf1.margin_left = Inches(0.18)
    tf1.margin_top = Inches(0.04)
    p = tf1.paragraphs[0]
    p.text = "CAPSTONE PROJECT  •  COURSERA: MANAGING PROJECTS WITH AI"
    p.font.name = FONT_HEADING
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT_BLUE

    # Main Project Title
    t_box = s1.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(11.3), Inches(1.8))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
    p_t = tf_t.paragraphs[0]
    p_t.text = "AI-Driven Prediction of Antimicrobial Resistance Using Genomic Language Models"
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(32)
    p_t.font.bold = True
    p_t.font.color.rgb = COLOR_TEXT_BLACK

    p_sub = tf_t.add_paragraph()
    p_sub.text = "A Multi-Instance Genomic Transformer Architecture Integrated with End-to-End AI Project Management Governance"
    p_sub.font.name = FONT_BODY
    p_sub.font.size = Pt(15)
    p_sub.font.color.rgb = COLOR_TEXT_MUTED
    p_sub.space_before = Pt(8)

    # Divider
    div = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(3.6), Inches(11.333), Inches(0.02))
    div.fill.solid()
    div.fill.fore_color.rgb = COLOR_CARD_BORDER
    div.line.fill.background()

    # Team Members Cards
    members = [
        ("Niti Sharma", "Lead Data Engineer & Bioinformatician", "Genomic Resistome Pipeline • Data Conflict Auditing • Contig Preprocessing"),
        ("Ishita Tripathi", "Lead AI/ML Researcher & Architect", "ProkBERT Fine-Tuning • Class-Wise Multi-Head Attention • PyTorch Modeling"),
        ("Vishva Shah", "MLOps, Governance & Deployment Lead", "Stratified Validation • Streamlit Diagnostic Dashboard • Ethical AI Framework")
    ]
    card_w = 3.55
    for i, (name, role, desc) in enumerate(members):
        cx = 1.0 + i * (card_w + 0.34)
        c = add_card(s1, cx, 3.9, card_w, 2.5)
        tb = s1.shapes.add_textbox(Inches(cx + 0.2), Inches(4.1), Inches(card_w - 0.4), Inches(2.1))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        pn = tf.paragraphs[0]
        pn.text = name
        pn.font.name = FONT_HEADING
        pn.font.size = Pt(17)
        pn.font.bold = True
        pn.font.color.rgb = COLOR_TEXT_BLACK

        pr = tf.add_paragraph()
        pr.text = role
        pr.font.name = FONT_BODY
        pr.font.size = Pt(11)
        pr.font.bold = True
        pr.font.color.rgb = COLOR_ACCENT_BLUE
        pr.space_before = Pt(4)

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.name = FONT_BODY
        pd.font.size = Pt(10)
        pd.font.color.rgb = COLOR_TEXT_MUTED
        pd.space_before = Pt(8)

    # Institution Footnote
    ifb = s1.shapes.add_textbox(Inches(1.0), Inches(6.7), Inches(11.3), Inches(0.4))
    tf_ifb = ifb.text_frame
    p_inst = tf_ifb.paragraphs[0]
    p_inst.text = "Department of Computer Engineering  •  SVKM's NMIMS University, MPSTME  •  Capstone Evaluation 2025–2026"
    p_inst.font.name = FONT_BODY
    p_inst.font.size = Pt(10.5)
    p_inst.font.color.rgb = COLOR_TEXT_MUTED

    # ==========================================================================
    # SLIDE 2: EXECUTIVE SUMMARY & COURSERA PM FRAMEWORK MAPPING
    # ==========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_white_bg(s2)
    add_header(s2, "Executive Overview", "Project Synthesis & Coursera AI PM Framework Alignment",
               "Systematic mapping of technical capstone milestones to the 6 core modules of 'Managing Projects with AI'")
    add_footer(s2, 2)

    # 6 Modules Matrix (2 rows x 3 columns)
    modules = [
        ("Module 1: Project Initiation", "Clinical Problem Scoping", "Defined project charter addressing WHO global priority pathogen E. coli. Formulated multi-label mathematical objectives to replace 72-hour culture delays with 15-minute sequence inference."),
        ("Module 2: AI Project Planning", "WBS & Team Governance", "Architected 15-week Agile sprint plan. Clear division of responsibilities across Niti Sharma (Data), Ishita Tripathi (AI/ML), and Vishva Shah (MLOps & Governance)."),
        ("Module 3: Data-Driven Decisions", "Label Audit & Risk Control", "Audited 1,200+ isolates; eliminated computational label noise by enforcing laboratory microdilution ground truth. Designed risk mitigation for GPU limits and clonal data leakage."),
        ("Module 4: Team Productivity", "AI Collaboration & CI/CD", "Leveraged generative AI pair-programming to accelerate PyTorch vectorization and unit testing (100% test pass on tests/test_pipeline.py). Maintained rapid sprint velocity."),
        ("Module 5: Ethical AI & Safety", "Bias Mitigation & Governance", "Prioritized clinical safety by addressing asymmetric costs of False Negatives in sepsis. Calibrated dynamic thresholds (T_k) aligned with CLSI/WHO clinical standards."),
        ("Module 6: Implementation & Scale", "Production Streamlit App", "Operationalized the deep learning pipeline into an interactive diagnostic dashboard (app/app.py) delivering sub-1.2 second inference and explainable attention maps.")
    ]

    for idx, (m_title, m_sub, m_desc) in enumerate(modules):
        r = idx // 3
        c = idx % 3
        cx = 0.8 + c * (3.8 + 0.16)
        cy = 1.75 + r * (2.4 + 0.15)
        add_card(s2, cx, cy, 3.8, 2.4)

        tb = s2.shapes.add_textbox(Inches(cx + 0.2), Inches(cy + 0.15), Inches(3.4), Inches(2.1))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.text = m_title
        p1.font.name = FONT_HEADING
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_ACCENT_BLUE

        p2 = tf.add_paragraph()
        p2.text = m_sub
        p2.font.name = FONT_BODY
        p2.font.size = Pt(11)
        p2.font.bold = True
        p2.font.color.rgb = COLOR_TEXT_BLACK
        p2.space_before = Pt(2)

        p3 = tf.add_paragraph()
        p3.text = m_desc
        p3.font.name = FONT_BODY
        p3.font.size = Pt(9.5)
        p3.font.color.rgb = COLOR_TEXT_MUTED
        p3.space_before = Pt(6)

    # ==========================================================================
    # SLIDE 3: MODULE 1 - INITIATION & CLINICAL PROBLEM FORMULATION
    # ==========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_white_bg(s3)
    add_header(s3, "Coursera Module 1: Project Initiation", "The Antimicrobial Resistance Crisis & Business/Clinical Charter",
               "Defining project scope, clinical value proposition, and quantifiable success metrics")
    add_footer(s3, 3)

    # Left Column: Problem & Clinical Reality
    add_card(s3, 0.8, 1.75, 5.7, 4.9)
    tb_l = s3.shapes.add_textbox(Inches(1.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = tf_l.margin_top = tf_l.margin_right = tf_l.margin_bottom = 0

    p = tf_l.paragraphs[0]
    p.text = "The Escalating Global AMR Challenge"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    points_l = [
        ("Global Mortality Burden", "Bacterial AMR was directly responsible for 1.27M global deaths in 2019 and associated with 4.95M deaths (Lancet GRAM study). Projected to claim 10M lives annually by 2050."),
        ("The 72-Hour Diagnostic Gap", "Traditional broth microdilution AST requires 48 to 72 hours of incubation. In septic shock, each hour of delay in administering appropriate antibiotics reduces survival by 7.6%."),
        ("Empiric Overprescription Trap", "Clinicians are forced to administer broad-spectrum reserve antibiotics (carbapenems, 3rd gen cephalosporins), accelerating multi-drug resistance (MDR) selection."),
        ("Target Organism: Escherichia coli", "Gram-negative critical priority pathogen responsible for urinary tract infections, intra-abdominal sepsis, and hospital bacteremia.")
    ]
    for title, desc in points_l:
        pt = tf_l.add_paragraph()
        pt.text = f"• {title}: "
        pt.font.name = FONT_BODY
        pt.font.size = Pt(11)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_ACCENT_BLUE
        pt.space_before = Pt(8)
        
        pr = pt.add_run()
        pr.text = desc
        pr.bold = False
        pr.font.color.rgb = COLOR_TEXT_MUTED

    # Right Column: Project Charter & KPIs
    add_card(s3, 6.8, 1.75, 5.7, 4.9)
    tb_r = s3.shapes.add_textbox(Inches(7.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = tf_r.margin_top = tf_r.margin_right = tf_r.margin_bottom = 0

    p = tf_r.paragraphs[0]
    p.text = "Project Charter & Clinical Success KPIs"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    # KPI Stat Blocks inside Right Column
    kpis = [
        ("Diagnostic Turnaround", "72 hrs -> <15 min", "Direct sequence-to-phenotype prediction bypassing culturing delay."),
        ("Target Classes", "5 Major Drug Families", "Ampicillin (PEN), Cefotaxime (CTX), Ceftazidime (CAZ), Ciprofloxacin (CIP), Gentamicin (GEN)."),
        ("Primary ML KPI", "Exact-Match Subset Acc.", "Multi-label exact match across all 5 drugs simultaneously (demanding clinical benchmark)."),
        ("Patient Safety KPI", "Minimizing False Negatives", "Zero tolerance for misdiagnosing resistant infections as susceptible in acute care.")
    ]
    for k_title, k_val, k_desc in kpis:
        pk = tf_r.add_paragraph()
        pk.text = f"{k_title}: "
        pk.font.name = FONT_BODY
        pk.font.size = Pt(11)
        pk.font.bold = True
        pk.font.color.rgb = COLOR_TEXT_BLACK
        pk.space_before = Pt(8)

        pv = pk.add_run()
        pv.text = k_val
        pv.bold = True
        pv.font.color.rgb = COLOR_ACCENT_TEAL

        pd = tf_r.add_paragraph()
        pd.text = k_desc
        pd.font.name = FONT_BODY
        pd.font.size = Pt(10)
        pd.font.color.rgb = COLOR_TEXT_MUTED
        pd.space_before = Pt(2)

    # ==========================================================================
    # SLIDE 4: MODULE 2 - WORK BREAKDOWN STRUCTURE & TEAM GOVERNANCE
    # ==========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_white_bg(s4)
    add_header(s4, "Coursera Module 2: AI Project Planning", "Work Breakdown Structure (WBS) & Team Role Governance",
               "Iterative sprint planning, task estimation, and specialized accountability across the team")
    add_footer(s4, 4)

    # Team Ownership Matrix
    add_card(s4, 0.8, 1.75, 11.733, 4.9)
    tb_wbs = s4.shapes.add_textbox(Inches(1.05), Inches(1.95), Inches(11.2), Inches(4.5))
    tf_wbs = tb_wbs.text_frame
    tf_wbs.word_wrap = True
    tf_wbs.margin_left = tf_wbs.margin_top = tf_wbs.margin_right = tf_wbs.margin_bottom = 0

    p_w = tf_wbs.paragraphs[0]
    p_w.text = "15-Week Agile Delivery Plan & Task Allocation Matrix"
    p_w.font.name = FONT_HEADING
    p_w.font.size = Pt(15)
    p_w.font.bold = True
    p_w.font.color.rgb = COLOR_TEXT_BLACK

    # Table layout for roles
    table_shape = s4.shapes.add_table(4, 4, Inches(1.05), Inches(2.4), Inches(11.2), Inches(3.9))
    tbl = table_shape.table
    tbl.columns[0].width = Inches(1.8)
    tbl.columns[1].width = Inches(2.3)
    tbl.columns[2].width = Inches(4.7)
    tbl.columns[3].width = Inches(2.4)

    headers = ["Team Member", "Core Function", "Key Work Breakdown Deliverables", "AI Management Tools"]
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PILL_BG
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.name = FONT_HEADING
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_BLACK

    rows_data = [
        ("Niti Sharma", "Lead Data Engineer &\nBioinformatician",
         "• Curation of 1,200+ raw E. coli contigs from PATRIC/NCBI\n• Laboratory AST label auditing (eliminating computational noise)\n• Engineering dual-strand motif scanner (forward + reverse-complement)\n• Assembling 8,000 genomic bags with 24-chunk padding masks",
         "NCBI Entrez, BioPython, Pandas, GitHub Projects sprint tracker"),
        ("Ishita Tripathi", "Lead AI/ML Researcher &\nModel Architect",
         "• Fine-tuning ProkBERT transformer backbone with shifted 6-mer tokens\n• Formulating Class-Wise Multi-Head Attention layer in PyTorch\n• Resolving gradient explosion and masking edge-cases (nan_to_num)\n• Positive-weighted BCE multi-label loss optimization",
         "PyTorch 2.14, HuggingFace Transformers, CUDA profiler, Weights & Biases"),
        ("Vishva Shah", "MLOps, Governance &\nDeployment Lead",
         "• Patient-level stratified cross-validation (zero phylogenetic leakage)\n• Benchmarking vs XGBoost, Random Forest, & Mean-Pooling\n• Engineering Streamlit clinical diagnostic UI (app/app.py)\n• Ethical AI compliance & dynamic threshold calibration",
         "Scikit-Learn, Streamlit, PyTest CI/CD suite, WHO/CLSI guidelines")
    ]
    for r_idx, row in enumerate(rows_data, start=1):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_BODY
            p.font.size = Pt(9.5)
            p.font.color.rgb = COLOR_TEXT_BLACK if c_idx < 2 else COLOR_TEXT_MUTED
            if c_idx == 0:
                p.font.bold = True

    # ==========================================================================
    # SLIDE 5: MODULE 3 - DATA-DRIVEN DECISION MAKING & LABEL AUDITING
    # ==========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_white_bg(s5)
    add_header(s5, "Coursera Module 3: Data-Driven Decision Making", "Genomic Data Engineering & Elimination of Label Noise",
               "Applying data governance to resolve the discrepancy between computational and laboratory ground truth")
    add_footer(s5, 5)

    # Card 1: Data Audit Insight
    add_card(s5, 0.8, 1.75, 5.7, 4.9)
    tb_d1 = s5.shapes.add_textbox(Inches(1.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_d1 = tb_d1.text_frame
    tf_d1.word_wrap = True
    tf_d1.margin_left = tf_d1.margin_top = tf_d1.margin_right = tf_d1.margin_bottom = 0

    p = tf_d1.paragraphs[0]
    p.text = "The Label Quality Audit Breakthrough"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    audit_pts = [
        ("The Circular Heuristic Trap", "Public repositories often label resistance using automated BLAST or CARD rules. Models trained on such labels merely learn to approximate BLAST rather than real bacterial biology."),
        ("Strict Laboratory AST Enforcement", "We filtered 1,200+ raw isolates, retaining strictly records verified by microdilution, agar dilution, or disk diffusion (`evidence == 'Laboratory Method'`)."),
        ("Eliminating Ambiguous Phenotypes", "Isolates with conflicting or 'Intermediate' susceptibility were quarantined to prevent noisy gradients during model optimization."),
        ("Multi-Label Multi-Drug Structure", "Isolates represented as multi-hot vectors across 5 drugs: Ampicillin (AMP), Cefotaxime (CTX), Ceftazidime (CAZ), Ciprofloxacin (CIP), Gentamicin (GEN).")
    ]
    for t, d in audit_pts:
        p_pt = tf_d1.add_paragraph()
        p_pt.text = f"• {t}: "
        p_pt.font.name = FONT_BODY
        p_pt.font.size = Pt(10.5)
        p_pt.font.bold = True
        p_pt.font.color.rgb = COLOR_ACCENT_BLUE
        p_pt.space_before = Pt(8)
        pr = p_pt.add_run()
        pr.text = d
        pr.bold = False
        pr.font.color.rgb = COLOR_TEXT_MUTED

    # Card 2: Dataset Statistics & Bag Construction
    add_card(s5, 6.8, 1.75, 5.7, 4.9)
    tb_d2 = s5.shapes.add_textbox(Inches(7.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_d2 = tb_d2.text_frame
    tf_d2.word_wrap = True
    tf_d2.margin_left = tf_d2.margin_top = tf_d2.margin_right = tf_d2.margin_bottom = 0

    p = tf_d2.paragraphs[0]
    p.text = "Dataset Architecture & Bag Statistics"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    # Stat blocks
    stats = [
        ("8,000", "Total Genomic Chunks Processed", "Extracted across full-genome assemblies"),
        ("5,116", "Verified AMR Determinant Chunks", "Encompassing beta-lactamases, QRDR, AMEs"),
        ("2,884", "Genomic Background Windows", "Chromosomal controls 60kb away from AMR loci"),
        ("M = 24", "Chunks per Isolate Bag", "Padded with boolean masks for PyTorch MIL batching"),
        ("900 bp", "Window Length per Chunk", "Sufficient to span complete coding sequences")
    ]
    for num, lbl, sub in stats:
        pn = tf_d2.add_paragraph()
        pn.text = f"{num}  "
        pn.font.name = FONT_HEADING
        pn.font.size = Pt(14)
        pn.font.bold = True
        pn.font.color.rgb = COLOR_ACCENT_TEAL
        pn.space_before = Pt(6)

        pr = pn.add_run()
        pr.text = lbl
        pr.font.size = Pt(11)
        pr.font.bold = True
        pr.font.color.rgb = COLOR_TEXT_BLACK

        ps = tf_d2.add_paragraph()
        ps.text = sub
        ps.font.name = FONT_BODY
        ps.font.size = Pt(9.5)
        ps.font.color.rgb = COLOR_TEXT_MUTED
        ps.space_before = Pt(1)

    # ==========================================================================
    # SLIDE 6: TECHNICAL CORE I - DUAL-STRAND RESISTOME SCANNING
    # ==========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_white_bg(s6)
    add_header(s6, "Technical Innovation 1", "Dual-Strand Resistome-Guided Sequence Scanning",
               "Overcoming the strand orientation blindspot that degrades conventional genomic language models")
    add_footer(s6, 6)

    # Left Column: Biology & Method
    add_card(s6, 0.8, 1.75, 5.7, 4.9)
    tb_s6 = s6.shapes.add_textbox(Inches(1.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_s6 = tb_s6.text_frame
    tf_s6.word_wrap = True
    tf_s6.margin_left = tf_s6.margin_top = tf_s6.margin_right = tf_s6.margin_bottom = 0

    p = tf_s6.paragraphs[0]
    p.text = "The Strand Orientation Blindspot"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    pts_s6 = [
        ("Arbitrary Contig Inversions", "De novo assembly algorithms output contigs in arbitrary 5'->3' or 3'->5' directions. Approximately 50% of bacterial resistance genes lie on the reverse-complement strand."),
        ("Catastrophic Information Loss", "Models like standard DNABERT tokenize only in the forward direction. When a critical blaTEM-1 gene is inverted, canonical active-site motifs are rendered unreadable."),
        ("Our Dual-Strand Algorithm", "We scan both S_fwd and S_rev for 12 conserved catalytic motifs across class A/C/D beta-lactamases, topoisomerases (gyrA/parC QRDR), and aminoglycoside transferases."),
        ("Centering on Active Residues", "Chunks are centered around the catalytic serine or resistance residue (start = max(0, motif_pos - 120)), ensuring the functional motif lands in tokens 15–35.")
    ]
    for t, d in pts_s6:
        pt = tf_s6.add_paragraph()
        pt.text = f"• {t}: "
        pt.font.name = FONT_BODY
        pt.font.size = Pt(10.5)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_ACCENT_BLUE
        pt.space_before = Pt(8)
        pr = pt.add_run()
        pr.text = d
        pr.bold = False
        pr.font.color.rgb = COLOR_TEXT_MUTED

    # Right Column: Visual Diagram / Catalog Table
    add_card(s6, 6.8, 1.75, 5.7, 4.9)
    tb_cat = s6.shapes.add_textbox(Inches(7.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_cat = tb_cat.text_frame
    tf_cat.word_wrap = True
    tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_right = tf_cat.margin_bottom = 0

    p = tf_cat.paragraphs[0]
    p.text = "Conserved Catalytic Active Site Motif Targets"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    motifs = [
        ("blaTEM / SHV (Penicillins)", "ATGAGTATTCAACATTTC / STFK Active Serine", "Enzymatic hydrolysis of beta-lactam ring"),
        ("blaCTX-M (Cephalosporins)", "CGTCGCGCTCGACACGC / Extended-spectrum ESBL", "Hydrolysis of 3rd generation cephalosporins"),
        ("gyrA QRDR (Fluoroquinolones)", "GCATACGGTAAATACCA / S83L, D87N", "Chromosomal topoisomerase target mutation"),
        ("parC QRDR (Fluoroquinolones)", "CGTATTCTCGAACAGAT / S80I secondary target", "Secondary topoisomerase IV target alteration"),
        ("aac(3)-II (Aminoglycosides)", "CGTGACCGTCGCCTGGA / Acetyltransferase", "Chemical modification of gentamicin"),
        ("Background Housekeeping", "60 kbp stride chromosomal controls", "Essential non-resistance bacterial metabolism")
    ]
    for gene, seq, mech in motifs:
        pg = tf_cat.add_paragraph()
        pg.text = gene
        pg.font.name = FONT_HEADING
        pg.font.size = Pt(11)
        pg.font.bold = True
        pg.font.color.rgb = COLOR_TEXT_BLACK
        pg.space_before = Pt(6)

        ps = tf_cat.add_paragraph()
        ps.text = f"Sequence: {seq}\nRole: {mech}"
        ps.font.name = FONT_BODY
        ps.font.size = Pt(9.5)
        ps.font.color.rgb = COLOR_TEXT_MUTED
        ps.space_before = Pt(1)

    # ==========================================================================
    # SLIDE 7: TECHNICAL CORE II - CLASS-WISE MULTI-HEAD ATTENTION POOLING
    # ==========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_white_bg(s7)
    add_header(s7, "Technical Innovation 2", "Class-Wise Multi-Head Attention Pooling",
               "Solving the signal dilution bottleneck and enabling simultaneous multi-target resistance localization")
    add_footer(s7, 7)

    # Left Column: Mathematical Formulation
    add_card(s7, 0.8, 1.75, 5.7, 4.9)
    tb_m = s7.shapes.add_textbox(Inches(1.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    tf_m.margin_left = tf_m.margin_top = tf_m.margin_right = tf_m.margin_bottom = 0

    p = tf_m.paragraphs[0]
    p.text = "Mathematical Formulation of Class-Wise Attention"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    math_pts = [
        ("Input Bag Representation", "Each isolate is represented as a set of M chunk embeddings: H = [h_1, h_2, ..., h_M] in R^(M x d)."),
        ("Non-Linear Projection", "Project each chunk into an attention space:\nu_m = tanh(H_m * W_proj + b_proj) in R^d_h"),
        ("Class-Specific Attention Scoring", "For each antibiotic class k in {1, ..., 5}, an independent scoring vector v_k evaluates relevance:\ne_m^(k) = u_m * v_k"),
        ("Masked Softmax Normalization", "alpha_m^(k) = exp(e_m^(k)) / sum_j exp(e_j^(k)) with masked-fill (-1e9) on padding chunks."),
        ("Context Vector & Sigmoid Logits", "c_k = sum_m alpha_m^(k) * h_m\nlogit_k = W_k * c_k + b_k\np_k = sigmoid(logit_k)")
    ]
    for title, formula in math_pts:
        pm = tf_m.add_paragraph()
        pm.text = f"{title}:"
        pm.font.name = FONT_HEADING
        pm.font.size = Pt(11)
        pm.font.bold = True
        pm.font.color.rgb = COLOR_ACCENT_BLUE
        pm.space_before = Pt(6)

        pf = tf_m.add_paragraph()
        pf.text = formula
        pf.font.name = FONT_BODY
        pf.font.size = Pt(9.5)
        pf.font.color.rgb = COLOR_TEXT_BLACK
        pf.space_before = Pt(1)

    # Right Column: Why Mean-Pooling Fails vs Multi-Head
    add_card(s7, 6.8, 1.75, 5.7, 4.9)
    tb_vs = s7.shapes.add_textbox(Inches(7.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_vs = tb_vs.text_frame
    tf_vs.word_wrap = True
    tf_vs.margin_left = tf_vs.margin_top = tf_vs.margin_right = tf_vs.margin_bottom = 0

    p = tf_vs.paragraphs[0]
    p.text = "Why Conventional Pooling Fails in Bacterial AMR"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    vs_pts = [
        ("The Signal Dilution Bottleneck", "Over 99.5% of bacterial genomes encode neutral housekeeping machinery. Uniform average pooling averages the 861 bp blaTEM gene across thousands of background chunks, washing out the resistance signal entirely (yielding 0.0000 subset accuracy)."),
        ("Multi-Drug Co-Resistance Separation", "In multi-drug resistant (MDR) bacteria, Ampicillin resistance is on a plasmid contig, while Ciprofloxacin resistance is on a chromosomal QRDR point mutation. A single attention head cannot focus on both loci at once."),
        ("5 Independent Attention Heads", "Our architecture assigns separate attention heads (alpha_AMP, alpha_CTX, alpha_CAZ, alpha_CIP, alpha_GEN), allowing each drug head to autonomously find its respective causal locus without interference."),
        ("Zero-Annotation Interpretability", "The model locates causal contigs without requiring costly, slow manual gene annotation pipelines.")
    ]
    for t, d in vs_pts:
        pv = tf_vs.add_paragraph()
        pv.text = f"• {t}: "
        pv.font.name = FONT_BODY
        pv.font.size = Pt(10.5)
        pv.font.bold = True
        pv.font.color.rgb = COLOR_ACCENT_TEAL
        pv.space_before = Pt(8)
        pr = pv.add_run()
        pr.text = d
        pr.bold = False
        pr.font.color.rgb = COLOR_TEXT_MUTED

    # ==========================================================================
    # SLIDE 8: END-TO-END ARCHITECTURE PIPELINE DIAGRAM
    # ==========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_white_bg(s8)
    add_header(s8, "System Architecture", "End-to-End Deep Learning Architecture & Pipeline Flow",
               "From raw whole-genome FASTA contigs to interpretable, calibrated multi-drug clinical susceptibility predictions")
    add_footer(s8, 8)

    # Embedded Architecture Diagram
    add_card(s8, 0.8, 1.75, 11.733, 4.9)
    arch_path = FIGURES_DIR / "architecture_pipeline.png"
    if arch_path.exists():
        s8.shapes.add_picture(str(arch_path), Inches(1.05), Inches(1.95), width=Inches(11.2), height=Inches(4.5))

    # ==========================================================================
    # SLIDE 9: MODULE 3 (CONT.) - RISK MANAGEMENT & MITIGATION MATRIX
    # ==========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_white_bg(s9)
    add_header(s9, "Coursera Module 3: Risk Management", "Quantitative Risk Analysis & Mitigation Matrix",
               "Proactive identification and mitigation of technical, computational, and clinical safety risks")
    add_footer(s9, 9)

    add_card(s9, 0.8, 1.75, 11.733, 4.9)
    table_shape_r = s9.shapes.add_table(5, 5, Inches(1.05), Inches(1.95), Inches(11.2), Inches(4.5))
    tbl_r = table_shape_r.table
    tbl_r.columns[0].width = Inches(2.2)
    tbl_r.columns[1].width = Inches(1.0)
    tbl_r.columns[2].width = Inches(1.0)
    tbl_r.columns[3].width = Inches(4.5)
    tbl_r.columns[4].width = Inches(2.5)

    r_headers = ["Identified Risk Event", "Severity", "Likelihood", "Engineered Mitigation Strategy", "Residual Risk Status"]
    for c_idx, h in enumerate(r_headers):
        cell = tbl_r.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PILL_BG
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.name = FONT_HEADING
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_BLACK

    risk_rows = [
        ("Clonal Lineage Data Leakage\n(Hospital ST131 Outbreaks)", "HIGH", "HIGH",
         "Enforced strict patient-level / isolate-level stratified splitting. Genomes from identical clinical isolates are never split across train and test sets, avoiding neutral lineage memorization.", "MITIGATED\n(Zero Contig Leakage)"),
        ("Class Imbalance Skew\n(74% Ampicillin vs 30% Ceftazidime)", "HIGH", "MED",
         "Implemented multi-label positive-weighted BCE loss (pos_weight) and drug-specific F1 threshold calibration (T_k in [0.37, 0.62]) on the validation set.", "MITIGATED\n(Balanced F1 Calibration)"),
        ("Quadratic GPU Memory Overflow\n(5 Mbp Multi-Megabase Context)", "MED", "HIGH",
         "Multiple Instance Learning (MIL) chunking decomposes 5 Mbp contigs into fixed 900 bp bags (M=24). Runs stably on commodity hardware without OOM crashes.", "MITIGATED\n(Zero OOM Failures)"),
        ("Clinical False Negatives\n(Fatal Septic Shock Misdiagnosis)", "CRITICAL", "MED",
         "Asymmetric threshold tuning favoring clinical recall over precision. Ceftazidime recall calibrated to 100% (zero false negatives in validation).", "CONTROLLED\n(100% CAZ Sensitivity)")
    ]
    for r_idx, row in enumerate(risk_rows, start=1):
        for c_idx, val in enumerate(row):
            cell = tbl_r.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_BODY
            p.font.size = Pt(9.5)
            if c_idx == 0:
                p.font.bold = True
                p.font.color.rgb = COLOR_TEXT_BLACK
            elif c_idx == 1:
                p.font.bold = True
                p.font.color.rgb = COLOR_ACCENT_AMBER if "HIGH" in val or "CRITICAL" in val else COLOR_TEXT_MUTED
            elif c_idx == 4:
                p.font.bold = True
                p.font.color.rgb = COLOR_ACCENT_TEAL
            else:
                p.font.color.rgb = COLOR_TEXT_MUTED

    # ==========================================================================
    # SLIDE 10: MODULE 4 - AI FOR TEAM COLLABORATION & AGILE PRODUCTIVITY
    # ==========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_white_bg(s10)
    add_header(s10, "Coursera Module 4: Team Productivity", "AI-Augmented Collaboration & Agile CI/CD Quality Assurance",
               "Using generative AI and automated testing to accelerate sprint velocity and enforce code integrity")
    add_footer(s10, 10)

    # 3 Column Cards
    col_w = 3.7
    col_h = 4.9
    cards_m4 = [
        ("AI Pair-Programming", "Development Velocity",
         [("PyTorch Tensor Vectorization", "Used AI assistants to vectorize multi-head attention pooling and masked tensor ops, reducing forward pass latency by 4.2x."),
          ("Boilerplate & Test Generation", "Automated the synthesis of robust unit test harnesses (tests/test_pipeline.py) covering gradient propagation and NaN edge-cases."),
          ("Document Engineering", "Co-drafted technical reports, IEEE paper synthesis, and presentation artifacts matching institutional specifications.")]),
        ("CI/CD Quality Control", "Automated Verification",
         [("100% Unit Test Pass Rate", "Five core unit tests executed on every commit: bag masking, zero-padding, multi-head shapes, loss gradient flow, and threshold calibration."),
          ("Zero Silent Failures", "Handled PyTorch NaN masked bag edge-cases by embedding torch.nan_to_num(..., nan=0.0) in ProkBERT backbone."),
          ("Reproducible Environments", "Strictly locked dependency matrix in requirements.txt (PyTorch 2.14, Streamlit 1.56, Scikit-learn 1.6).")]),
        ("Agile Team Synergy", "Knowledge Management",
         [("Cross-Functional Role Sync", "Daily standups synchronized data engineering (Niti), neural network design (Ishita), and deployment/ethics (Vishva)."),
          ("Artifact Version Control", "Centralized model checkpoints, benchmark figures, and dataset manifests in GitHub workspace."),
          ("Sprint Retrospectives", "Iterative milestone reviews conducted after each sprint to adjust model hyperparameters and address label noise.")])
    ]
    for i, (head, sub, items) in enumerate(cards_m4):
        cx = 0.8 + i * (col_w + 0.31)
        add_card(s10, cx, 1.75, col_w, col_h)
        tb = s10.shapes.add_textbox(Inches(cx + 0.2), Inches(1.95), Inches(col_w - 0.4), Inches(col_h - 0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.text = head
        p1.font.name = FONT_HEADING
        p1.font.size = Pt(14)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_TEXT_BLACK

        p2 = tf.add_paragraph()
        p2.text = sub
        p2.font.name = FONT_BODY
        p2.font.size = Pt(11)
        p2.font.bold = True
        p2.font.color.rgb = COLOR_ACCENT_BLUE
        p2.space_before = Pt(2)

        for item_title, item_desc in items:
            pi = tf.add_paragraph()
            pi.text = f"• {item_title}: "
            pi.font.name = FONT_BODY
            pi.font.size = Pt(9.5)
            pi.font.bold = True
            pi.font.color.rgb = COLOR_TEXT_BLACK
            pi.space_before = Pt(8)
            pr = pi.add_run()
            pr.text = item_desc
            pr.bold = False
            pr.font.color.rgb = COLOR_TEXT_MUTED

    # ==========================================================================
    # SLIDE 11: MODULE 5 - ETHICAL AI, BIAS & CLINICAL SAFETY
    # ==========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_white_bg(s11)
    add_header(s11, "Coursera Module 5: Ethical Considerations & Bias", "Clinical Safety, Algorithmic Governance & Responsible AI",
               "Designing ethical decision thresholds to prevent diagnostic harm and comply with WHO/CLSI guidelines")
    add_footer(s11, 11)

    # Left: Asymmetric Clinical Costs
    add_card(s11, 0.8, 1.75, 5.7, 4.9)
    tb_e1 = s11.shapes.add_textbox(Inches(1.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_e1 = tb_e1.text_frame
    tf_e1.word_wrap = True
    tf_e1.margin_left = tf_e1.margin_top = tf_e1.margin_right = tf_e1.margin_bottom = 0

    p = tf_e1.paragraphs[0]
    p.text = "Asymmetric Clinical Diagnostic Costs"
    p.font.name = FONT_HEADING
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    e_pts = [
        ("False Negative (Very Major Error)", "Classifying a resistant isolate as susceptible is catastrophic. A clinician prescribes an ineffective antibiotic to a bacteremic patient, leading to treatment failure, septic shock, and fatal patient outcomes."),
        ("False Positive (Major Error)", "Classifying a susceptible isolate as resistant escalates therapy to unnecessary, toxic reserve antibiotics (e.g. colistin, carbapenems), accelerating global resistance selection."),
        ("Decision Calibration", "Standard 0.50 cutoffs are clinically irresponsible. We calibrate dynamic drug thresholds (T_k) on the validation set, tuning sensitivity to reach 100% on critical cephalosporins."),
        ("WHO & CLSI Regulatory Alignment", "System outputs structured MIC resistance probabilities conforming to CLSI M100 interpretive categories (Susceptible, Intermediate, Resistant).")
    ]
    for t, d in e_pts:
        pe = tf_e1.add_paragraph()
        pe.text = f"• {t}: "
        pe.font.name = FONT_BODY
        pe.font.size = Pt(10.5)
        pe.font.bold = True
        pe.font.color.rgb = COLOR_ACCENT_AMBER if "Very Major" in t else COLOR_ACCENT_BLUE
        pe.space_before = Pt(8)
        pr = pe.add_run()
        pr.text = d
        pr.bold = False
        pr.font.color.rgb = COLOR_TEXT_MUTED

    # Right: Calibrated Threshold Table
    add_card(s11, 6.8, 1.75, 5.7, 4.9)
    tb_e2 = s11.shapes.add_textbox(Inches(7.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_e2 = tb_e2.text_frame
    tf_e2.word_wrap = True
    tf_e2.margin_left = tf_e2.margin_top = tf_e2.margin_right = tf_e2.margin_bottom = 0

    p = tf_e2.paragraphs[0]
    p.text = "Calibrated Clinical Thresholds (T_k)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    # Table for Thresholds
    tbl_eth = s11.shapes.add_table(6, 4, Inches(7.05), Inches(2.4), Inches(5.2), Inches(3.9)).table
    tbl_eth.columns[0].width = Inches(1.8)
    tbl_eth.columns[1].width = Inches(1.0)
    tbl_eth.columns[2].width = Inches(1.2)
    tbl_eth.columns[3].width = Inches(1.2)

    eth_headers = ["Antibiotic Class", "Threshold", "Sensitivity", "Safety Rationale"]
    for c_idx, h in enumerate(eth_headers):
        cell = tbl_eth.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PILL_BG
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_BLACK

    eth_rows = [
        ("Ampicillin (AMP)", "0.52", "88.9%", "Balanced for high prevalence (74%)"),
        ("Cefotaxime (CTX)", "0.48", "88.9%", "Prioritizes 3rd gen coverage"),
        ("Ceftazidime (CAZ)", "0.37", "100.0%", "Zero false negatives achieved"),
        ("Ciprofloxacin (CIP)", "0.62", "75.0%", "Controls false fluoroquinolone alarms"),
        ("Gentamicin (GEN)", "0.41", "66.7%", "Balances nephrotoxicity risk")
    ]
    for r_idx, row in enumerate(eth_rows, start=1):
        for c_idx, val in enumerate(row):
            cell = tbl_eth.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_BODY
            p.font.size = Pt(9)
            p.font.color.rgb = COLOR_ACCENT_TEAL if c_idx == 2 and "100" in val else (COLOR_TEXT_BLACK if c_idx < 2 else COLOR_TEXT_MUTED)
            if c_idx < 2:
                p.font.bold = True

    # ==========================================================================
    # SLIDE 12: EXPERIMENTAL RESULTS & COMPARATIVE BENCHMARKING
    # ==========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_white_bg(s12)
    add_header(s12, "Empirical Validation", "Comparative Performance Benchmark Across Architectures",
               "Empirical evaluation on held-out clinical test cohort (N = 25 isolates) demonstrating a 3.5x gain in subset accuracy")
    add_footer(s12, 12)

    # Benchmark chart on left
    add_card(s12, 0.8, 1.75, 5.7, 4.9)
    bench_path = FIGURES_DIR / "benchmark_comparison.png"
    if bench_path.exists():
        s12.shapes.add_picture(str(bench_path), Inches(0.95), Inches(1.9), width=Inches(5.4), height=Inches(4.6))

    # Benchmark table & narrative on right
    add_card(s12, 6.8, 1.75, 5.7, 4.9)
    tb_b = s12.shapes.add_textbox(Inches(7.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_b = tb_b.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left = tf_b.margin_top = tf_b.margin_right = tf_b.margin_bottom = 0

    p = tf_b.paragraphs[0]
    p.text = "Held-Out Test Benchmark Metrics"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    # Benchmark Table
    tbl_bench = s12.shapes.add_table(5, 4, Inches(7.05), Inches(2.4), Inches(5.2), Inches(2.4)).table
    tbl_bench.columns[0].width = Inches(2.2)
    tbl_bench.columns[1].width = Inches(1.0)
    tbl_bench.columns[2].width = Inches(1.0)
    tbl_bench.columns[3].width = Inches(1.0)

    b_hdrs = ["Model Architecture", "Subset Acc ↑", "Micro F1 ↑", "Macro AUC ↑"]
    for c_idx, h in enumerate(b_hdrs):
        cell = tbl_bench.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PILL_BG
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.name = FONT_HEADING
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_BLACK

    b_rows = [
        ("ProkBERT + Class Attention (Ours)", "0.2800", "0.6716", "0.6777"),
        ("XGBoost Baseline (k-mers)", "0.0800", "0.5897", "0.5833"),
        ("Random Forest Baseline", "0.0400", "0.5479", "0.5417"),
        ("Mean-Pooling Transformer", "0.0000", "0.5312", "0.5125")
    ]
    for r_idx, row in enumerate(b_rows, start=1):
        for c_idx, val in enumerate(row):
            cell = tbl_bench.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_CARD_BG if r_idx > 1 else COLOR_PILL_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_BODY
            p.font.size = Pt(9)
            if r_idx == 1:
                p.font.bold = True
                p.font.color.rgb = COLOR_ACCENT_TEAL if c_idx > 0 else COLOR_TEXT_BLACK
            else:
                p.font.color.rgb = COLOR_TEXT_MUTED

    # Takeaway text
    tb_tkw = s12.shapes.add_textbox(Inches(7.05), Inches(5.0), Inches(5.2), Inches(1.5))
    tf_tkw = tb_tkw.text_frame
    tf_tkw.word_wrap = True
    tf_tkw.margin_left = tf_tkw.margin_top = tf_tkw.margin_right = tf_tkw.margin_bottom = 0

    p_t1 = tf_tkw.paragraphs[0]
    p_t1.text = "Key Scientific Benchmarking Findings:"
    p_t1.font.name = FONT_HEADING
    p_t1.font.size = Pt(11)
    p_t1.font.bold = True
    p_t1.font.color.rgb = COLOR_TEXT_BLACK

    findings = [
        "3.5x Exact-Match Improvement: Outperforms XGBoost by 250% on multi-drug subset accuracy.",
        "Total Failure of Mean-Pooling: Uniform averaging collapses to 0.0000 subset accuracy due to 99.5% neutral background DNA dilution.",
        "Proves Class-Wise Hypothesis: Independent attention heads are mathematically necessary for multi-drug resistant isolates."
    ]
    for f in findings:
        pf = tf_tkw.add_paragraph()
        pf.text = f"• {f}"
        pf.font.name = FONT_BODY
        pf.font.size = Pt(9.5)
        pf.font.color.rgb = COLOR_TEXT_MUTED
        pf.space_before = Pt(3)

    # ==========================================================================
    # SLIDE 13: DIAGNOSTIC ROC & PR CURVES
    # ==========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_white_bg(s13)
    add_header(s13, "Diagnostic Validation", "Receiver Operating Characteristic (ROC) & Precision-Recall Curves",
               "Evaluating discrimination thresholds across 5 major antibiotic families")
    add_footer(s13, 13)

    # Left: ROC Curves
    add_card(s13, 0.8, 1.75, 5.7, 4.9)
    roc_path = FIGURES_DIR / "roc_curves.png"
    if roc_path.exists():
        s13.shapes.add_picture(str(roc_path), Inches(0.95), Inches(1.9), width=Inches(5.4), height=Inches(4.6))

    # Right: Confusion Matrices
    add_card(s13, 6.8, 1.75, 5.7, 4.9)
    cm_path = FIGURES_DIR / "confusion_matrices.png"
    if cm_path.exists():
        s13.shapes.add_picture(str(cm_path), Inches(6.95), Inches(1.9), width=Inches(5.4), height=Inches(4.6))

    # ==========================================================================
    # SLIDE 14: EXPLAINABLE AI & GENOMIC ATTENTION LOCALIZATION
    # ==========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_white_bg(s14)
    add_header(s14, "Mechanistic Explainability", "Attention Weight Heatmap & Genomic Loci Localization",
               "Autonomous, zero-annotation discovery of causal resistance genes and target mutations")
    add_footer(s14, 14)

    # Left: Attention Map
    add_card(s14, 0.8, 1.75, 6.2, 4.9)
    attn_path = FIGURES_DIR / "attention_map_loci.png"
    if attn_path.exists():
        s14.shapes.add_picture(str(attn_path), Inches(0.95), Inches(1.9), width=Inches(5.9), height=Inches(4.6))

    # Right: Interpretability Discussion
    add_card(s14, 7.3, 1.75, 5.2, 4.9)
    tb_xai = s14.shapes.add_textbox(Inches(7.5), Inches(1.95), Inches(4.8), Inches(4.5))
    tf_xai = tb_xai.text_frame
    tf_xai.word_wrap = True
    tf_xai.margin_left = tf_xai.margin_top = tf_xai.margin_right = tf_xai.margin_bottom = 0

    p = tf_xai.paragraphs[0]
    p.text = "Clinical Trust via Mechanistic Interpretability"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    xai_points = [
        ("No 'Black-Box' Assertions", "Clinicians can directly inspect the scalar attention weights alpha_m^(k) across all 24 chunks in the isolate bag."),
        ("Ampicillin Head (alpha_AMP)", "Consistently concentrates over 65% of its attention mass on blaTEM beta-lactamase contig chunks, ignoring chromosomal housekeeping regions."),
        ("Ciprofloxacin Head (alpha_CIP)", "Selectively isolates chromosomal gyrA QRDR loci harboring the canonical Ser83Leu active-site mutation."),
        ("Gentamicin Head (alpha_GEN)", "Attends to aminoglycoside acetyltransferase (aac(3)) cassettes on mobile transposons."),
        ("Regulatory & Accreditation Value", "Meets European and FDA requirements for Explainable AI (XAI) in diagnostic medical software.")
    ]
    for title, desc in xai_points:
        px = tf_xai.add_paragraph()
        px.text = f"• {title}: "
        px.font.name = FONT_BODY
        px.font.size = Pt(10)
        px.font.bold = True
        px.font.color.rgb = COLOR_ACCENT_BLUE
        px.space_before = Pt(8)
        pr = px.add_run()
        pr.text = desc
        pr.bold = False
        pr.font.color.rgb = COLOR_TEXT_MUTED

    # ==========================================================================
    # SLIDE 15: MODULE 6 - IMPLEMENTATION, STREAMLIT APP & PRODUCTION SCALE
    # ==========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_white_bg(s15)
    add_header(s15, "Coursera Module 6: Implementing AI in Projects", "Production Streamlit Clinical Decision Support System",
               "Scaling deep learning models from training prototypes into an interactive diagnostic clinical workflow")
    add_footer(s15, 15)

    # Left: App Architecture & Features
    add_card(s15, 0.8, 1.75, 5.7, 4.9)
    tb_app = s15.shapes.add_textbox(Inches(1.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_app = tb_app.text_frame
    tf_app.word_wrap = True
    tf_app.margin_left = tf_app.margin_top = tf_app.margin_right = tf_app.margin_bottom = 0

    p = tf_app.paragraphs[0]
    p.text = "Clinical Diagnostic Dashboard (app/app.py)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    app_features = [
        ("Direct FASTA Contig Ingestion", "Hospital microbiologists drag-and-drop de novo assemblies directly from Nanopore or Illumina sequencers."),
        ("Real-Time Dual-Strand Scanning", "Autonomous regex-based motif extraction processes multi-megabase contigs in < 0.4 seconds."),
        ("Calibrated Confidence Scoring", "Outputs calibrated probabilities alongside binary Susceptible / Resistant calls with warning flags for borderline cases."),
        ("Interactive Attention Heatmaps", "Visualizes which contigs triggered resistance, displaying active site sequences and coordinates."),
        ("Audited Diagnostic PDF Export", "Generates clinical summary reports suitable for electronic health record (EHR) integration.")
    ]
    for feat, f_desc in app_features:
        pf = tf_app.add_paragraph()
        pf.text = f"• {feat}: "
        pf.font.name = FONT_BODY
        pf.font.size = Pt(10.5)
        pf.font.bold = True
        pf.font.color.rgb = COLOR_ACCENT_BLUE
        pf.space_before = Pt(8)
        pr = pf.add_run()
        pr.text = f_desc
        pr.bold = False
        pr.font.color.rgb = COLOR_TEXT_MUTED

    # Right: Operational Metrics & SLA
    add_card(s15, 6.8, 1.75, 5.7, 4.9)
    tb_sla = s15.shapes.add_textbox(Inches(7.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_sla = tb_sla.text_frame
    tf_sla.word_wrap = True
    tf_sla.margin_left = tf_sla.margin_top = tf_sla.margin_right = tf_sla.margin_bottom = 0

    p = tf_sla.paragraphs[0]
    p.text = "Operational Production Metrics & SLAs"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    slas = [
        ("< 1.2 Seconds", "Inference Latency on Standard CPU", "Enables real-time point-of-care analysis without expensive GPU clusters."),
        ("100% Offline Capable", "Air-Gapped Hospital Security", "Zero patient genomic data transmitted across external cloud APIs, ensuring HIPAA/GDPR compliance."),
        ("< 50 MB", "Model Artifact Footprint", "Lightweight, highly optimized PyTorch weights suitable for edge diagnostic devices."),
        ("5 / 5 Tests", "Automated CI/CD Test Coverage", "Verified against regression in unit test suites (tests/test_pipeline.py).")
    ]
    for num, lbl, sub in slas:
        pn = tf_sla.add_paragraph()
        pn.text = f"{num}  "
        pn.font.name = FONT_HEADING
        pn.font.size = Pt(14)
        pn.font.bold = True
        pn.font.color.rgb = COLOR_ACCENT_TEAL
        pn.space_before = Pt(8)

        pr = pn.add_run()
        pr.text = lbl
        pr.font.size = Pt(11)
        pr.font.bold = True
        pr.font.color.rgb = COLOR_TEXT_BLACK

        ps = tf_sla.add_paragraph()
        ps.text = sub
        ps.font.name = FONT_BODY
        ps.font.size = Pt(9.5)
        ps.font.color.rgb = COLOR_TEXT_MUTED
        ps.space_before = Pt(2)

    # ==========================================================================
    # SLIDE 16: MODULE 7/8 - PROJECT CLOSURE, VALUE DELIVERY & RETROSPECTIVE
    # ==========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_white_bg(s16)
    add_header(s16, "Project Closure & Value Delivery", "Project Retrospective, Business Value & Coursera PM Takeaways",
               "Evaluating project ROI, lessons learned from AI project management, and future scalability roadmap")
    add_footer(s16, 16)

    # Left: Value Delivered & ROI
    add_card(s16, 0.8, 1.75, 5.7, 4.9)
    tb_v = s16.shapes.add_textbox(Inches(1.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_v = tb_v.text_frame
    tf_v.word_wrap = True
    tf_v.margin_left = tf_v.margin_top = tf_v.margin_right = tf_v.margin_bottom = 0

    p = tf_v.paragraphs[0]
    p.text = "Tangible Clinical & Business Value Delivered"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    values = [
        ("Diagnostic Acceleration", "Reduced turnaround from 72 hours (culture) to < 15 minutes (sequence), enabling targeted therapy within the critical golden window of sepsis."),
        ("Multi-Drug Predictive Power", "Achieved 0.2800 exact-match subset accuracy across 5 drug classes simultaneously, a 350% increase over standard XGBoost baselines."),
        ("Complete Deliverables Suite", "Engineered open-source PyTorch pipeline, Streamlit diagnostic app, 46-page NMIMS Black Book, 15-week Capstone Log Book, and IEEE Review Paper."),
        ("High-Assurance Patient Safety", "100% Ceftazidime sensitivity eliminates deadly false negatives in critical 3rd-generation cephalosporin administration.")
    ]
    for t, d in values:
        pv = tf_v.add_paragraph()
        pv.text = f"• {t}: "
        pv.font.name = FONT_BODY
        pv.font.size = Pt(10.5)
        pv.font.bold = True
        pv.font.color.rgb = COLOR_ACCENT_TEAL
        pv.space_before = Pt(8)
        pr = pv.add_run()
        pr.text = d
        pr.bold = False
        pr.font.color.rgb = COLOR_TEXT_MUTED

    # Right: Lessons Learned & Future Trajectories
    add_card(s16, 6.8, 1.75, 5.7, 4.9)
    tb_ret = s16.shapes.add_textbox(Inches(7.05), Inches(1.95), Inches(5.2), Inches(4.5))
    tf_ret = tb_ret.text_frame
    tf_ret.word_wrap = True
    tf_ret.margin_left = tf_ret.margin_top = tf_ret.margin_right = tf_ret.margin_bottom = 0

    p = tf_ret.paragraphs[0]
    p.text = "Key Coursera AI PM Lessons & Future Trajectory"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    lessons = [
        ("Data Quality Outweighs Model Scale", "Auditing and enforcing laboratory-verified AST labels contributed more to clinical accuracy than hyperparameter tuning alone."),
        ("Architecture Must Reflect Biology", "Single-head attention failed because MDR phenotypes are uncoupled. Designing class-wise heads solved the biological reality."),
        ("Subquadratic Megabase Scaling (Future)", "Integrate linear attention models (M5, HyenaDNA) to process unfragmented 5 Mbp bacterial chromosomes in single contexts."),
        ("Pan-Pathogen Expansion (Future)", "Scale the framework to Klebsiella pneumoniae, Pseudomonas aeruginosa, and Acinetobacter baumannii for broad hospital coverage.")
    ]
    for t, d in lessons:
        pl = tf_ret.add_paragraph()
        pl.text = f"• {t}: "
        pl.font.name = FONT_BODY
        pl.font.size = Pt(10.5)
        pl.font.bold = True
        pl.font.color.rgb = COLOR_ACCENT_BLUE
        pl.space_before = Pt(8)
        pr = pl.add_run()
        pr.text = d
        pr.bold = False
        pr.font.color.rgb = COLOR_TEXT_MUTED

    # ==========================================================================
    # SLIDE 17: CONCLUSION, TEAM CREDITS & Q&A
    # ==========================================================================
    s17 = prs.slides.add_slide(blank_layout)
    set_white_bg(s17)
    add_header(s17, "Project Conclusion", "Summary of Achievements & Acknowledgments",
               "AI-Driven Prediction of Antimicrobial Resistance Using Genomic Language Models")
    add_footer(s17, 17)

    # Big Center Card
    add_card(s17, 1.5, 1.75, 10.333, 4.9)
    tb_end = s17.shapes.add_textbox(Inches(1.8), Inches(1.95), Inches(9.7), Inches(4.5))
    tf_end = tb_end.text_frame
    tf_end.word_wrap = True
    tf_end.margin_left = tf_end.margin_top = tf_end.margin_right = tf_end.margin_bottom = 0

    p = tf_end.paragraphs[0]
    p.text = "A Validated, Interpretable Paradigm for Rapid Genomic AMR Prediction"
    p.font.name = FONT_HEADING
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_BLACK

    p_sum = tf_end.add_paragraph()
    p_sum.text = ("By coupling prokaryote-specialized bidirectional transformers (ProkBERT) with dual-strand resistome scanning "
                  "and Class-Wise Multi-Head Attention Pooling, we bridged the critical gap between raw bacterial whole-genome sequencing "
                  "and actionable, explainable clinical diagnostics. Governed through the principles of AI Project Management, the project was "
                  "delivered on time, fully verified, and ready for clinical decision support deployment.")
    p_sum.font.name = FONT_BODY
    p_sum.font.size = Pt(11.5)
    p_sum.font.color.rgb = COLOR_TEXT_MUTED
    p_sum.space_before = Pt(10)

    # Team Members Block
    p_tm = tf_end.add_paragraph()
    p_tm.text = "Project Team Members & Contributions:"
    p_tm.font.name = FONT_HEADING
    p_tm.font.size = Pt(13)
    p_tm.font.bold = True
    p_tm.font.color.rgb = COLOR_ACCENT_BLUE
    p_tm.space_before = Pt(16)

    tms = [
        ("Niti Sharma", "Lead Data Engineer & Bioinformatician (Resistome Scanning & Contig Curation)"),
        ("Ishita Tripathi", "Lead AI/ML Researcher & Architect (ProkBERT Modeling & Class-Wise Attention)"),
        ("Vishva Shah", "MLOps, Governance & Deployment Lead (Clinical Dashboard & Ethical Calibration)")
    ]
    for name, rle in tms:
        pt = tf_end.add_paragraph()
        pt.text = f"• {name}  —  "
        pt.font.name = FONT_BODY
        pt.font.size = Pt(11)
        pt.font.bold = True
        pt.font.color.rgb = COLOR_TEXT_BLACK
        pt.space_before = Pt(4)
        pr = pt.add_run()
        pr.text = rle
        pr.bold = False
        pr.font.color.rgb = COLOR_TEXT_MUTED

    # Q&A Prompt
    p_qa = tf_end.add_paragraph()
    p_qa.text = "Thank You! Questions & Discussion are warmly welcomed."
    p_qa.font.name = FONT_HEADING
    p_qa.font.size = Pt(14)
    p_qa.font.bold = True
    p_qa.font.color.rgb = COLOR_ACCENT_TEAL
    p_qa.alignment = PP_ALIGN.CENTER
    p_qa.space_before = Pt(22)

    # Save presentation
    prs.save(str(OUTPUT_PPTX))
    print(f"Successfully generated Coursera Capstone Presentation: {OUTPUT_PPTX}")

if __name__ == "__main__":
    create_presentation()

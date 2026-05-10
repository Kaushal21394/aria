"""
50 synthetic CRO proposal summaries for ARIA's RAG knowledge layer.

Each document represents a past proposal/study summary from Meridian CRO.
Metadata fields are used for filtered retrieval in the Outreach Drafter agent.

Therapeutic areas: oncology, rare_disease, neurology, cardiology,
                   metabolic, respiratory, immunology, infectious_disease
Phases: Phase I, Phase I/II, Phase II, Phase III
Outcomes: won, lost, ongoing
"""
from __future__ import annotations

from typing import Any, Dict, List

PROPOSALS: List[Dict[str, Any]] = [
    # ── Oncology (10) ──────────────────────────────────────────────────────────
    {
        "id": "prop_001",
        "therapeutic_area": "oncology",
        "phase": "Phase I/II",
        "service_type": "full_service",
        "geography": "north_america",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "small",
        "text": (
            "Arpex Oncology engaged Meridian CRO for full-service Phase I/II support for ARPX-101, "
            "a bispecific antibody targeting HER2+ solid tumors. The study enrolled 48 patients across "
            "12 investigative sites in the US and Canada, including 4 academic cancer centers. Primary "
            "endpoints required serial PK sampling and tumor biopsies, demanding highly trained site "
            "coordinators. Meridian designed the eClinical platform to support complex adaptive dose "
            "escalation, with a safety monitoring committee reviewing data every two cohorts.\n\n"
            "Meridian's biomarker operations team managed central HER2 IHC/FISH testing across all "
            "sites with a <3% sample rejection rate. A custom EDC workflow flagged protocol deviations "
            "in real time, reducing query resolution time by 35% vs. industry benchmark.\n\n"
            "Outcome: WON — Arpex renewed for a Phase II expansion (180 patients, 20 sites) following "
            "a positive Phase I readout. Key differentiator cited by sponsor: Meridian's biomarker "
            "logistics and CAP/CLIA central lab network."
        ),
    },
    {
        "id": "prop_002",
        "therapeutic_area": "oncology",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2023,
        "sponsor_size": "large",
        "text": (
            "ClearPath Pharma selected Meridian CRO for a Phase III registrational study of CPP-4510, "
            "a 3rd-generation EGFR inhibitor in non-small cell lung cancer (NSCLC). The 620-patient "
            "study operated across 85 sites in the US, EU, and South Korea. The primary endpoint was "
            "progression-free survival by BICR, requiring Meridian's independent imaging vendor "
            "management and blinded central read program.\n\n"
            "Meridian's regulatory operations team led the FDA pre-submission meeting, optimized the "
            "statistical analysis plan, and supported the China filing strategy as a parallel track. "
            "Enrollment completed 2 months ahead of schedule due to Meridian's site activation "
            "performance (median 42-day site activation across 85 sites).\n\n"
            "Outcome: WON — NDA submission accepted. ClearPath awarded Meridian a follow-on oncology "
            "franchise agreement covering the next three pipeline assets."
        ),
    },
    {
        "id": "prop_003",
        "therapeutic_area": "oncology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "north_america",
        "outcome": "ongoing",
        "year": 2024,
        "sponsor_size": "mid",
        "text": (
            "Solace Biosciences retained Meridian CRO for a Phase II randomized study of SOL-882, an "
            "antibody-drug conjugate in triple-negative breast cancer. The study targets 200 patients "
            "across 30 US sites (academic and community), with PFS and OS as co-primary endpoints. "
            "Key complexity: extensive tumor sampling for translational research at baseline, Cycle 2 "
            "Day 1, and at progression.\n\n"
            "Meridian leads data management, biostatistics, and central lab services. An automated "
            "sample tracking system alerts site coordinators within 4 hours of any collection "
            "deviation. Enrollment is 60% complete as of Q3 2024.\n\n"
            "Outcome: ONGOING — Interim analysis expected Q2 2025 with a pre-specified adaptive "
            "sample size recalculation option if the interim hazard ratio falls within a "
            "pre-defined zone."
        ),
    },
    {
        "id": "prop_004",
        "therapeutic_area": "oncology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "north_america",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "mid",
        "text": (
            "Novara Therapeutics selected Meridian for a Phase II single-arm study of NVR-703, an "
            "IDH2 inhibitor in relapsed/refractory acute myeloid leukemia (AML). Eighty-five patients "
            "enrolled at 18 US hematology centers. The heavily pre-treated population (median 3 prior "
            "lines) required intensive eligibility screening support.\n\n"
            "Meridian's hematology-specialist CRAs reduced screen failure rate by 22% vs. sponsor "
            "projections through enhanced pre-screen training and a dedicated eligibility hotline. "
            "Central bone marrow review by an independent hematopathology panel was managed by "
            "Meridian's biopsy logistics team with a 98% adequate sample rate.\n\n"
            "Outcome: WON — Novara filed a BLA and cited Meridian in the NDA for data quality. "
            "A follow-on Phase III combination study was awarded to Meridian."
        ),
    },
    {
        "id": "prop_005",
        "therapeutic_area": "oncology",
        "phase": "Phase I",
        "service_type": "full_service",
        "geography": "north_america",
        "outcome": "won",
        "year": 2021,
        "sponsor_size": "small",
        "text": (
            "Helix Immuno contracted Meridian CRO to manage a Phase I safety study combining HXI-250 "
            "(anti-PD-L1) with stereotactic body radiation in locally advanced solid tumors. "
            "Thirty-six patients enrolled at 6 NCI-designated cancer centers. The complex protocol "
            "required coordination of SBRT scheduling with immunotherapy dosing windows.\n\n"
            "Meridian developed a real-time site dashboard for dose scheduling compliance and managed "
            "AE adjudication for radiation-related vs. drug-related events. Protocol compliance rate "
            "exceeded 98% across all sentinel and expansion cohorts.\n\n"
            "Outcome: WON — Clean safety database enabled FDA IND amendment for Phase II. Sponsor "
            "attributed the compliance rate to Meridian's site oversight model. Phase II full-service "
            "agreement executed."
        ),
    },
    {
        "id": "prop_006",
        "therapeutic_area": "oncology",
        "phase": "Phase II",
        "service_type": "regulatory",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "large",
        "text": (
            "JapanPharma KK, partnered with Bridgetech, engaged Meridian CRO for a Phase II bridging "
            "study of JP-0440 in colorectal cancer, required for US IND submission following positive "
            "Japan data. Eighty patients enrolled at 10 US GI oncology centers and 4 Japan sites. "
            "Meridian managed cross-border data harmonization between US eClinical systems and Japan's "
            "J-GCP data requirements.\n\n"
            "Meridian's regulatory affairs team prepared the full IND submission package, bridging "
            "Japan Phase II data with US exposure-response analyses. FDA acknowledged receipt with "
            "no clinical hold.\n\n"
            "Outcome: WON — Bridging study met primary endpoint; NDA submission supported within "
            "6 months of enrollment completion. Meridian cited as the critical connector between "
            "Japan and US regulatory strategies."
        ),
    },
    {
        "id": "prop_007",
        "therapeutic_area": "oncology",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "lost",
        "year": 2022,
        "sponsor_size": "large",
        "text": (
            "Cascadia Bio evaluated Meridian CRO for a Phase III study of CAS-9900, a PSMA-targeted "
            "radioligand therapy in metastatic castration-resistant prostate cancer (mCRPC). "
            "Nine hundred patients targeted across global sites (US, EU, Australia, Canada).\n\n"
            "Meridian was shortlisted but lost to a larger CRO with established radioligand therapy "
            "handling infrastructure and compliance certification for high-energy radiopharmaceutical "
            "handling at over 50 sites. Meridian's radiation pharmacist network and Qualified Person "
            "infrastructure were insufficient to meet sponsor requirements.\n\n"
            "Outcome: LOST — Winning CRO offered 40 pre-qualified radioligand therapy sites vs. "
            "Meridian's 12. Radioligand therapy site network is a strategic investment priority "
            "for the oncology franchise."
        ),
    },
    {
        "id": "prop_008",
        "therapeutic_area": "oncology",
        "phase": "Phase I",
        "service_type": "logistics",
        "geography": "north_america",
        "outcome": "won",
        "year": 2023,
        "sponsor_size": "small",
        "text": (
            "CellVector Bio retained Meridian CRO to manage the leukapheresis logistics and "
            "manufacturing-chain monitoring for a Phase I CAR-T study in large B-cell lymphoma. "
            "Twenty-four patients enrolled at 6 authorized treatment centers. Meridian developed "
            "a proprietary chain-of-custody tracking system integrated with the cell therapy "
            "manufacturer's LIMS.\n\n"
            "Temperature excursion rate during product transport: 0% across 48 shipments. Meridian's "
            "cell therapy coordinators were embedded at each site to manage the 22-day vein-to-vein "
            "window, significantly reducing scheduling failures.\n\n"
            "Outcome: WON — CellVector recognized Meridian as preferred cell therapy logistics "
            "partner; 3 additional cell therapy trials in the pipeline awarded. The 0% excursion "
            "rate is best-in-class for this modality."
        ),
    },
    {
        "id": "prop_009",
        "therapeutic_area": "oncology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "europe",
        "outcome": "won",
        "year": 2021,
        "sponsor_size": "mid",
        "text": (
            "EurOncology Partners selected Meridian CRO's European operations for a Phase II study "
            "of EOP-44, a PARP inhibitor/anti-angiogenic combination in platinum-sensitive ovarian "
            "cancer. One hundred and twenty patients enrolled across 18 EU sites (Germany, France, "
            "UK, Spain, Netherlands). Meridian EU managed all local regulatory submissions, import "
            "licenses, and patient informed consent translations across 5 languages.\n\n"
            "Central CA-125 and BRCA testing were coordinated through a single EU central laboratory. "
            "Meridian's EU site activation cycle was 38 days median vs. the 60-day EU industry "
            "benchmark for oncology trials.\n\n"
            "Outcome: WON — European MA filing supported. Meridian EU team's regulatory expertise "
            "and pre-existing site relationships were cited as decisive factors in EurOncology's "
            "RFP debrief."
        ),
    },
    {
        "id": "prop_010",
        "therapeutic_area": "oncology",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "lost",
        "year": 2023,
        "sponsor_size": "mid",
        "text": (
            "Pathogen Therapeutics evaluated Meridian for a Phase III study of PATH-21 in pancreatic "
            "cancer with a quality-of-life co-primary endpoint alongside overall survival. "
            "Six hundred patients across global sites targeted.\n\n"
            "Meridian lost on two factors: price (15% higher than the winning bid) and perceived "
            "depth of patient-reported outcomes (PRO) and COA expertise. The sponsor's highest-weight "
            "evaluation criterion was ePRO platform capability and PRO training for sites in "
            "GI oncology.\n\n"
            "Outcome: LOST — Key lesson: invest in a dedicated COA/PRO capability center with GI "
            "oncology-specific QoL instrument experience and a proprietary ePRO platform."
        ),
    },

    # ── Rare Disease (8) ───────────────────────────────────────────────────────
    {
        "id": "prop_011",
        "therapeutic_area": "rare_disease",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "north_america",
        "outcome": "won",
        "year": 2021,
        "sponsor_size": "small",
        "text": (
            "Genova Therapeutics contracted Meridian CRO for a Phase II study of GTV-512, an "
            "exon-skipping therapy in ambulatory boys with Duchenne muscular dystrophy (DMD, age 5–16). "
            "Sixty patients enrolled at 12 US pediatric neuromuscular centers. Natural history data "
            "gaps required Meridian to build a custom 6-minute walk test normative database from "
            "external sources for benchmarking.\n\n"
            "Pediatric consent and assent processes were standardized across all sites by Meridian's "
            "patient advocacy coordinator. A dedicated pediatric CRA with neuromuscular disease "
            "experience was assigned to each site cluster.\n\n"
            "Outcome: WON — North Star Ambulatory Assessment data quality was characterized as "
            "'among the best I have reviewed' by FDA in a Type B meeting. Follow-on Phase III "
            "natural history sub-study awarded to Meridian."
        ),
    },
    {
        "id": "prop_012",
        "therapeutic_area": "rare_disease",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "mid",
        "text": (
            "GenPathways retained Meridian CRO for a Phase III gene therapy study of GPW-1, an AAV9 "
            "vector in SMA Type I infants (<6 months). Forty-five patients enrolled at 9 sites across "
            "US and EU. Critical complexities: single-dose IV infusion requiring pre-immunosuppression, "
            "immunogenicity monitoring over 24 months, and anti-AAV9 antibody screening at baseline.\n\n"
            "Meridian's rare disease team developed site feasibility criteria including ICU respiratory "
            "support capability and infant spinal cord MRI standards. A dedicated gene therapy "
            "operations pharmacist was embedded at each infusion center.\n\n"
            "Outcome: WON — BLA filed and approved. FDA cited the data package as 'a model for gene "
            "therapy trial conduct.' This landmark trial established Meridian as a recognized leader "
            "in rare pediatric gene therapy operations."
        ),
    },
    {
        "id": "prop_013",
        "therapeutic_area": "rare_disease",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "europe",
        "outcome": "won",
        "year": 2021,
        "sponsor_size": "mid",
        "text": (
            "FabryGen engaged Meridian CRO for a Phase III study of FGN-9, a novel enzyme replacement "
            "therapy in Fabry disease with cardiomyopathy. One hundred and twenty patients enrolled "
            "at 20 EU and 5 US sites, covering ERT-naive and ERT-switch populations. Meridian managed "
            "the complex stratified randomization and crossover endpoint design.\n\n"
            "Echocardiography core lab coordination and 24-hour ambulatory blood pressure monitoring "
            "were centralized by Meridian's cardiac imaging operations team. GCP inspection by EMA "
            "yielded zero critical findings — a landmark for Meridian's EU operations.\n\n"
            "Outcome: WON — EU MA granted by EMA. US NDA under review. Meridian's EU GCP compliance "
            "record cited as a key differentiator in the sponsor's CRO evaluation."
        ),
    },
    {
        "id": "prop_014",
        "therapeutic_area": "rare_disease",
        "phase": "Phase I/II",
        "service_type": "regulatory",
        "geography": "north_america",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "small",
        "text": (
            "MetaRare Inc. contracted Meridian CRO for a Phase I/II safety and efficacy study of "
            "MRI-7 in methylmalonic acidemia (MMA), a rare inborn error of metabolism. Twenty-four "
            "pediatric patients enrolled at 6 metabolic disease referral centers under FDA Rare "
            "Pediatric Disease designation.\n\n"
            "Meridian prepared the IND, managed FDA communications, and coordinated protocol "
            "amendments through two FDA cycles. A metabolic disease medical director reviewed each "
            "patient's eligibility and safety events in real time, managing complex ammonia-monitoring "
            "stopping rules.\n\n"
            "Outcome: WON — Rare Pediatric Disease Priority Review Voucher received. Meridian's "
            "metabolic disease site network and regulatory advisory capability recognized as unique "
            "competitive strengths in this ultra-rare indication."
        ),
    },
    {
        "id": "prop_015",
        "therapeutic_area": "rare_disease",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2023,
        "sponsor_size": "large",
        "text": (
            "CFTherapy Corp selected Meridian CRO for a Phase III study of CFT-800, a CFTR "
            "potentiator/corrector triple combination in CF patients aged ≥12 with F508del/minimal "
            "function mutations. Four hundred patients enrolled across 50 CF Foundation-accredited "
            "centers (US, Canada, Germany, UK, France).\n\n"
            "Meridian partnered with the CF Foundation's Therapeutics Development Network for site "
            "identification, reducing start-up time by 6 weeks. Spirometry and sweat chloride central "
            "review protocols were established with a dedicated respiratory physiologist.\n\n"
            "Outcome: WON — Enrollment 3 months ahead of schedule; NDA filed. Meridian named as "
            "preferred CRO partner in CFTherapy's 5-year pipeline agreement, covering 4 planned "
            "rare respiratory studies."
        ),
    },
    {
        "id": "prop_016",
        "therapeutic_area": "rare_disease",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "asia_pacific",
        "outcome": "lost",
        "year": 2023,
        "sponsor_size": "mid",
        "text": (
            "TransAmyloid Pharma evaluated Meridian for a Phase II study of TAP-3 in hereditary "
            "transthyretin amyloidosis (hATTR) with cardiomyopathy. Sites were required in US, EU, "
            "Japan, and Taiwan — a complex multi-regional package.\n\n"
            "Meridian was not selected due to limited Japan regulatory experience and an insufficient "
            "number of pre-qualified echocardiography core lab partners familiar with hATTR-specific "
            "cardiac endpoint definitions (extracellular volume fraction, native T1 mapping).\n\n"
            "Outcome: LOST — Key lesson: expand Japan and Taiwan regulatory affairs capability and "
            "validate cardiac imaging core lab partners with hATTR-specific MRI expertise. The hATTR "
            "cardiomyopathy space is growing and represents a strategic gap to close."
        ),
    },
    {
        "id": "prop_017",
        "therapeutic_area": "rare_disease",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "europe",
        "outcome": "ongoing",
        "year": 2024,
        "sponsor_size": "mid",
        "text": (
            "AdaptaNeuro retained Meridian CRO for a Phase III adaptive design study of ANR-14 in "
            "early manifest Huntington's disease (cUHDRS primary endpoint). Three hundred patients "
            "enrolled across 45 EU sites (Germany, UK, Netherlands, Denmark, France, Italy). The "
            "adaptive design includes a pre-specified interim analysis at 50% enrollment for potential "
            "sample size re-estimation.\n\n"
            "Meridian leads statistical programming, DSMB secretariat, and patient-reported outcome "
            "data capture via a custom eCOA platform. Site coordinator training was developed in "
            "partnership with the European Huntington's Disease Network (EHDN).\n\n"
            "Outcome: ONGOING — 45% enrolled as of Q2 2024. Interim analysis planned Q4 2024. "
            "EHDN site collaboration is a key recruitment driver."
        ),
    },
    {
        "id": "prop_018",
        "therapeutic_area": "rare_disease",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "small",
        "text": (
            "LysoCure Bio contracted Meridian CRO for a Phase II study of LCB-5, an oral substrate "
            "reduction therapy in Gaucher disease Type III (neuronopathic form). Forty patients "
            "enrolled at 15 sites in the US, Israel, and EU. The neuronopathic endpoint package "
            "required neuropsychological testing in multiple languages and brain MRI volumetry at "
            "academic centers with certified protocols.\n\n"
            "Meridian's rare disease neuropsychology team built a COA package that passed FDA "
            "validation review. MRI volumetry analysis was performed by a central academic "
            "neuroradiology partner under Meridian contract.\n\n"
            "Outcome: WON — FDA granted Accelerated Approval pathway. Meridian's neuropsychology "
            "COA package was cited as a key strength in FDA meeting minutes. Continued as CRO "
            "for the confirmatory Phase III trial."
        ),
    },

    # ── Neurology (8) ─────────────────────────────────────────────────────────
    {
        "id": "prop_019",
        "therapeutic_area": "neurology",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "large",
        "text": (
            "AlzClear Therapeutics selected Meridian CRO to manage a Phase III study of ACT-100, an "
            "anti-tau antibody in early Alzheimer's disease (CDR 0.5–1.0). Eight hundred patients "
            "enrolled at 90 global sites (US, EU, Japan). The study required amyloid PET confirmation "
            "at screening — Meridian managed a central PET reader program and negotiated preferential "
            "rates with 6 imaging vendors across 3 continents.\n\n"
            "A blood-based biomarker sub-study (plasma p-tau217) required specialized sample handling "
            "and central lab logistics. Meridian's biomarker operations team achieved a <2% sample "
            "rejection rate globally.\n\n"
            "Outcome: WON — Phase III met co-primary endpoints (CDR-SB and ADAS-Cog); NDA filing "
            "anticipated. FDA evaluated Meridian's central PET operations as a key element of "
            "data integrity in the NDA review."
        ),
    },
    {
        "id": "prop_020",
        "therapeutic_area": "neurology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "north_america",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "small",
        "text": (
            "NeuroMotion Bio engaged Meridian CRO for a Phase II study of NMB-33, a GLP-1R agonist "
            "in early Parkinson's disease (H&Y Stage 1–2). One hundred and fifty patients enrolled "
            "at 20 US movement disorder centers. The study used a novel wearable-based endpoint "
            "(tremor/bradykinesia composite), requiring Meridian to develop site training for sensor "
            "placement, calibration, and data upload verification.\n\n"
            "Meridian's digital health team built a custom EDC integration for wearable data "
            "ingestion, flagging anomalies in real time. Device data quality exceeded the "
            "FDA-specified pre-specified acceptability threshold across all sites.\n\n"
            "Outcome: WON — Digital endpoint data quality highlighted at IAPRD as methodological "
            "innovation. NeuroMotion cited Meridian's digital health team as the decisive factor. "
            "Phase IIb agreement executed."
        ),
    },
    {
        "id": "prop_021",
        "therapeutic_area": "neurology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "europe",
        "outcome": "won",
        "year": 2021,
        "sponsor_size": "mid",
        "text": (
            "ImmunoCNS selected Meridian CRO's EU operations for a Phase II head-to-head study of "
            "ICN-77 vs. teriflunomide in relapsing multiple sclerosis. Two hundred and eighty patients "
            "at 35 EU sites. A centralized MRI reading program with two independent neuroradiologists "
            "reviewed all T2/T1 Gd+ scans for protocol deviations and lesion counting accuracy.\n\n"
            "Meridian's EU regulatory team managed decentralized submission packages across 9 EU "
            "member states, achieving simultaneous first-patient-in across 9 countries. The central "
            "MRI program returned reads within 5 business days.\n\n"
            "Outcome: WON — Study met non-inferiority margin; EU MA variation filing submitted. "
            "ImmunoCNS cited Meridian's MRI core lab and EU regulatory network as differentiators "
            "in their public business development commentary."
        ),
    },
    {
        "id": "prop_022",
        "therapeutic_area": "neurology",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2021,
        "sponsor_size": "large",
        "text": (
            "Cepha Bio engaged Meridian CRO for a Phase III study of CPB-44, a CGRP receptor "
            "antagonist in chronic migraine prevention. Six hundred and fifty patients enrolled across "
            "60 US and 20 EU sites. Patient-reported electronic diary data were captured via "
            "Meridian's ePRO platform, pre-validated for the ICHD-3 headache diary format.\n\n"
            "Site coordinator training for diary completion coaching was standardized via an LMS "
            "module developed by Meridian's COA team. A dedicated ePRO support line handled "
            "patient questions 7 days a week.\n\n"
            "Outcome: WON — Strong primary endpoint (monthly headache day reduction); NDA filed. "
            "Meridian's ePRO platform data completeness rate (>97%) was highlighted in the FDA "
            "advisory committee briefing document as best practice."
        ),
    },
    {
        "id": "prop_023",
        "therapeutic_area": "neurology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "north_america",
        "outcome": "lost",
        "year": 2023,
        "sponsor_size": "mid",
        "text": (
            "NeuralPath Inc. evaluated Meridian for a Phase II study of NPI-60, a neuroprotective "
            "agent in ALS with ALSFRS-R as the primary endpoint. Sites required across US and Canada, "
            "drawing on established ALS specialty centers.\n\n"
            "Meridian was not selected due to a limited ALS site network and insufficient dedicated "
            "ALS CRA expertise. The competing CRO had pre-qualified 30 ALS specialty centers vs. "
            "Meridian's 8, and had existing relationships with the Northeast ALS Consortium (NEALS).\n\n"
            "Outcome: LOST — Key lesson: ALS trials require specialized site relationships and "
            "dedicated ALSFRS-R CRA training. A NEALS partnership and expanded ALS site network "
            "are strategic priorities for the neurology franchise."
        ),
    },
    {
        "id": "prop_024",
        "therapeutic_area": "neurology",
        "phase": "Phase I",
        "service_type": "regulatory",
        "geography": "north_america",
        "outcome": "won",
        "year": 2023,
        "sponsor_size": "small",
        "text": (
            "SpineGenix contracted Meridian CRO to manage a Phase I safety study of SGX-1, an "
            "AAV-delivered BDNF gene therapy administered intrathecally in chronic thoracic spinal "
            "cord injury. Eighteen patients enrolled at 4 US academic SCI centers.\n\n"
            "Meridian prepared the IND, managed DSMB operations, and wrote a risk management "
            "protocol addressing gene therapy-specific risks including immunogenicity and insertional "
            "mutagenesis — accepted by FDA without clinical hold. Intrathecal delivery procedure "
            "monitoring was conducted by Meridian's specialist neurology CRAs.\n\n"
            "Outcome: WON — 6/6 sentinel dose cohort completed without dose-limiting toxicities; "
            "Phase I/II expansion IND amendment filed. SpineGenix named Meridian as the Phase II "
            "full-service CRO."
        ),
    },
    {
        "id": "prop_025",
        "therapeutic_area": "neurology",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "large",
        "text": (
            "EpilexPharma selected Meridian CRO for a Phase III study of ELP-7, a voltage-gated "
            "sodium channel modulator in drug-resistant focal epilepsy. Four hundred and twenty "
            "patients enrolled across dual cohorts (pediatric age 4–11 and adult) at 55 EU and "
            "US sites. Central EEG reading panel and seizure diary data management were both "
            "managed by Meridian.\n\n"
            "The pediatric cohort required age-appropriate eCOA forms and a dedicated pediatric "
            "site support line. Consent and assent were translated into 12 languages.\n\n"
            "Outcome: WON — EU and US regulatory submissions supported. Meridian's dual-cohort "
            "management and central EEG program were cited as key study strengths in the EU "
            "regulatory assessment report."
        ),
    },
    {
        "id": "prop_026",
        "therapeutic_area": "neurology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "north_america",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "small",
        "text": (
            "ClearMind Bio contracted Meridian CRO for a Phase II study of CMB-5, an NMDA receptor "
            "modulator in treatment-resistant depression (TRD). One hundred and eighty patients "
            "enrolled at 25 US academic psychiatry sites. Mandatory rater training for MADRS and "
            "HDRS, with a 24/7 site support line staffed by Meridian psychiatric nurse specialists, "
            "mitigated acute psychiatric event risks.\n\n"
            "Meridian's data operations team implemented automated query generation to flag outlier "
            "rater performance. Inter-rater reliability analysis showed Meridian-trained sites had "
            "significantly lower ICC variation than published industry benchmarks.\n\n"
            "Outcome: WON — Statistically significant MADRS improvement at interim analysis; IND "
            "expanded to include post-partum depression. Rater training program licensed to two "
            "other sponsors as a standalone service."
        ),
    },

    # ── Cardiology (6) ────────────────────────────────────────────────────────
    {
        "id": "prop_027",
        "therapeutic_area": "cardiology",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "large",
        "text": (
            "HeartFirst Pharma retained Meridian CRO for a Phase III outcomes trial of HFP-3, a "
            "novel GLP-1/GIP dual agonist in HFpEF. Two thousand eight hundred patients enrolled at "
            "220 global sites (US, EU, Brazil, China). Primary endpoint: composite MACE plus heart "
            "failure hospitalization. Meridian's cardiovascular outcomes trial team managed the "
            "independent event adjudication committee with a 99.7% adjudication completion rate.\n\n"
            "Central echocardiography laboratory managed E/e' ratio and LVEF measurements. Meridian's "
            "CVOT event adjudication infrastructure was evaluated by the FDA advisory committee as "
            "critical infrastructure.\n\n"
            "Outcome: WON — Study met primary endpoint; NDA filing supported positive regulatory "
            "review. Meridian's CVOT capability positions it as a top-3 CRO in cardiovascular "
            "outcomes research."
        ),
    },
    {
        "id": "prop_028",
        "therapeutic_area": "cardiology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "europe",
        "outcome": "won",
        "year": 2021,
        "sponsor_size": "mid",
        "text": (
            "EuroCardio AG selected Meridian CRO's EU team for a Phase II biomarker-enrichment study "
            "of ECG-11, a platelet P2Y12 inhibitor in high-risk acute coronary syndrome (ACS). "
            "Three hundred patients enrolled at 28 EU interventional cardiology centers. The study "
            "used pre-specified biomarker stratification by hs-CRP and platelet reactivity index.\n\n"
            "Meridian managed the central biomarker lab, ensuring <6-hour sample processing to meet "
            "assay stability windows. Meridian's EU cardiology CRA team had prior catheterization "
            "lab monitoring experience critical for ACS patient management.\n\n"
            "Outcome: WON — Biomarker-positive subgroup showed a clear dose response; Phase III "
            "planned. EuroCardio cited Meridian EU's cardiology CRA network and biomarker operations "
            "as differentiating factors."
        ),
    },
    {
        "id": "prop_029",
        "therapeutic_area": "cardiology",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "asia_pacific",
        "outcome": "won",
        "year": 2023,
        "sponsor_size": "large",
        "text": (
            "PacificHeart KK contracted Meridian CRO for a Phase III study of PHK-20, a factor XIa "
            "inhibitor in non-valvular atrial fibrillation for stroke prevention, with primary "
            "enrollment in Asia-Pacific (Japan, South Korea, Singapore, Australia). Twelve hundred "
            "patients enrolled at 80 APAC sites.\n\n"
            "Meridian's APAC team managed all country regulatory submissions and PMDA scientific "
            "consultations, filing all 4 country submissions within 90 days of study start — a "
            "program record for APAC regulatory operations.\n\n"
            "Outcome: WON — Enrollment completed on schedule; PMDA submission supported. Meridian "
            "APAC's multi-country regulatory capability cited as the single most important "
            "differentiator in PacificHeart's CRO selection process."
        ),
    },
    {
        "id": "prop_030",
        "therapeutic_area": "cardiology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "lost",
        "year": 2022,
        "sponsor_size": "mid",
        "text": (
            "PressureLow Bio evaluated Meridian for a Phase II study of PLB-5, a renal denervation "
            "catheter device in resistant hypertension. Sites required active catheterization "
            "laboratory infrastructure and trained interventional cardiologists.\n\n"
            "Meridian was not selected due to limited interventional cardiology procedure monitoring "
            "experience and insufficient track record with device/drug combination studies. The "
            "competing CRO had 8 dedicated interventional cardiology trials in the prior 3 years "
            "vs. Meridian's 2.\n\n"
            "Outcome: LOST — Key lesson: interventional cardiology procedure monitoring is a "
            "capability gap. Investment needed in catheterization lab monitoring protocols and "
            "device/drug combination study experience."
        ),
    },
    {
        "id": "prop_031",
        "therapeutic_area": "cardiology",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2023,
        "sponsor_size": "large",
        "text": (
            "StatinNova selected Meridian CRO for a Phase III study of STN-7, a hepatocyte-targeting "
            "siRNA for LDL reduction in familial hypercholesterolemia. Nine hundred patients enrolled "
            "at 70 sites globally (US, EU, Canada). The siRNA formulation required central lipid "
            "panel processing with specific centrifugation and storage protocols.\n\n"
            "Meridian's laboratory operations team established protocol adherence monitoring with "
            "automated temperature alerts and a <2% sample rejection rate across all sites. The "
            "siRNA cold-chain distribution was managed end-to-end by Meridian's depot network.\n\n"
            "Outcome: WON — LDL reduction primary endpoint met. Sponsor credited Meridian's lab "
            "quality program for the sample quality record. Phase IV outcomes trial planned with "
            "Meridian as preferred CRO."
        ),
    },
    {
        "id": "prop_032",
        "therapeutic_area": "cardiology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "north_america",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "small",
        "text": (
            "CardiGene Therapeutics contracted Meridian CRO for a Phase II study of CGT-4, a cardiac "
            "myosin inhibitor in symptomatic obstructive hypertrophic cardiomyopathy (HCM). Two "
            "hundred patients enrolled at 25 US HCM specialist centers, the majority affiliated with "
            "the HCM Network registry.\n\n"
            "Meridian developed a site qualification checklist tied to HCM Network certification "
            "criteria. LVOT gradient measurement by echocardiography was performed by a central "
            "core lab with HCM-specialist cardiologist readers.\n\n"
            "Outcome: WON — Study met primary endpoint (LVOT gradient reduction); FDA granted "
            "Breakthrough Therapy Designation. Meridian's access to HCM Network sites was cited as "
            "a unique competitive advantage by CardiGene."
        ),
    },

    # ── Metabolic / Diabetes (6) ───────────────────────────────────────────────
    {
        "id": "prop_033",
        "therapeutic_area": "metabolic",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "large",
        "text": (
            "GlucoPharm International engaged Meridian CRO for a Phase III cardiovascular outcomes "
            "trial of GPI-801, a novel SGLT2/GLP-1 dual agonist in Type 2 diabetes. Five thousand "
            "patients enrolled at 320 global sites. Primary endpoint: 3-point MACE composite. "
            "Meridian managed the independent MACE adjudication committee and a central HbA1c "
            "laboratory network across 4 regions.\n\n"
            "Enrollment completed 4 months ahead of schedule — 320 sites activated in 8 months, a "
            "record for Meridian's cardiovascular franchise.\n\n"
            "Outcome: WON — NDA filed. Meridian's CVOT execution capability solidified its market "
            "position as a top-3 CRO in the diabetes outcomes segment."
        ),
    },
    {
        "id": "prop_034",
        "therapeutic_area": "metabolic",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "north_america",
        "outcome": "won",
        "year": 2023,
        "sponsor_size": "mid",
        "text": (
            "ObesiCure Bio contracted Meridian CRO for a Phase II dose-ranging study of OCB-12, a "
            "GLP-1 agonist/amylin analog combination in adults with BMI ≥30. Three hundred and twenty "
            "patients enrolled at 24 US obesity medicine centers. The study required standardized "
            "meal tolerance tests, DEXA body composition scans, and patient-reported satiety diaries.\n\n"
            "Meridian's site qualification emphasized obesity medicine specialty certification and "
            "DEXA equipment calibration verification. ePRO satiety diary data completeness: 95%.\n\n"
            "Outcome: WON — Dose-response established. ObesiCure advanced to Phase III with Meridian "
            "as preferred CRO, citing expertise in obesity medicine site networks and metabolic "
            "endpoint management."
        ),
    },
    {
        "id": "prop_035",
        "therapeutic_area": "metabolic",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "ongoing",
        "year": 2024,
        "sponsor_size": "large",
        "text": (
            "LiverStrat Pharma selected Meridian CRO for a Phase III study of LSP-200, a FXR/TGR5 "
            "dual agonist in MASH with F2–F3 fibrosis. Nine hundred and fifty patients at 80 global "
            "sites. Primary endpoints: fibrosis improvement ≥1 stage without worsening MASH, and "
            "MASH resolution without worsening fibrosis.\n\n"
            "The study requires central liver biopsy histopathology review — Meridian manages biopsy "
            "logistics and a 5-member central pathology panel. A high screen failure rate (~45%) "
            "prompted Meridian to deploy a site coaching program to improve eligibility screening.\n\n"
            "Outcome: ONGOING — 30% enrolled as of Q1 2024. Adaptive screen failure mitigation "
            "reducing screen failure to 38% in the most recent enrollment cohort."
        ),
    },
    {
        "id": "prop_036",
        "therapeutic_area": "metabolic",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "europe",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "mid",
        "text": (
            "ImmunoSugar Bio engaged Meridian CRO's EU operations for a Phase II immunomodulation "
            "study of ISB-5, targeting beta-cell function preservation in newly diagnosed Type 1 "
            "diabetes (pediatric, age 8–17). One hundred and twenty patients enrolled at 18 EU "
            "academic pediatric diabetes centers.\n\n"
            "Mixed meal tolerance test and C-peptide central lab processing required standardized "
            "protocols across EU labs. Meridian's pediatric eCOA platform was adapted for patient "
            "and parent diaries in 5 languages.\n\n"
            "Outcome: WON — Meaningful C-peptide preservation in the treatment arm; EU Pediatric "
            "Investigation Plan (PIP) granted. Highlighted at ADA as a best-in-class pediatric "
            "trial design. Phase III agreement awarded."
        ),
    },
    {
        "id": "prop_037",
        "therapeutic_area": "metabolic",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "asia_pacific",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "mid",
        "text": (
            "PharmaGout Asia retained Meridian CRO's APAC team for a Phase III study of PGA-9, a "
            "selective xanthine oxidase inhibitor in gout with cardiovascular risk factors. Seven "
            "hundred patients enrolled across 40 APAC sites (Japan, China, South Korea, Thailand, "
            "Singapore). The study required standardized serum urate measurements with central "
            "laboratory processing.\n\n"
            "PMDA consultations for Japan-specific data requirements were led by Meridian APAC's "
            "Japan-qualified regulatory team, coordinating country-specific dosing schedule "
            "adjustments based on PK bridging requirements.\n\n"
            "Outcome: WON — Study met primary endpoint (proportion achieving sUA <6 mg/dL); PMDA "
            "submission accepted. Meridian APAC regulatory team credited for the Japan-specific "
            "data package quality."
        ),
    },
    {
        "id": "prop_038",
        "therapeutic_area": "metabolic",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2021,
        "sponsor_size": "mid",
        "text": (
            "TransTTR Pharma engaged Meridian CRO for a Phase II study of TTP-8, an RNAi agent "
            "targeting TTR in ATTR wild-type amyloidosis with cardiomyopathy. Ninety patients enrolled "
            "at 15 US and 10 EU centers. The study required serial cardiac MRI for extracellular "
            "volume quantification and 99mTc-PYP scintigraphy — 4 imaging modalities per patient.\n\n"
            "Meridian developed a multimodal cardiac imaging logistics protocol managing scheduling, "
            "transport, and central reading from a single operations hub.\n\n"
            "Outcome: WON — Cardiac biomarker signals supported a Phase III go decision. Study cited "
            "as a methodological model for multimodal cardiovascular endpoints in amyloidosis at "
            "Heart Failure Society of America."
        ),
    },

    # ── Respiratory (5) ───────────────────────────────────────────────────────
    {
        "id": "prop_039",
        "therapeutic_area": "respiratory",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "large",
        "text": (
            "AirPath Therapeutics selected Meridian CRO for a Phase III study of APT-500, a triple "
            "combination inhaler (ICS/LABA/LAMA) in symptomatic COPD (GOLD Grade 2–3). Two thousand "
            "two hundred patients enrolled at 160 global sites (US, EU, Latin America). Primary "
            "endpoints: trough FEV1 at Week 24 and COPD exacerbation rate.\n\n"
            "Meridian managed centralized spirometry quality review with a designated respiratory "
            "physiologist reviewing all flagged maneuvers. The program resulted in <4% unusable "
            "assessments vs. the industry average of ~12%.\n\n"
            "Outcome: WON — Primary endpoints met; NDA/MAA submitted. Meridian's spirometry quality "
            "program cited in the FDA statistical review as a significant contributor to the "
            "robustness of the FEV1 dataset."
        ),
    },
    {
        "id": "prop_040",
        "therapeutic_area": "respiratory",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "europe",
        "outcome": "won",
        "year": 2021,
        "sponsor_size": "mid",
        "text": (
            "BioAsthma EU contracted Meridian CRO's EU operations for a Phase II study of BAE-3, an "
            "anti-IL-5 biologic in eosinophilic asthma (blood eosinophils ≥300/µL). Two hundred and "
            "forty patients enrolled at 30 EU sites. Central blood eosinophil counting standardization "
            "required Meridian to align 6 central labs across EU on a single validated counting "
            "protocol.\n\n"
            "The study utilized an eDiary for daily symptom scores and rescue SABA use. Meridian's "
            "eDiary platform achieved >96% data completeness across 24 weeks.\n\n"
            "Outcome: WON — Dose-dependent eosinophil reduction and symptom improvement confirmed. "
            "EU Phase III full-service agreement awarded on strength of Phase II execution."
        ),
    },
    {
        "id": "prop_041",
        "therapeutic_area": "respiratory",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "lost",
        "year": 2023,
        "sponsor_size": "large",
        "text": (
            "FibroLung Sciences evaluated Meridian for a Phase III study of FLS-11, an anti-fibrotic "
            "in idiopathic pulmonary fibrosis (IPF) with FVC decline as the primary endpoint. "
            "Four hundred patients at IPF specialist centers globally.\n\n"
            "Meridian was not selected due to a perceived gap in IPF-specific site experience and "
            "concerns about Meridian's pulmonary function testing QA program for the FVC endpoint. "
            "The winning CRO had 40 pre-qualified IPF centers and established relationships with "
            "IPF clinical trial working groups.\n\n"
            "Outcome: LOST — Key lesson: invest in IPF specialist site network and a dedicated "
            "pulmonary function testing QA program with ATS/ERS-certified spirometry reviewers."
        ),
    },
    {
        "id": "prop_042",
        "therapeutic_area": "respiratory",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "mid",
        "text": (
            "ModuCF Solutions engaged Meridian CRO for a Phase II study of MCS-6, a novel CFTR "
            "corrector in CF patients with rare gating mutations. Eighty patients enrolled at 20 US "
            "and 10 EU CF Foundation-accredited centers. Meridian's pre-established CF site network "
            "reduced site activation time by 4 weeks vs. a cold-start.\n\n"
            "Sweat chloride testing protocol was standardized across all sites with central quality "
            "review by a dedicated CF physiologist. Spirometry QA was adapted for the "
            "pediatric/adult CF population.\n\n"
            "Outcome: WON — Statistically significant sweat chloride reduction; IND expansion "
            "approved by FDA. ModuCF named Meridian a preferred CRO partner for all future CFTR "
            "modulator development programs."
        ),
    },
    {
        "id": "prop_043",
        "therapeutic_area": "respiratory",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "small",
        "text": (
            "PulmoVex Bio contracted Meridian CRO for a Phase II study of PVB-2, a soluble guanylate "
            "cyclase stimulator in pulmonary arterial hypertension (PAH, WHO Functional Class II–III). "
            "One hundred and twenty patients enrolled at 20 US and 8 EU PAH expert centers.\n\n"
            "The primary endpoint — 6-minute walk distance — required Meridian to implement a "
            "standardized 6MWT corridor protocol and blinded assessor certification. Right heart "
            "catheterization at baseline and Week 24 was conducted at PH expert centers under "
            "Meridian monitoring, with a central hemodynamic data review board.\n\n"
            "Outcome: WON — 6MWT improvement met the pre-specified threshold. Meridian's regulatory "
            "team successfully supported FDA Breakthrough Therapy Designation, which was granted."
        ),
    },

    # ── Immunology / Rheumatology (5) ─────────────────────────────────────────
    {
        "id": "prop_044",
        "therapeutic_area": "immunology",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2023,
        "sponsor_size": "large",
        "text": (
            "RheumaVance Pharma selected Meridian CRO for a Phase III study of RVP-10, a selective "
            "JAK1/2 inhibitor in rheumatoid arthritis with inadequate MTX response. Nine hundred "
            "patients enrolled at 80 global sites. Primary endpoints: ACR50 at Week 12 and HAQ-DI "
            "change at Week 24. The study included a cardiovascular risk sub-study with adjudicated "
            "MACE events.\n\n"
            "Meridian's immunology CRA team had >80% prior RA trial experience; site productivity "
            "metrics significantly exceeded Phase III RA industry benchmarks.\n\n"
            "Outcome: WON — Both co-primary endpoints met; NDA filed. RheumaVance cited Meridian's "
            "RA-experienced CRA team as the single most important differentiator. Follow-on Phase IIIb "
            "extension study awarded."
        ),
    },
    {
        "id": "prop_045",
        "therapeutic_area": "immunology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "europe",
        "outcome": "won",
        "year": 2021,
        "sponsor_size": "mid",
        "text": (
            "SkinClear EU selected Meridian CRO's EU team for a Phase II dose-ranging study of SCE-7, "
            "an anti-IL-17A/F bispecific in moderate-to-severe plaque psoriasis. Two hundred and "
            "eighty patients enrolled at 30 EU dermatology centers. The primary endpoint — PASI 90 "
            "at Week 16 — required central photography with a panel of independent assessors for "
            "blinded PASI scoring.\n\n"
            "Meridian's central photography platform and PASI training program achieved a >95% "
            "photograph acceptability rate. A 5-member independent dermatologist panel performed "
            "all central PASI reads.\n\n"
            "Outcome: WON — PASI 90 dose response confirmed. EU Phase III expansion awarded. "
            "SkinClear cited Meridian's central PASI photography program as a model they will "
            "require in all future dermatology studies."
        ),
    },
    {
        "id": "prop_046",
        "therapeutic_area": "immunology",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "large",
        "text": (
            "AtopyRx Inc. retained Meridian CRO for a Phase III study of ARX-18, an IL-4Rα antagonist "
            "in moderate-to-severe atopic dermatitis. Seven hundred and fifty patients enrolled at "
            "65 US and EU dermatology centers. Primary endpoints: IGA 0/1 and EASI-75 at Week 16.\n\n"
            "The patient population included a significant proportion with skin of color. Meridian "
            "implemented specific photographic standardization protocols (lighting, angle, calibration "
            "scale) to ensure accurate IGA and EASI assessment across all skin tones.\n\n"
            "Outcome: WON — Both primary endpoints met; FDA approved. Meridian's photographic "
            "standardization methodology for skin of color was recognized in a journal correspondence "
            "by the principal investigators as an industry-advancing practice."
        ),
    },
    {
        "id": "prop_047",
        "therapeutic_area": "immunology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2023,
        "sponsor_size": "mid",
        "text": (
            "LupusMed Bio contracted Meridian CRO for a Phase II study of LMB-4, an anti-IFNAR1 "
            "antibody in active systemic lupus erythematosus (SLEDAI ≥6). Two hundred and twenty "
            "patients enrolled at 30 US and 15 EU sites. Complex eligibility criteria required "
            "intensive site training and a dedicated eligibility confirmation process.\n\n"
            "Meridian developed a pre-screening eligibility checklist reviewed by the medical monitor "
            "for each patient before randomization. Screen failure rate: 28% vs. sponsor projection "
            "of 42% — saving approximately $800K in operational costs.\n\n"
            "Outcome: WON — SLEDAI response rate significantly exceeded placebo; Phase III initiated. "
            "The screen failure improvement methodology adopted as standard in Meridian's immunology "
            "franchise."
        ),
    },
    {
        "id": "prop_048",
        "therapeutic_area": "immunology",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "europe",
        "outcome": "ongoing",
        "year": 2024,
        "sponsor_size": "mid",
        "text": (
            "GutImmune Partners retained Meridian CRO for a Phase II study of GIP-6, an anti-TL1A "
            "antibody in moderate-to-severe Crohn's disease. Three hundred patients enrolled at "
            "45 EU sites. Primary endpoint: clinical remission (CDAI <150) at Week 12. Central "
            "ileocolonoscopy reading by a GI core lab manages central endoscopy adjudication.\n\n"
            "Meridian's EU IBD site network includes 20 dedicated IBD centers of excellence. "
            "An endoscopy sub-study capturing SES-CD scores at baseline and Week 12 requires "
            "central video adjudication by 3 independent GI endoscopists.\n\n"
            "Outcome: ONGOING — 50% enrolled as of Q2 2024; endoscopy sub-study progressing on "
            "schedule. Interim futility analysis planned Q1 2025."
        ),
    },

    # ── Infectious Disease (2) ────────────────────────────────────────────────
    {
        "id": "prop_049",
        "therapeutic_area": "infectious_disease",
        "phase": "Phase III",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "large",
        "text": (
            "VaxShield Bio selected Meridian CRO for a Phase III efficacy study of VSB-7, an RSV "
            "prefusion F protein vaccine in adults aged ≥60. Twenty-two thousand patients in a "
            "randomized placebo-controlled design across 2 RSV seasons at 120 global sites (US, EU, "
            "Latin America, South Africa). The study required a central RSV surveillance laboratory "
            "network for RT-PCR confirmation and serology testing across 6 continents.\n\n"
            "Meridian's global lab logistics team coordinated cold-chain sample transport from "
            "120 sites with a <0.1% sample compromise rate — the largest single study Meridian has "
            "managed, establishing a global infectious disease trial infrastructure.\n\n"
            "Outcome: WON — Vaccine efficacy established; NDA/BLA filed. Meridian recognized with "
            "a Sponsor Recognition Award from VaxShield for operational excellence."
        ),
    },
    {
        "id": "prop_050",
        "therapeutic_area": "infectious_disease",
        "phase": "Phase II",
        "service_type": "full_service",
        "geography": "global",
        "outcome": "won",
        "year": 2022,
        "sponsor_size": "mid",
        "text": (
            "LongActRx contracted Meridian CRO for a Phase II study of LAR-5, a long-acting integrase "
            "inhibitor/CCR5 antagonist combination administered every 2 months (IM injection) in "
            "virologically suppressed HIV+ adults. Two hundred patients enrolled at 10 US HIV "
            "treatment centers and 5 sub-Saharan Africa sites.\n\n"
            "The Africa sites required Meridian to manage import/export licensing across 3 countries "
            "and facilitate community advisory board engagement. Cold-chain distribution for the "
            "temperature-sensitive IM formulation was managed by Meridian's Africa depot partner.\n\n"
            "Outcome: WON — Virologic non-inferiority demonstrated vs. standard-of-care oral "
            "regimen. Phase III global agreement in negotiation. Meridian's Africa operational "
            "capability cited as a unique differentiator vs. all competing CROs in this RFP."
        ),
    },
]

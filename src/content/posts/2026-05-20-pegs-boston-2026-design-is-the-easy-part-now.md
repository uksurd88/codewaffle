---
title: "PEGS Boston 2026: Design Is the Easy Part Now"
description: "Five days at PEGS Boston. The design question is mostly answered. The hard problems have moved to CMC tolerance and immune acceptance, and the field knows it."
date: 2026-05-20
categories: ["Science", "Antibody Engineering", "Industry"]
tags: []
authors: ["Sukhi Singh"]
draft: false
---

Three years ago the big question at PEGS was whether AI could design antibody binders at all. This year nobody asked that.

The question has shifted: can the system design something a CMC team will tolerate, and something a patient's immune system will accept? Those are harder questions, and the field is only beginning to have ground truth for them.

I spent five days in Boston at PEGS 2026 running Booth 310 with the ENPICOM team. Here is what I keep coming back to.

## Design is no longer the bottleneck

Chai Discovery's Ryan Peckner and Paul Wollenhaupt showed data I will be thinking about for a while. Fifteen therapeutic targets, VHH and VHL designs, binders found for 14 of 15. Cryo-EM validation on five designs with RMSD of 0.4 to 1.7 Å between the in silico prediction and the experimental structure. CDR loops within 0.3 Å. The sequences are 11 to 26 mutations away from anything in PDB. These are not retrievals or near-matches. They are genuinely new structures.

The developability data was the part I needed to see. They reformatted VHH designs as full IgGs and benchmarked against approved biologics on yield, thermostability, size dispersity, specificity, and hydrophobicity. About 85 percent of designs landed in the therapeutic zone on three or more of those properties. Trastuzumab as the green-zone reference, cetuximab as the red-zone one, Chai designs sitting roughly where humanised therapeutics sit.

Ryan was direct about the immunogenicity question: no de novo biologic has reached clinic yet, so there is no clinical ground truth. The in silico framing is honest. They scored designs on a foreignness-times-display metric against OAS and netMHC class II predictions, and the distribution sits to the left of fully human therapeutics. It is a prior, not a proof.

Rohith Krishna from the Baker lab put a wider frame on it. The talk was technically about RFdiffusion plus ProteinMPNN plus RF3 composability, but the observation that stuck was simpler: these tools are shipping as primitives. Other groups will combine them in ways the original designers could not have imagined. Custom enzymes designed from scratch, compact sequence-specific DNA binders at single-digit nanomolar, glycan-display proteins with steric shielding against mannosidases. Things you could not have attempted two years ago are now a planning conversation at a lab meeting.

## Training data composition is the actual differentiator

Norbert Furtmann (Sanofi) gave the talk I came for. His Biologics AI and Design team went from three million internal nanobody sequences pre-2025 to over one billion now, across more than 30 NGS campaigns including naive llama repertoires sampled pre-immunisation. That corpus underlies their Sanofi-PLM, a continued-training ESM variant that beats both general protein language models and VHH-specific public models on real downstream tasks.

The uncomfortable finding for the broader field: public VHH-specific models underperform public antibody-general models on real tasks. Academic nanobody communities have put energy into building specialist architectures, and the data gap underneath is what limits them.

His evaluation methodology is worth adopting regardless. Family-based leave-one-out splits rather than random splits. Random splits leak parent-mutant pairs across train and test, which inflates every metric and hides generalization failures. This is not a minor technical note. It is the reason half the published benchmarks in this space are misleading.

Victor Greiff from Oslo said it plainly on Friday: architecture is what gets the press release, training data composition is what determines whether the model works on the target you actually care about. That line belongs in every conversation about AI antibody platform credibility.

## Immunogenicity: what the field can honestly claim

Will Thrift's talk at Genentech was a model of appropriate calibration. Genentech has a curated dataset of about 100 monoclonal antibodies with clinical ADA incidence, and he now has a model combining T-cell epitope filtering with B-cell patch prediction. The architecture is a LoRA-fine-tuned SaProt embedding fed into a GNN head with adjacent-residue smoothing, predicting risky residues and aggregating them into patches.

Results on his held-out set: T-cell filtering alone removes most high-ADA antibodies. B-cell patch counting catches five of the seven that slip through. He was direct about the small-data problem. Training on 100 antibodies with clinical ADA data, even carefully curated, leaves genuine uncertainty about whether you are optimizing for how your labels were labelled rather than the underlying biology.

The honest status of the field: T-cell epitope mapping is genuinely useful and should be in every pipeline. B-cell prediction is improving fast. Self/non-self patch filtering is still open. No de novo biologic has reached clinic, so all of this is built on inferred ground truth for the class. The groups doing this work are being appropriately honest about it, which is progress in itself.

## Lab-in-the-loop is a specific operating model, not a phrase

The phrase came up in almost every session, and by Wednesday it had stopped meaning anything. But there is a concrete model underneath it.

Foundation-model-based design at the front generates candidate sequences at a cost and speed that makes thousands of variants viable. An automated developability panel in the middle (yield, thermostability, size dispersity, specificity, hydrophobicity, charge, roughly the Adimab 2017 thresholds) filters down without a scientist in the loop for every candidate. Immunogenicity scoring happens at the residue level, not as a downstream afterthought. Then the wet-lab loop closes with kinetics data that feeds back into the next design cycle.

Andrew Dippel's (AstraZeneca) numbers on developability automation made the middle layer concrete: from 200 samples per week with hands-on time throughout, to 800 per week with 15 minutes of human input per run. The bottleneck is not throughput. It is the data layer underneath. His framing: you can build a beautiful automated workflow and then manually copy data out of it. Physical and digital both need solving.

## What the data layer has to be

The groups doing this well share one thing: the data model was built before the model. Sequence and modification context as first-class fields, not spreadsheet columns. FAIR capture at every step so that an agent, a model, or a new hire can ask a question without reconstructing context from scratch.

Most of the interesting talks this week lived downstream of that foundation. Chai, Nabla, Sanofi, Genentech: all using a specialised structure-prediction model, generating sequences with diffusion or MPNN-style approaches, filtering on developability and immunogenicity. The differentiation is increasingly about three things: the dataset you train and evaluate on, the wet-lab loop you run, and the integration that makes all of it visible in one project view.

None of those are commodities. All of them depend on what the data layer looked like before anyone trained a model.

The week in one sentence: the field is consolidating around lab-in-the-loop as the dominant operating model, the technical risk has shifted from "can the model design a binder" to "can it design something CMC-tolerant and immune-system-tolerant," and the answer to both is now mostly yes, with honest asterisks.

Working in antibody engineering or repertoire analytics? I'd be interested to hear what your data layer looks like in practice. Reach out or explore what ENPICOM's IGX Platform can do for your team at [enpicom.com](https://enpicom.com).

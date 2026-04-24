---
title: "VHH Humanization Is Mostly a Search Problem, Not a Grafting Problem"
description: "Everyone frames nanobody humanization as CDR grafting. It's not. It's a search problem with a brutal fitness landscape."
date: 2026-04-24
categories: ["Science", "Antibody Engineering"]
tags: []
authors: ["Sukhi Singh"]
draft: false
---

Everyone frames nanobody humanization as CDR grafting. It's not. It's a search problem with a brutal fitness landscape.

The llama gives you a single-domain binder that folds, expresses, and hits picomolar affinity. Then you have to convince a human immune system it's family. Swap too few framework residues and ADA risk stays high. Swap too many and you lose the binder entirely. Somewhere in that combinatorial space is a variant that keeps the paratope geometry and passes T-cell epitope screens. Finding it is the whole game.

## The classical pipeline is a bottleneck

The textbook workflow: align your VHH to the closest human IGHV germline (usually IGHV3-23 or IGHV3-66), identify framework divergences, graft CDRs onto the human scaffold, then rescue affinity with back-mutations at Vernier zone and VH-VL interface positions. Except there's no VL. That's the whole point of a VHH. So the Vernier logic borrowed from classical antibody humanization doesn't map cleanly.

What you're really doing is preserving the hallmark residues at positions 37, 44, 45, and 47 that stabilize the solvent-exposed former VL interface. Mutate those wrong and the domain aggregates. Keep them llama-like and MHC-II peptides there light up every in silico immunogenicity predictor you run.

So teams iterate. Build 20 variants, express them, measure binding by SPR, run NetMHCIIpan or EpiMatrix on the sequences, pick the Pareto front. It works. It's also slow and expensive.

## Where ML is actually changing things

The interesting shift isn't a new grafting algorithm. It's that sequence-based protein language models now give you a prior over "human-like" without an explicit germline alignment. AbLang, Sapiens, IgBert, and the nanobody-specific NanoBERT variants score sequences by how likely they are to appear in a human repertoire. You can use that as a loss term during in silico maturation alongside a binder-fitness term.

Pair that with ESM or AlphaFold-based structural constraints to keep the CDR loop conformations stable, and suddenly humanization becomes a directed search in latent space rather than a residue-by-residue decision tree. Groups at Adimab, Absci, and several academic labs have published variants of this. The results are real: fewer rounds, better affinity retention, lower predicted immunogenicity.

What's still missing is clinical validation. In silico T-cell epitope scores correlate with ADA only loosely. The only thing that actually tells you a humanized VHH won't trigger immunogenicity is a human PBMC assay or, eventually, patients. Every pipeline I've seen overweights the computational score because the wet-lab score is expensive and slow.

## The data problem underneath it all

Every humanization model is only as good as the repertoire data behind it. Public human VH datasets are dominated by peripheral blood from healthy adults. That's a narrow slice. Bone marrow plasma cell repertoires, mucosal tissue B cells, disease-state repertoires: all underrepresented. If your "human-likeness" prior is trained on healthy blood, you're optimizing for a specific compartment, not human-ness.

This is where repertoire sequencing platforms matter. Not because they run the humanization, but because they define what human even means as a reference.

## My take

The VHH humanization pipelines I'd bet on combine three things: a language-model prior trained on deep, diverse human repertoires; structure-aware CDR grafting with explicit preservation of the hallmark framework residues; and early, cheap immunogenicity triage before you commit to expression. The grafting step is almost a solved problem. The search strategy and the reference data are where the quality differential lives.

Working on something similar? I'd love to hear about it, or explore what ENPICOM's IGX Platform can do for your team at [enpicom.com](https://enpicom.com)
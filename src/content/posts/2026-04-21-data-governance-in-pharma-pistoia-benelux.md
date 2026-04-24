---
title: "Data Governance in Pharma: Notes from the Pistoia Alliance Benelux Forum #5"
meta_title: "Data Governance in Pharma - Pistoia Alliance Benelux Forum"
description: "A speaker-by-speaker recap of the European Life Science Informatics Forum Benelux #5 at GSK Wavre: data governance, FAIR, and agentic AI in drug discovery."
date: 2026-04-21T10:00:00Z
image: ""
categories: ["pharma", "ai"]
authors: ["Sukhi Singh"]
tags: ["data-governance", "fair", "pistoia-alliance", "agentic-ai", "drug-discovery", "bioinformatics"]
draft: false
---

Yesterday I had the privilege of attending, and speaking at, the fifth edition of the **European Life Science Informatics Forum Benelux**, a [Pistoia Alliance](https://www.pistoiaalliance.org/) event hosted at [GSK](https://www.gsk.com/) Wavre. The focus area was **Data Governance in Pharma: Navigating the Digital & AI Revolution**, with morning talks, a lightning Q&A, and four World Café breakouts in the afternoon. Outputs will feed a Pistoia Alliance publication and the Life Science AI Exchange webinar series.

Here is a speaker-by-speaker summary of what we covered.

## Opening

**Cristina Fasca** (Consultant, Pistoia Alliance) set the tone, framing data governance not as a compliance burden but as the foundational capability that makes AI in pharma trustworthy and sustainable.

**Quentin Grignet** (Head of Master Data Strategy & Analytics, GSK) welcomed attendees and posed the day's central question: how do organisations govern data at scale when AI is reshaping every assumption we have made about workflows, roles, and accountability?

## The Expert Perspective

**Jan Henderyckx** (President Council Liaison, [DAMA](https://www.dama.org/)) opened with a crisp conceptual framework: **humans set the *why*, machines execute the *how***. He introduced four personas every data governance operating system needs:

- **Meaning maker**, sets semantics, context, norms
- **Accountability actor**, owns decisions and outcomes
- **Intent setter**, defines value and boundaries for automation
- **Human in the loop**, provides final oversight, ethics, and judgement

He argued that semantic layers and *active* metadata are not optional, they are the backbone of any AI-ready data strategy. His warning: without runtime observability baked in from the start, agentic systems will fail in the same way early GPS systems did (confident, fast, and occasionally driving into canals). Jan also facilitated the afternoon's Lightning Talks Q&A and the *Human in the Loop* World Café breakout.

## The Pharma Perspective

**Maxine Fletcher & Quentin Grignet** (GSK) laid out GSK's data quality management system: documented business rules (critical for GxP data), a data quality management plan with error classification and SLAs, a live KPI dashboard, and a DevOps-based ticketing system that routes errors automatically to the last person who touched a record, with a countdown to fix it.

Quentin then showed where AI enters the picture. GSK's **AI Data Stewardship programme** adds an agent that reads the ticket queue, queries an internal ontology, formulates its own database queries, retrieves regulatory documents (including SMPC sections), and appends a proposed resolution with sources and a confidence score back to the ticket. The human steward reviews, overrides if needed, and the agent learns. The framing: AI as **co-pilot**, not replacement. Preserving entry-level roles was a deliberate choice, cutting them destroys the pipeline for future domain expertise.

**Sophie Ollivier** (Chief Data Officer, R&D Data Office, [SERVIER](https://www.servier.com/)) shared Servier's seven-year digital transformation, starting from a 2019 R&D Data Office and moving through data catalogues, a global cloud data platform, and a structured AI governance layer. Key milestones:

- Internal data accessible in the platform: **30% -> 65%** (target >90% by end of 2028)
- Active AI use cases across the R&D lifecycle: **doubled**
- [EU AI Act](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai) compliance layer added in 2025
- New secure internal GPT deployed, agentic tools expanding

Next on the roadmap: advancing toward a full [FAIR](https://www.go-fair.org/fair-principles/) implementation, ICH regulatory system alignment, and compliance with the [European Health Data Space](https://health.ec.europa.eu/ehealth-digital-health-and-care/european-health-data-space_en) regulation.

**Luiza Gabriel** (Director, Data Products & Data Strategy, Global Development, [Johnson & Johnson](https://www.jnj.com/)) brought the data science lens. The central challenge at J&J: data scientists could not reliably answer "which data should I use?" internally or externally. Her team's answer: a fit-for-purpose **data product strategy**, built in close collaboration with data governance, data quality, MDM, and data management teams. No two data products are identical because the consumption context always differs. The horizontal team's job is to define what exists, where it is, and under what conditions it can be used for AI/ML, dashboards, and predictive modelling.

## The Consulting Perspective

**Lars Juhl Jensen** (Director, [ZS Associates](https://www.zs.com/)) gave the day's most technical, and most honest, talk: a case study on **network embedding-based disease-protein prioritisation** using the [STRING database](https://string-db.org/). The approach combines omics data with protein interaction networks, generates 64-dimensional embeddings, and applies logistic regression to rank candidate proteins per disease, achieving roughly **double the recall** at 5% false positive rate compared to omics integration alone.

When he tried to apply this systematically using a client's internal, "standardised and centralised" omics infrastructure, he hit what he called **"Schrödinger's metadata"**: metadata that simultaneously exists and does not. Annotations had been made at the project level, not the sample level, meaning disease labels were wrong, and the data was effectively unretrievable without manual LLM-assisted extraction.

> "You only find out if you have AI-ready data if you try to actually solve an AI task with your data."

His prescription: run a small proof-of-concept on a real task. Do not wait until you think the foundation is perfect. The gaps reveal themselves only under real use.

## The Supply-Side Perspective

I spoke about how [ENPICOM](https://www.enpicom.com/) approaches [FAIR principles](https://www.go-fair.org/fair-principles/) and data governance within our SaaS platform for early biologics and antibody discovery. Scientists upload millions of sequences, run clustering and machine learning, and work down to a candidate shortlist, but the data governance challenges start well before that.

Three core problems we see repeatedly:

- **Metadata lag**: instrument data arrives first, metadata follows on day three by email or in a spreadsheet
- **No shared language**: IgG1, IG-1, Immunoglobulin 1, identical to a human, invisible to a machine
- **FAIR in name only**: CDO mandates guidelines, by the time they reach the bench scientist, FAIR is an abstract concept with no practical implementation

Our answer is **FAIR by design**: no data ingestion without metadata, persistent URIs for all objects, ontology-aligned terminology, governance controls delegated to power users, and full ML model provenance from training to deployment.

Looking ahead, the future is agentic. Platforms like ours need to become the **guardrails**, embedding data governance directly into APIs and MCP servers so that agents operate within the same rules as human users, with identity tracking for each agent and full audit trails on every run.

**Sara Velkovska** (Product Director) and **Lieven Poelman** (VP Engineering, [Ontoforce](https://www.ontoforce.com/)) demonstrated what **governance-in-the-semantic-layer** looks like in production, using a real client case involving sensitive patient-level data. The challenge: secondary reuse of clinical data is scientifically valuable but legally constrained by individual patient consent. Their architecture:

- **Protected concepts**: consent and access rules are baked into the ontology layer, not the source data, so governance follows the concept, not the schema, even as data sources evolve
- **Settable threshold**: any result set below a configurable minimum (e.g. 10 patients) is automatically suppressed to prevent re-identification of rare-disease cohorts
- **MCP server**: applies identical access rules to human users, LLMs, and autonomous agents, so connecting Claude or ChatGPT Enterprise to their API inherits all governance logic automatically

> "You cannot write a legally binding NDA with an AI agent. Governance has to be baked into the semantic layer from day one."

Researchers, and agents, still see that a cohort exists and why access is restricted, so they can navigate the system rather than around it.

## Afternoon: World Café Breakout Sessions

After lunch, attendees split into four facilitated breakout groups, each producing input for a forthcoming Pistoia Alliance publication and the Life Science AI Exchange webinar series.

| Group | Topic | Facilitator |
|------|-------|-------------|
| 1 | **Data Governance** | Quentin Grignet (GSK) |
| 2 | **Data Quality** | Bert Torfs (J&J Innovative Medicine) |
| 3 | **Making Data AI Ready** | Laura Van Haute (UCB) |
| 4 | **Human in the Loop** | Jan Henderyckx (DAMA) |

Key threads from the room: the EU AI Act is clear on *what* is required but silent on *how*, leaving industry to shape compliance frameworks together. GxP validation for agentic systems remains an open question. And the consensus on data foundations: **the principles have not changed, the technology has**. Build and deliver in parallel, do not wait for a perfect foundation before showing value.

## The Thread Running Through the Day

> Governance is not a brake on AI, it is what makes AI in pharma sustainable. The organisations getting this right are treating data quality and metadata as a **product**, not a compliance checkbox.

Thank you to **Cristina Fasca**, **John Wise**, and the full Pistoia Alliance steering committee for a genuinely rich day of conversation. And to GSK Wavre for the hospitality.

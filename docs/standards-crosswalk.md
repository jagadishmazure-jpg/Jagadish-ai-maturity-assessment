# Standards crosswalk

Every capability of the Enterprise Agentic AI Maturity Model mapped to NIST AI RMF (functions and categories), ISO/IEC 42001 (clauses and Annex A controls) and the EU AI Act (articles). The source of truth is the `maps_to` field in `framework/framework.yaml`; a test keeps this table in step with it.

The mapping is for orientation: it shows which part of each standard a capability helps evidence. A high level is not a conformity claim.

## SV Strategy & Value

| Capability | NIST AI RMF | ISO/IEC 42001 | EU AI Act |
|---|---|---|---|
| SV-1 Agentic AI Thesis | GOVERN 1, MAP 1 | 4.1, 5.2, 6.2 | no direct article |
| SV-2 Use-Case Portfolio & Prioritisation | MAP 1, MAP 3 | 6.1, 6.2, A.6 | no direct article |
| SV-3 Value Realisation | MAP 3, MEASURE 1, MANAGE 2 | 9.1 | no direct article |

## DF Data Foundation

| Capability | NIST AI RMF | ISO/IEC 42001 | EU AI Act |
|---|---|---|---|
| DF-1 Knowledge & Grounding Sources | MAP 2, MAP 4 | A.7 | Art. 10 |
| DF-2 Data Quality & Contracts | MEASURE 2, MANAGE 4 | A.7 | Art. 10 |
| DF-3 Governed Access & Synthetic Data | GOVERN 1, MANAGE 1 | A.7, A.4 | Art. 10 |

## PL Platform & LLMOps

| Capability | NIST AI RMF | ISO/IEC 42001 | EU AI Act |
|---|---|---|---|
| PL-1 Paved-Road Engineering Platform | MANAGE 2 | A.4, A.6 | Art. 15 |
| PL-2 Release & Lifecycle Automation | MANAGE 1, MANAGE 4 | 8.1, A.6 | Art. 17 |
| PL-3 Observability & Runtime Operations | MEASURE 3, MEASURE 4, MANAGE 4 | 9.1, A.6 | Art. 12, Art. 72 |

## AE Agent Engineering

| Capability | NIST AI RMF | ISO/IEC 42001 | EU AI Act |
|---|---|---|---|
| AE-1 Evaluation & Quality Gates | MEASURE 1, MEASURE 2 | 9.1, A.6 | Art. 15 |
| AE-2 Tool & Interoperability Design | MAP 4, GOVERN 6 | A.10, A.6 | Art. 15 |
| AE-3 Autonomy & Human Oversight | GOVERN 2, MANAGE 2 | A.9, A.6 | Art. 12, Art. 14 |

## SI Security & Identity

| Capability | NIST AI RMF | ISO/IEC 42001 | EU AI Act |
|---|---|---|---|
| SI-1 Agent Identity & Secrets | GOVERN 1, MANAGE 1 | A.4, A.6 | Art. 15 |
| SI-2 AI Threat Defence | MEASURE 2, MANAGE 4 | 8.2, A.6 | Art. 15 |
| SI-3 Supply Chain & Platform Hardening | GOVERN 6, MANAGE 3 | A.10, A.6 | Art. 15 |

## GR Governance, Risk & Compliance

| Capability | NIST AI RMF | ISO/IEC 42001 | EU AI Act |
|---|---|---|---|
| GR-1 AI Policy & Accountability | GOVERN 1, GOVERN 2, GOVERN 4 | 5.2, 5.3, A.2, A.3 | Art. 17, Art. 26 |
| GR-2 Risk & Impact Management | MAP 5, MEASURE 2, MANAGE 1 | 6.1, 8.2, 8.4, A.5 | Art. 9, Art. 27 |
| GR-3 Regulatory Compliance & Transparency | GOVERN 1, MEASURE 2 | 4.2, A.8 | Art. 11, Art. 13, Art. 50 |

## PO People & Operating Model

| Capability | NIST AI RMF | ISO/IEC 42001 | EU AI Act |
|---|---|---|---|
| PO-1 Sponsorship & Operating Model | GOVERN 2, GOVERN 3 | 5.1, 5.3, A.3 | no direct article |
| PO-2 Skills & AI Literacy | GOVERN 3, GOVERN 4 | 7.2, 7.3 | Art. 4 |
| PO-3 Adoption & Change | GOVERN 5, MEASURE 4 | 7.4, A.8 | no direct article |

## FC FinOps & Cost

| Capability | NIST AI RMF | ISO/IEC 42001 | EU AI Act |
|---|---|---|---|
| FC-1 Cost Guardrails | MANAGE 2 | A.4 | no direct article |
| FC-2 Unit Economics & Model Routing | MAP 3, MEASURE 1 | 9.1 | no direct article |

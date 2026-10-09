# AI Governance Risk Classification & Assessment

## Naukri.com Domain Support Agent (HR & Recruitment Track)

---

### 1. Regulatory Risk Classification: HIGH RISK

Under the European Union Artificial Intelligence Act (EU AI Act, Annex III, Section 4: *Employment, workers management and access to self-employment*) and global enterprise recruitment governance frameworks (including India's Digital Personal Data Protection Act), the **Naukri.com Domain Support Agent** is formally classified as a **High-Risk AI System**.

### 2. Governance Justification & Impact Analysis

The agent operates directly at the intersection of enterprise talent acquisition, candidate career lifecycles, and internal human resource mobility. The system performs two consequential business operations: (1) interpreting binding employment policies (including notice period durations, buyout approvals, probation confirmation criteria, and background verification mandates), and (2) evaluating candidate application tracking states and synthesizing an empirical escalation score ($S_{esc}$) that prioritizes candidate applications for urgent human HR review. Any unmitigated failure mode—such as model hallucination regarding buyout obligations, miscalculation of candidate escalation urgency, leakage of unmasked contact details, or unauthorized tool execution across autonomous agent layers—can directly prejudice a candidate's employment prospects, induce financial and contractual liability for enterprise clients, and violate statutory personal data retention mandates. Consequently, the application implements strict defense-in-depth mitigations: pre-execution token budget caps, role-based Least Autonomy tool bindings, deterministic offline Mock LLM execution, input-layer PII phone number redaction, and an independent secondary Autogen peer-review stage before any response reaches a human recruiter.

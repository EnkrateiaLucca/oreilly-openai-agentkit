# OpenAI Agent Builder — Business Use Cases: An Independent Analysis

> Research report for the O'Reilly course on OpenAI AgentKit. Focuses on the business problems Agent Builder solves and the evidence behind each claim. Workflow diagrams are included for pedagogical reference.

---

## Why Agent Builder Specifically

This is not "AI vs. no AI." The relevant question is: **Agent Builder canvas vs. writing your own agent with the Agents SDK vs. LangChain vs. n8n vs. CrewAI.** Understanding when Agent Builder wins — and when it doesn't — is the precondition for making a sensible deployment decision.

### What the canvas approach actually unlocks

**Governance as a first-class artifact.** The visual canvas is a compliance document, not just a development surface. Business analysts, legal teams, and audit functions can read and trace a workflow without reading Python. When a regulated organization must demonstrate human oversight to regulators — [EU AI Act Article 14](https://artificialintelligenceact.eu/article/14/) requires demonstrable intervention points; [Federal Reserve SR 26-02](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.pdf) (effective April 2026) now explicitly covers GenAI and agentic workflows under model risk management — a named approval node on a canvas diagram is materially different from a code comment asserting "we check this." [Deloitte's 2025 State of AI survey](https://www.deloitte.com/us/en/about/press-room/state-of-ai-report-2026.html) (3,235 business and IT leaders, 24 countries) found only **21% of companies have a mature governance model for autonomous agents**. The canvas lowers the cost of reaching that 21%.

**Integrated evaluation on the same surface.** Agent Builder's built-in eval suite — dataset-driven trace grading, automated prompt optimization based on eval outcomes — runs on the same surface where you build and deploy. LangChain's equivalent (LangSmith) is a separate paid product ($2.50–$5.00 per 1,000 traces). n8n has no native eval primitive. For teams iterating on agent quality, closing the build–eval–improve loop on one surface is a genuine productivity difference.

**ChatKit as an immediate deployment surface.** The embeddable chat widget with managed conversation threads, memory, token limits, and theming deploys in under an hour for teams already on the OpenAI stack. No alternative framework ships a comparable first-party chat UI. Self-hostable; customers pay only for tokens.

**Guardrails as modular, traceable nodes.** PII masking, jailbreak detection, moderation, and hallucination detection are configured per-node, are open-source, and appear in traces. Custom-coded systems implement safety checks ad-hoc; n8n requires assembling multiple third-party nodes; LangChain requires NeMo Guardrails or equivalent. When regulators ask "show me your safety controls," a named Guardrails node in a workflow diagram is a cleaner answer than scattered middleware.

**Speed-to-prototype for OpenAI-native teams.** For teams already on the OpenAI stack, the SDK reduces boilerplate and the prototype-to-review cycle is faster than assembling a LangChain pipeline with equivalent observability.

### The honest tradeoffs

Agent Builder trades flexibility for speed-to-governance. The costs are documented, not speculative:

- **Hard model lock-in.** Locked to OpenAI models. No Claude, Gemini, Llama, or self-hosted models. Three independent practitioners — [Humanloop](https://humanloop.com/blog/openai-agents-sdk), [Roberto Infante on Medium](https://medium.com/@roberto.g.infante/the-state-of-ai-agent-frameworks-comparing-langgraph-openai-agent-sdk-google-adk-and-aws-d3e52a497720), and an [independent AgentKit reviewer](https://medium.com/@leucopsis/openais-agentkit-review-c83bee3c3d02) — identified this as the consensus second-order risk. For enterprises with multi-vendor AI strategies, this is disqualifying.
- **No data sovereignty, no self-host.** All execution runs on OpenAI's cloud. HIPAA BAA is not currently offered for AgentKit. GDPR data residency requirements for EU data are not met. n8n self-hosted is the explicit alternative for compliance-sensitive organizations.
- **Shallow integration ecosystem in practice.** [Independent testers](https://www.finalroundai.com/blog/openai-agent-builder-what-software-developers-are-saying-after-testing) report only ~8 native integrations working reliably out-of-the-box; MCP write operations showed instability during testing. n8n has 500+ battle-tested integrations.
- **Chat-shaped, not workflow-shaped.** Agent Builder is optimized for synchronous conversational agents. It lacks first-class event triggers (cron, webhooks, queue consumers). For event-driven backend automation or durable long-running workflows, bring n8n, Temporal, or Inngest.
- **Deprecation risk.** OpenAI deprecated the Assistants API (sunset August 2026) one year after launch. [Multiple independent reviewers](https://www.finalroundai.com/blog/openai-agent-builder-what-software-developers-are-saying-after-testing) noted Agent Builder "recycles" features from that API, raising a legitimate concern about the canvas's own longevity.
- **Cost ceiling at scale.** [Real-world costs of $200–$900/month](https://createaiagent.net/openai-agent-builder-vs-n8n-ai-agent/) for non-trivial production usage. n8n self-hosted runs $10–$40/month plus model costs.

**The decision shortcut:** Choose Agent Builder when your team is OpenAI-native, building conversational/synchronous agents, and governance speed matters more than portability. Choose n8n when you need data sovereignty, event-driven triggers, or deep integration breadth. Choose LangChain/LangGraph when you need stateful multi-agent orchestration with full code control. In practice, a hybrid pattern is emerging: Agent Builder as the "cockpit" for chat and eval iteration, code-first frameworks as the "engine room" for durable execution.

---

## Business Use Cases by Problem Category

The cases below are organized by the business problem they solve, not by platform features. Each entry follows the same template: business pain with sourced evidence → why Agent Builder's specific architecture fits → evidence quality assessment → honest failure modes → workflow diagram.

---

### 1. Information Overload and Policy Fragmentation

**Business pain.** Employees in knowledge-intensive organizations spend a significant share of their time answering questions that are already answered somewhere in a policy document, HR handbook, legal brief, or internal wiki. [Thomson Reuters' 2025 survey](https://www.lawnext.com/2025/04/thomson-reuters-survey-over-95-of-legal-professionals-expect-gen-ai-to-become-central-to-workflow-within-five-years.html) of 2,200+ legal and professional services workers found active generative AI usage doubled from 14% to 26% year-over-year, primarily driven by document retrieval burdens. [McKinsey's cross-industry data](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai) shows function-level productivity improvements of **10–20% in knowledge-worker roles** where AI handles structured retrieval.

**Why Agent Builder fits.** The workflow is low-risk by design: classify question → retrieve from approved corpus → answer with cited passages → escalate unresolvable cases. There are no external writes. Guardrails protect confidentiality at the entry point. File search runs against a vetted document set. Human escalation is a named, auditable node. The entire flow is legible to non-engineers.

**Evidence quality.** Strong for the underlying pattern (knowledge retrieval + structured escalation is the most validated AI agent use case across industries). Weak for Agent Builder canvas-specific deployments in production — most named implementations use enterprise search platforms (Glean, Notion AI, Guru) or custom Agents SDK code, not the canvas. Independent deployment evidence for Agent Builder in this use case is limited as of May 2025.

**Honest failure modes.** File Search requires manual document uploads — there is no live sync with wikis, helpdesks, or existing knowledge systems. [One practitioner review](https://www.eesel.ai/blog/openai-agentkit-reviews) described this as "just not practical" for support teams with continuously updated knowledge bases. Teams must engineer automated upload pipelines to keep corpora current.

```
[START]  employee question + optional attachment
    |
    v
[GUARDRAILS]  confidentiality / PII check
    |
    v
[AGENT]  classify --> {domain, answerability, needed_sources}
    |
    +---[answerable]--------------------+---[not answerable]
    |                                   |
    v                                   v
[FILE SEARCH]  policy corpus      [AGENT]  draft escalation
[MCP]          knowledge system        |
    |                                  v
    v                            [MCP]  create case
[AGENT]  answer with cited passages + confidence
    |
    v
RETURN  answer
```

---

### 2. Customer-Facing Repetitive Interactions

**Business pain.** Customer service is the most documented AI agent use case. [Gartner predicts](https://www.gartner.com/en/newsroom/press-releases/2025-03-05-gartner-predicts-agentic-ai-will-autonomously-resolve-80-percent-of-common-customer-service-issues-without-human-intervention-by-20290) agentic AI will autonomously resolve **80% of common customer service issues without human intervention by 2029**, with a **30% reduction in operational costs**. [McKinsey's cross-industry data](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai) shows **10–20% cost reductions** in customer-service functions where AI handles tier-1 deflection. The [Klarna deployment](https://openai.com/index/klarna/) — handling the equivalent of 700 FTE in month one, cutting resolution time from 11 minutes to under 2 minutes across 23 markets — is widely cited as a production benchmark (company-disclosed via OpenAI).

An important nuance: Klarna and comparable deployments used OpenAI's API with custom code, not the Agent Builder canvas. Agent Builder is best positioned for mid-market organizations building this pattern for the first time, where the canvas governance advantage offsets the development time cost of writing custom orchestration.

**Why Agent Builder fits.** The tier-1 deflection pattern maps precisely to Agent Builder's architecture: guardrails filter at the entry point, classification routes by intent and severity, file search handles policy and FAQ retrieval, approval gates sit in front of account modifications or credits. Built-in evals make it possible to grade "was this classified correctly?" and "was the draft acceptable?" — questions compliance teams and QA managers care about.

**Evidence quality.** Strong for the business problem (multiple independent analyst sources). Moderate for Agent Builder specifically.

**Honest failure modes.** AgentKit as of 2025 lacks SOC2/HIPAA certification, disqualifying it for regulated industries (healthcare, financial services) handling sensitive customer data on the hosted canvas. File search does not auto-sync with live helpdesk ticket history — a gap for support use cases where context from prior interactions matters.

```
[START]  customer message + customer ID
    |
    v
[GUARDRAILS]  PII / jailbreak / off-topic
    |
    v
[AGENT]  classify --> {intent, severity, queue, draft_reply}
    |
    +---[simple]-----------------------------+---[refund / escalation]
    |                                        |
    v                                        v
[FILE SEARCH]  help articles          [HUMAN APPROVAL]
[MCP]          account context         |            |
    |                              [ok]        [rejected]
    v                               |                |
[AGENT]  draft reply            [MCP] update    [AGENT] revise
    |                               |                |
    +-------------------------------+----------------+
                                    |
                                    v
                             RETURN  response
```

---

### 3. Revenue Pipeline Latency

**Business pain.** Prospecting, account research, and lead qualification are documented productivity drains across sales organizations. [Accenture's banking case study](https://newsroom.accenture.com/news/2025/accenture-helps-organizations-advance-agentic-ai-with-gemini-enterprise) documents **50% productivity increase for marketing teams** and **20% revenue increase from AI-powered campaigns**. [McKinsey's cross-function analysis](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai) shows marketing and product development functions with AI agents achieving **>10% revenue uplift**. [Clay](https://openai.com/index/clay/) (10× year-over-year growth) and [Unify](https://openai.com/index/unify/) (30% of pipeline from AI agents) are cited by OpenAI as production deployments.

**Why Agent Builder fits.** Sales prep and lead qualification require connector-heavy workflows — calendar → CRM → web search → email draft — that benefit from MCP's catalog approach over bespoke OAuth integrations. Human approval before outbound communications is both a regulatory requirement (CAN-SPAM, GDPR) and a quality gate. The visual canvas makes it easier for sales operations teams — who are not engineers — to modify scoring logic and approval thresholds without filing an engineering ticket.

**Evidence quality.** Strong for the business problem. Moderate for Agent Builder specifically — production deployments at Clay/Unify scale use custom code. Agent Builder is the right fit for sales-ops teams building this pattern without a dedicated engineering team.

**Honest failure modes.** Web search tool quality varies; enriched briefs can surface stale or inaccurate public information without explicit freshness checks. [Independent testing](https://www.finalroundai.com/blog/openai-agent-builder-what-software-developers-are-saying-after-testing) found MCP CRM write-back unstable in some scenarios. Approval bottlenecks can eliminate latency improvements if review workflows are not designed for throughput.

```
[START]  manual trigger or scheduled run
    |
    v
[MCP]  read calendar events
    |
    v
[AGENT]  filter customer-facing meetings
    |
    +---[meeting found]-------------------+---[none found]
    |                                     |
    v                                     v
[MCP]  pull CRM notes + docs           [END]
    |
    v
[AGENT + web search]  enrich with recent public news
    |
    v
[TRANSFORM]  normalise brief schema
    |
    v
[AGENT]  draft brief + exec summary
    |
    v
[HUMAN APPROVAL]
    |
    +---[approved]------------+---[rejected]
    |                         |
    v                         v
[MCP]  save brief         [AGENT]  revise
       send summary            |
    |                          |
    +--------------------------+
    |
    v
[END]
```

---

### 4. Document-Heavy Intake Processing

**Business pain.** Invoice processing and accounts payable automation are the most quantified document-intake category. [Gartner's 2025 finance survey](https://www.gartner.com/en/newsroom/press-releases/2025-11-18-gartner-survey-shows-finance-ai-adoption-remains-steady-in-2025) found AP process automation is the **second-most-adopted finance AI use case at 37%** of organizations. [Independent peer-reviewed research](https://www.researchgate.net/publication/394436747) across 247 organizations in 15 industries found a **median 150% ROI in Year 1** for AP automation (range: 30–300%). Named production cases:

- **FRoSTA AG** (frozen food manufacturer, Europe): Deployed SAP BTP + Document AI for touchless invoice processing. [SAPinsider reports](https://sapinsider.org/blogs/frosta-achieves-60-touchless-invoice-processing-with-sap-btp-and-sap-document-ai/) **~60% of invoices fully automated end-to-end; processing time under one minute per invoice**.
- **Western Sugar Cooperative**: **25% reduction in invoice processing time; cost per invoice from $8 to $6** (SAP customer case, vendor-reported).

**Why Agent Builder fits.** Confidence-based branching is both a teaching moment and a production reality: high-confidence, low-risk invoices auto-route to draft posting; uncertain or potentially fraudulent items get a human. This maps precisely to Agent Builder's if/else branch structure with named approval nodes. Structured extraction plus confidence scoring is a strong showcase of the platform's output schema capabilities.

**Evidence quality.** Strong for the business problem. Note: the enterprises with the most documented AP automation results (FRoSTA, Western Sugar) used packaged ERP SaaS (SAP BTP, Ariba) — not custom Agent Builder workflows. Agent Builder is best positioned as the reasoning layer on top of document intake, not as a full AP platform. [Forrester reports](https://www.forrester.com/blogs/top-agentic-ai-use-cases-for-ap-automation-in-2026/) fewer than **15% of firms have activated agentic features** in their automation suites as of 2026 planning cycles — the market is real but early.

**Honest failure modes.** Regulated financial entities face data sovereignty issues with cloud-hosted canvas execution. "Agentic AI" vocabulary is being retroactively applied to RPA + ML deployments in vendor marketing; practitioners should distinguish genuine multi-step agent orchestration from classic document extraction pipelines.

```
[START]  invoice file or supplier email
    |
    v
[GUARDRAILS]
    |
    v
[AGENT]  extract --> {supplier, invoice_no, PO_no, amount, currency, confidence}
    |
    +---[high confidence]---------+---[low confidence / exception]---+---[fraud signal]
    |                             |                                   |
    v                             v                                   v
[MCP]                      [HUMAN APPROVAL]                   [HUMAN APPROVAL]
look up PO / vendor               |                                   |
    |                             v                                   v
    v                        [MCP]  post bill                  [MCP]  flag
draft posting                or queue exception task            for review
```

---

### 5. IT Operations and Access Management

**Business pain.** IT support teams face repetitive tier-1 volume — password resets, how-to questions, access requests — that drains specialist time from higher-value infrastructure work. [ServiceNow entered a multi-year strategic agreement with OpenAI](https://openai.com/index/servicenow-powers-actionable-enterprise-ai-with-openai/) (January 2026) to integrate GPT models across the ServiceNow platform. The broader IT service management market is one of the most active areas for agentic AI investment in 2025, though production deployments with quantified outcomes remain limited in publicly available independent sources.

**Why Agent Builder fits.** Branching by issue type maps cleanly to the canvas: how-to questions → file search answer, incidents → MCP ticket creation, access changes → human approval → MCP privilege grant. State management across conversation turns allows tracking of ticket IDs and status for multi-step follow-ups. The compliance argument is especially strong: access changes should never be autonomous, and a named approval node makes the control point explicit and auditable. [EU AI Act Article 14](https://artificialintelligenceact.eu/article/14/) and the [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) both require explicit intervention points in workflows that affect individual access or rights.

**Evidence quality.** Strong for the pattern and compliance argument. Weak for Agent Builder canvas-specific production deployments — most named IT service desk AI deployments use ServiceNow's own platform or Jira Service Management, not Agent Builder.

```
[START]  employee issue or access request
    |
    v
[GUARDRAILS]
    |
    v
[AGENT]  classify --> {category, urgency, access_change?, knowledge_answerable?}
    |
    +---[how-to]-------------+---[incident]-----------+---[access change]
    |                        |                        |
    v                        v                        v
[FILE SEARCH]           [MCP]                  [HUMAN APPROVAL]
    |                   create ticket               |
    v                       |                       v
[AGENT]  answer         escalation queue       [MCP]  submit to
    |                                          identity platform
    v
[SET STATE]  store ticket IDs + status for follow-up
```

---

### 6. Security Questionnaire and Compliance Document Response

**Business pain.** B2B software companies receive dozens of CAIQ, SIG, and customer-specific security questionnaires annually. Responding pulls security-engineer and sales-engineering time from higher-value work. The questions are semi-standardized, which makes this one of the most tractable document-intensive AI use cases — easier to evaluate reliably than most open-ended tasks.

**Why Agent Builder fits.** File search over an approved policy and evidence corpus is the right retrieval pattern. Structured output per question — question ID, proposed answer, evidence, confidence score, responsible owner — maps precisely to Agent Builder's output schema. Specialist routing by domain (security, legal, infrastructure) is a natural multi-agent handoff. All answers remain under human review before external release: the approval node is simultaneously a quality gate and an audit artifact demonstrating that no answer was sent without review.

**Evidence quality.** Architecturally sound and widely discussed in the practitioner community. Named production deployments using Agent Builder for this specific use case are not publicly documented as of May 2025. The pattern is established in custom-code implementations; Agent Builder is an emerging option for organizations building this capability without a dedicated engineering team.

```
[START]  uploaded questionnaire or pasted questions
    |
    v
[AGENT]  classify framework and section type
    |
    v
[FILE SEARCH]  retrieve approved policy, control, evidence docs
    |
    v
[AGENT]  emit --> {question_id, proposed_answer, evidence, confidence, owner}
    |
    +---[high confidence]----------+---[low confidence]
    |                              |
    v                              v
[HUMAN APPROVAL]            [SPECIALIST AGENT]
    |                        or domain reviewer
    v
[MCP]  export to document / spreadsheet
```

---

### 7. Legacy System Automation via Computer Use

**Business pain.** Many enterprise back-office systems have no API surface. Traditional RPA requires brittle UI scripting that breaks on minor UI changes. [Luminai](https://openai.com/index/new-tools-for-building-agents/) integrated the computer-use tool to automate complex operational workflows for an enterprise with legacy systems — in one pilot with a major community-service organization, it automated application processing and user enrollment in days, a workflow traditional RPA had failed to automate after months of effort.

**Evidence quality.** Directionally interesting. Production deployments at scale using Agent Builder's computer-use node are early-stage. This is the highest-complexity Agent Builder use case — treat it as an advanced pattern, not a first deployment.

**Honest failure modes.** Computer-use agents are brittle when UI layouts change — any release or redesign can silently break workflows. Guardrails must be configured to detect unexpected UI state and abort rather than proceed with incorrect form submissions. Without abort-on-deviation logic, computer-use agents can make incorrect writes to legacy systems in ways that are difficult to reverse.

```
[START]  application or enrollment request
    |
    v
[GUARDRAILS]  monitor for unexpected UI state, abort on deviation
    |
    v
[COMPUTER USE]  navigate legacy UI, fill forms, extract confirmation
    |
    +---[success]------------------------+---[failure]
    |                                    |
    v                                    v
[SET STATE]  record outcome         [HUMAN APPROVAL]
    |                                flag for manual review
    v
[MCP]  log result in tracking system
```

---

## Industry Verticals with Emerging Adoption

### Legal
Active AI adoption is documented and accelerating. [Thomson Reuters' 2025 survey](https://www.lawnext.com/2025/04/thomson-reuters-survey-over-95-of-legal-professionals-expect-gen-ai-to-become-central-to-workflow-within-five-years.html) (2,200+ professionals) found active generative AI usage in legal doubled to 26% year-over-year. [Clio's 2025 Legal Trends Report](https://www.clio.com/about/press/clio-latest-legal-trends-report/) (1,700+ legal professionals) found **69% of widely-AI-adopting firms saw revenue increases**. A&O Shearman (4,000+ staff, 43 jurisdictions), working with Harvey, [reports](https://www.law.com/legaltechnews/2025/07/09/inside-the-agentic-ai-tools-ao-shearman-built-with-harvey-/) **30% reduction in contract review time, 2–3 hours per user per week saved**, and key clauses across 2,000+ documents identified in under one hour versus previously a week. Thomson Reuters projects **240 hours per year saved per lawyer** within five years. [Harvey AI has reached 42% of the Am Law 100](https://legaltechnology.com/2025/12/02/the-impact-of-legal-ai-a-deeper-dive-into-the-rsgi-harvey-adoption-study/) as customers.

**Realistic Agent Builder scope in 2025:** Internal document Q&A, contract first-pass review with attorney approval gate, due diligence research triage, security questionnaire response (see above). **Hard boundary:** ABA Model Rule 5.5 and guidance from 23 state bar associations require attorney supervision of all AI-generated legal work. Agent Builder can research and draft; only licensed humans can advise.

### Healthcare
The strongest independently verified evidence in the entire agentic AI space comes from healthcare ambient documentation. [Kaiser Permanente (peer-reviewed, NEJM Catalyst, n=7,260 physicians)](https://catalyst.nejm.org/doi/abs/10.1056/CAT.25.0040): **15,700+ documentation hours saved; 88% of physicians reported positive impact on patient interaction quality**. [Cleveland Clinic: **14 minutes per day saved per clinician** across 4,000+ clinicians](https://www.aha.org/aha-center-health-innovation-market-scan/2025-03-11-3-takeaways-cleveland-clinics-ai-scribe-pilot-process-and-system-selection). [Northwell Health: prior authorization time reduced **from 2 hours to 6 seconds**](https://www.beckershospitalreview.com/healthcare-information-technology/ai/northwell-puts-ai-agents-to-work/) via the Ascertain AI agent. [Stanford Health Care: statistically significant reductions in physician task load and burnout](https://pubmed.ncbi.nlm.nih.gov/39657021/) in a prospective study.

**Realistic Agent Builder scope in 2025:** Administrative workflows — prior auth triage, documentation routing, internal policy Q&A, onboarding. **Hard boundaries:** (1) Any workflow involving ePHI on Agent Builder's hosted canvas requires a HIPAA BAA, which OpenAI does not currently offer for AgentKit. (2) Clinical decision support tools that replace physician judgment require FDA clearance. (3) Healthcare AI agents handling patient data need an immutable, reconstructable audit trail per HHS and HIPAA Security Rule §164.312(b) — Agent Builder traces are operational telemetry, not legal records.

### Financial Services
[McKinsey](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai) documents a global bank that used engineering agents to cut an IT modernization timeline by **>50%**, a multiagent market data system with **$3M projected annual savings**, and a financial institution credit memo restructuring with a **60% productivity gain for analysts**. [Accenture](https://newsroom.accenture.com/news/2025/accenture-helps-organizations-advance-agentic-ai-with-gemini-enterprise) documents a bank with **80% faster credit assessments and $200M annual productivity gains** from AI-assisted software development and operations. Forrester's Total Economic Impact methodology has documented **210% ROI over three years, with payback under 6 months**, for AI agent platform deployments in financial services.

**Realistic Agent Builder scope in 2025:** Internal analyst research assistance, document extraction and approval routing for non-regulated workflows, pre-trade compliance checks with human approval. **Hard boundaries:** Financial institutions in the US are now under [Federal Reserve SR 26-02](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.pdf) (effective April 2026), which explicitly covers GenAI and agentic workflows under model risk management. Any agent that informs a lending, trading, or credit decision requires independent validation and documentation standards that Agent Builder's hosted canvas does not currently satisfy without additional engineering.

### HR and People Operations
AI agent adoption in HR is early-stage. The most documented use cases are onboarding document processing, benefits Q&A, and job description generation. [Deloitte's survey](https://www.deloitte.com/us/en/about/press-room/state-of-ai-report-2026.html) shows 85% of companies expect to customize agents for HR needs, but production deployments with independently quantified outcomes are not yet publicly documented at scale.

**Realistic Agent Builder scope in 2025:** Benefits and policy Q&A, onboarding document routing with HR approval gate, job description drafting with human review before posting.

### Government and Public Sector
[OMB M-24-10](https://www.whitehouse.gov/wp-content/uploads/2024/03/M-24-10-Advancing-Governance-Innovation-and-Risk-Management.pdf) requires US federal agencies to maintain AI use-case inventories and implement human oversight requirements for rights-impacting or safety-impacting AI. Government procurement cycles are long and data sovereignty requirements are strict.

**Hard blocker for Agent Builder:** FedRAMP authorization and US federal data residency requirements disqualify Agent Builder's hosted canvas for most US federal workflows. State and local government use cases have more flexibility.

---

## What NOT to Build with Agent Builder

These are documented limitations based on practitioner experience and regulatory constraints — not speculative cautions.

**1. Workflows requiring low latency.** Agent Builder adds orchestration overhead from multi-node execution, tracing, and guardrails evaluation. [A practitioner review](https://www.eesel.ai/blog/openai-agentkit-reviews) found that a simple agent requiring "at least six different nodes" created a workflow that became "bloated and overly complicated." Real-time customer-facing interactions with strict latency SLAs are better served by direct API calls with minimal orchestration.

**2. Multi-model pipelines.** Agent Builder is locked to OpenAI models. If your workflow needs Claude for long-context reasoning, Gemini for summarization, and a local model for sensitive data, use LangChain, the Agents SDK, or a model-agnostic orchestration layer. This is the most commonly cited limitation across [independent practitioners](https://humanloop.com/blog/openai-agents-sdk).

**3. Durable, long-running, or resumable workflows.** The Agents SDK has no built-in durability primitives — no retries, checkpointing, or resumability across crashes or deployments. [A senior engineering leader at a fintech company](https://medium.com/@amri369/build-production-grade-agents-using-mcp-temporal-and-openai-agents-sdk-c49c928bc4ec) building a 6-agent financial analysis system concluded that "the SDK alone is insufficient" for production at scale and wrapped it in Temporal for durability: *"When it's time to serve millions of requests with real SLAs, you still need an orchestrator that gives you durability, retries, observability, versioning, and scale."* Agent Builder inherits this limitation.

**4. Regulated industries with strict data residency requirements.** Agent Builder runs entirely on OpenAI's cloud. No self-hosting option. No HIPAA BAA. GDPR EU data residency requirements are not satisfied. Financial services firms requiring on-premises model execution or auditor-accessible traces cannot use the hosted canvas without additional infrastructure.

**5. Workflows requiring immutable audit trails.** Agent Builder traces are operational telemetry. For use cases where the audit trail must be immutable, tamper-evident, and auditor-accessible — clinical decisions under FDA CDS guidance, financial model decisions under [SR 26-02](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.pdf), legal advice under state bar rules — the trace format and hosting arrangement are insufficient as legal records of decisions.

**6. Teams where the canvas governance advantage doesn't apply.** The visual canvas advantage — auditable by non-technical stakeholders — only delivers value if non-technical stakeholders actually use it. Engineering teams iterating on complex agent logic will find the canvas constraining. Use the Agents SDK directly and get the full expressiveness of Python.

**7. Cost-sensitive high-volume workloads without guardrails engineering.** A production case study found that without explicit cost guardrails, a failed agent made **47 tool calls per failed request at $0.41 per failure**. After adding three guardrails (tool-call budget cap, token-cost circuit breaker, duplicate-call termination), the same failure path dropped to **3 tool calls at $0.02 — a 95% per-failure cost reduction**. The SDK does not ship these guardrails by default. At high volume with pathological inputs, cost runaway is a real operational risk.

**8. Multi-agent patterns scaling past ~8–10 agents.** [Independent practitioners](https://medium.com/@roberto.g.infante/the-state-of-ai-agent-frameworks-comparing-langgraph-openai-agent-sdk-google-adk-and-aws-d3e52a497720) found that Agent Builder's handoff pattern "can become unwieldy with more than 8–10 agent types." Visual if/else routing logic becomes brittle for genuinely dynamic workflows with many conditional paths. For large multi-agent systems with complex routing logic, LangGraph or CrewAI Flows offer better primitives.

---

## Sources

### Analyst Reports
- [McKinsey & Company — The State of AI 2025: Agents, Innovation and Transformation](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai)
- [Deloitte — State of AI in the Enterprise 2026](https://www.deloitte.com/us/en/about/press-room/state-of-ai-report-2026.html)
- [Accenture — Advancing Agentic AI with Gemini Enterprise (banking case study, 2025)](https://newsroom.accenture.com/news/2025/accenture-helps-organizations-advance-agentic-ai-with-gemini-enterprise)
- [Accenture — The Productivity Payoff](https://www.accenture.com/us-en/insights/strategy/productivity-payoff)
- [Gartner — Agentic AI to Autonomously Resolve 80% of Customer Service Issues by 2029](https://www.gartner.com/en/newsroom/press-releases/2025-03-05-gartner-predicts-agentic-ai-will-autonomously-resolve-80-percent-of-common-customer-service-issues-without-human-intervention-by-20290)
- [Gartner — Over 40% of Agentic AI Projects Will Be Canceled by End of 2027](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027)
- [Gartner — Finance AI Adoption Remains Steady in 2025](https://www.gartner.com/en/newsroom/press-releases/2025-11-18-gartner-survey-shows-finance-ai-adoption-remains-steady-in-2025)
- [Forrester — Top Agentic AI Use Cases For AP Automation in 2026](https://www.forrester.com/blogs/top-agentic-ai-use-cases-for-ap-automation-in-2026/)
- [Thomson Reuters Institute — 2025 Generative AI in Professional Services Report (via LawNext)](https://www.lawnext.com/2025/04/thomson-reuters-survey-over-95-of-legal-professionals-expect-gen-ai-to-become-central-to-workflow-within-five-years.html)
- [Clio — 2025 Legal Trends Report](https://www.clio.com/about/press/clio-latest-legal-trends-report/)
- [ResearchGate — AP Automation ROI Study, 247 organizations, 15 industries](https://www.researchgate.net/publication/394436747)

### Peer-Reviewed and Clinical Research
- [Kaiser Permanente — Ambient AI Clinical Documentation, NEJM Catalyst (2025)](https://catalyst.nejm.org/doi/abs/10.1056/CAT.25.0040)
- [Stanford Health Care — Ambient AI Scribes and Physician Burnout, PubMed](https://pubmed.ncbi.nlm.nih.gov/39657021/)
- [SAPinsider — FRoSTA Achieves 60% Touchless Invoice Processing with SAP BTP](https://sapinsider.org/blogs/frosta-achieves-60-touchless-invoice-processing-with-sap-btp-and-sap-document-ai/)

### Independent Practitioner and Developer Accounts
- [Mohamed Amri (Director of AI Engineering, Alpheya) — Build Production Grade Agents Using MCP, Temporal and OpenAI Agents SDK](https://medium.com/@amri369/build-production-grade-agents-using-mcp-temporal-and-openai-agents-sdk-c49c928bc4ec)
- [Ahmet Kuzubaşlı (Staff Data Scientist, Udemy) — LangGraph vs. OpenAI Agents SDK](https://ahmetkuzubasli.medium.com/langgraph-vs-openai-agents-sdk-cdd7be7ec154)
- [Roberto Infante — The State of AI Agent Frameworks](https://medium.com/@roberto.g.infante/the-state-of-ai-agent-frameworks-comparing-langgraph-openai-agent-sdk-google-adk-and-aws-d3e52a497720)
- [Humanloop — OpenAI Agents SDK Assessment](https://humanloop.com/blog/openai-agents-sdk)
- [Independent AgentKit reviewer — OpenAI's AgentKit: Review](https://medium.com/@leucopsis/openais-agentkit-review-c83bee3c3d02)
- [eesel.ai — OpenAI AgentKit Reviews: A Practical Guide for Support Teams](https://www.eesel.ai/blog/openai-agentkit-reviews)
- [Final Round AI — What Software Developers Are Saying After Testing Agent Builder](https://www.finalroundai.com/blog/openai-agent-builder-what-software-developers-are-saying-after-testing)
- [All Things Open — How Block Scaled MCP to 12,000 Employees, 15 Job Functions](https://allthingsopen.org/articles/block-scaled-mcp-12000-employees-15-job-functions)
- [The New Stack — How Block Got 12,000 Employees Using AI Agents in Two Months](https://thenewstack.io/how-block-got-12000-employees-using-ai-agents-in-two-months/)
- [b-ta.ai — OpenAI Makes Building AI Agents Easier, Raises Vendor Lock-In Risks](https://www.b-ta.ai/blog/openai-makes-building-ai-agents-easier-raises-vendor-lock-in-risks)
- [CreateAIAgent — OpenAI Agent Builder vs n8n](https://createaiagent.net/openai-agent-builder-vs-n8n-ai-agent/)

### Industry Trade Press
- [Becker's Hospital Review — Northwell Puts AI Agents to Work](https://www.beckershospitalreview.com/healthcare-information-technology/ai/northwell-puts-ai-agents-to-work/)
- [AHA Market Scan — Cleveland Clinic AI Scribe: Pilot, Process and System Selection](https://www.aha.org/aha-center-health-innovation-market-scan/2025-03-11-3-takeaways-cleveland-clinics-ai-scribe-pilot-process-and-system-selection)
- [Law.com Legal Tech News — Inside the Agentic AI Tools A&O Shearman Built with Harvey](https://www.law.com/legaltechnews/2025/07/09/inside-the-agentic-ai-tools-ao-shearman-built-with-harvey-/)
- [Legal IT Insider — RSGI/Harvey AI Adoption Study](https://legaltechnology.com/2025/12/02/the-impact-of-legal-ai-a-deeper-dive-into-the-rsgi-harvey-adoption-study/)
- [PYMNTS — Ramp Adds AI Agents for Invoice Coding and Payment Processing](https://www.pymnts.com/news/artificial-intelligence/2025/ramp-adds-ai-agents-invoice-coding-approval-payment-processing/)

### Regulatory Frameworks and Standards
- [EU AI Act — Article 14: Human Oversight Requirements](https://artificialintelligenceact.eu/article/14/)
- [Federal Reserve — SR 26-02: Revised Guidance on Model Risk Management](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.pdf)
- [NIST — AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [OMB M-24-10 — Advancing Governance, Innovation, and Risk Management for Agency Use of AI](https://www.whitehouse.gov/wp-content/uploads/2024/03/M-24-10-Advancing-Governance-Innovation-and-Risk-Management.pdf)

### Vendor Case Studies
- [OpenAI — Klarna case study](https://openai.com/index/klarna/)
- [OpenAI — Introducing AgentKit](https://openai.com/index/introducing-agentkit/)
- [OpenAI — Luminai: New Tools for Building Agents](https://openai.com/index/new-tools-for-building-agents/)
- [OpenAI — ServiceNow: Powers Actionable Enterprise AI](https://openai.com/index/servicenow-powers-actionable-enterprise-ai-with-openai/)
- [OpenAI — Clay case study](https://openai.com/index/clay/)
- [OpenAI — Unify case study](https://openai.com/index/unify/)

---

*Research synthesized from analyst firms (McKinsey, Deloitte, Gartner, Forrester, Accenture), independent practitioner accounts, peer-reviewed studies (NEJM Catalyst, PubMed), industry trade press (Becker's, AHA, Law.com, Legal IT Insider, SAPinsider), regulatory frameworks (EU AI Act, NIST AI RMF, Federal Reserve SR 26-02), and vendor case studies. Vendor claims are not presented as independently verified outcomes.*

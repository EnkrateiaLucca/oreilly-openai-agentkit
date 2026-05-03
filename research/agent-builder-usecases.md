# OpenAI Agent Builder — Business Use Cases

> Course demo resource. Platform fundamentals (nodes, tools, handoffs) are covered in the course itself. This report focuses on **which business problems Agent Builder solves well**, **how real companies are using it**, and **which demos best showcase the platform features** for students.

---

## What makes a strong Agent Builder demo

A good demo is not "fully autonomous department replacement." The strongest demos share four traits:

| Criterion | Practical test |
|---|---|
| **Real business pain** | Removes repetitive manual work, reduces turnaround time, or adds a control layer that compliance teams care about |
| **Visual workflow fit** | Expressible in one canvas — clear stage-by-stage flow with explicit branch points, handoffs, and approval gates |
| **Feature showcase depth** | Shows at least two notable features beyond "single prompt plus tool" (guardrails, MCP write-back, approvals, multi-agent routing, evals) |
| **Bounded write scope** | Sensitive actions (money, outbound comms, data writes) are approval-gated, not autonomous |

The pattern that appears in every strong production deployment: **crisp input → structured intermediate output → explicit branch → narrow write permission with human approval**.

---

## Use Cases

### 1. Customer Support Triage & Draft-Response

**Business problem.** Support teams lose large amounts of time to non-customer-facing work — routing, searching policy docs, writing first-draft replies. AI-assisted triage is the highest-adoption use case today.

**Production anchor — [Klarna](https://openai.com/index/klarna/).** Klarna deployed an AI assistant powered by OpenAI that handled two-thirds of all customer service chats within its first month. It did the equivalent work of 700 full-time agents, matched human CSAT scores, and reduced average resolution time from 11 minutes to under 2 minutes across 23 markets in 35 languages.

**Workflow in Agent Builder.**

```
Start (ticket / chat message + customer ID)
  → Guardrails: PII check, jailbreak filter, off-topic block
  → Agent: classify intent → {intent, severity, queue, confidence, proposed_reply}
  → If/else:
      simple answer   → File search (help centre) + MCP (account context) → Agent: draft reply
      refund/credit   → Human approval → MCP: apply credit / update ticket
      escalation      → MCP: route to human queue
```

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

**Features showcased.** Guardrails, structured outputs, human approvals, MCP connectors, multi-agent routing, trace grading (eval: was queue correct? was draft acceptable?).

---

### 2. Internal Knowledge & Policy Q&A

**Business problem.** Information fragmentation is a documented productivity drain. HR, IT, finance, and legal policy questions repeat constantly and pull focus from skilled work. Self-service assistants with approved document corpora reduce caseloads and keep answers consistent.

**Why Agent Builder fits perfectly.** No risky external writes. The entire workflow is: classify question → retrieve from approved corpus → answer with cited passages → escalate unresolvable cases. This is also the easiest demo to scope and evaluate, making it the best "first build" for non-technical teams.

**Workflow in Agent Builder.**

```
Start (employee question + optional attachment)
  → Guardrails: confidentiality check
  → Agent: classify domain → {domain, answerability, needed_sources}
  → If/else:
      answerable   → File search (policy corpus) or MCP (knowledge system)
                   → Agent: answer with cited passages + confidence
      not answerable → Agent: draft escalation → MCP: create case
```

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

**Features showcased.** Hosted file search (strongest showcase), structured outputs, transform nodes, evals/tracing, simple specialist routing, optional MCP against document systems.

---

### 3. Sales Meeting Prep & Account Briefing

**Business problem.** Sales reps spend a large share of their time on non-selling work — researching accounts, reading CRM notes, writing pre-call briefs. This workflow assembles that brief automatically before each customer-facing meeting.

**Production anchors.**
- **[Clay](https://openai.com/index/clay/)** — built Claygent, an AI web scraper on GPT-4 that does the research work of an entire team. Achieved 10× year-over-year growth for two consecutive years, with 2.5× in the first five months of 2024 alone.
- **[Unify](https://openai.com/index/unify/)** — uses o3, GPT-4.1, and the Computer-Using Agent to automate prospecting, research, and outreach at scale; 30% of its pipeline is now generated by agents.

**Workflow in Agent Builder.**

```
Start (manual trigger or scheduled run)
  → MCP: read calendar → Agent: filter customer-facing meetings
  → If/else: external meeting found?
      Yes → MCP: pull CRM notes + document context
           → Agent (with web search tool): enrich with recent public news
           → Transform: normalise brief schema
           → Agent: draft brief + exec summary
           → Human approval
           → MCP: save brief + send summary
      No  → End
```

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

**Features showcased.** MCP/connector-rich demo (calendar + CRM + document + email), web search on the agent tooling side, structured briefs, human approval before writes, transform nodes.

---

### 4. CRM Lead Qualification & Follow-Up

**Business problem.** Prospecting and lead qualification are repetitive and highly structured — delay directly affects pipeline health. SDR and BDR teams need consistent scoring and timely follow-up without sacrificing personalisation.

**Production anchors.** Clay and Unify (see above). Both use OpenAI agents for exactly this: scoring, enrichment, personalised outreach draft, and CRM write-back.

**Workflow in Agent Builder.**

```
Start (inbound lead form / chat transcript / list item)
  → Guardrails: PII check, prompt abuse
  → Agent: extract company, role, intent, buying stage → strict schema
  → If/else: score threshold?
      qualified   → Agent: personalise follow-up draft
                  → Human approval → MCP: write CRM + send/draft email
      not ready   → MCP: write nurture tag to CRM
      high-value  → Specialist agent: objection-handling / senior routing
```

```
[START]  inbound lead form / chat transcript / list item
    |
    v
[GUARDRAILS]  PII check / prompt abuse
    |
    v
[AGENT]  extract --> {company, role, intent, buying stage, score}
    |
    +---[qualified]-----------+---[not ready]-----+---[high-value]
    |                         |                   |
    v                         v                   v
[AGENT]                  [MCP]            [SPECIALIST AGENT]
personalise              write nurture    objection handling /
follow-up draft          tag to CRM       senior routing
    |
    v
[HUMAN APPROVAL]
    |
    v
[MCP]  write CRM + send / draft email
```

**Features showcased.** Structured extraction, conditional routing by score, CRM connector write-back, outbound approval gates, multi-agent specialist routing, trace graders (did the model pick the right queue?).

---

### 5. IT Service Desk Triage & Access Requests

**Business problem.** IT support teams need a conversational front door that can answer "how-to" questions, classify incidents correctly, and route access requests — without granting any privilege changes autonomously.

**Production anchor — [ServiceNow](https://openai.com/index/servicenow-powers-actionable-enterprise-ai-with-openai/).** ServiceNow entered a multi-year strategic agreement with OpenAI (January 2026) to integrate GPT models as a preferred intelligence layer across the ServiceNow platform, directly enabling AI agents for service-desk and workflow automation at enterprise scale.

**Workflow in Agent Builder.**

```
Start (employee issue or access request)
  → Guardrails
  → Agent: classify → {category, urgency, access_change?, knowledge_answerable?}
  → If/else:
      how-to question      → File search → Agent: answer
      incident             → MCP: create ticket → route to escalation queue
      access change        → Human approval → MCP: submit to identity platform
  → Set state: store ticket IDs and status for follow-up turns
```

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
                                               identity platform
    |
    v
[SET STATE]  store ticket IDs + status for follow-up
```

**Features showcased.** Branching by issue type, human approvals for privileged changes, state across turns, case creation via MCP, multi-agent routing.

---

### 6. Invoice Intake & AP Exception Routing

**Business problem.** Accounts-payable teams are the clearest near-term target for document extraction + structured branching + finance system write-back. In 2025 AP surveys, top AI use cases were invoice data extraction, automated matching/approvals, and duplicate/fraud detection.

**Why it's a great Agent Builder demo.** The workflow is almost entirely deterministic once the extraction schema is fixed. Confidence-based branching is a perfect teaching moment: high-confidence, low-risk items auto-route to draft posting; anything uncertain gets a human.

**Workflow in Agent Builder.**

```
Start (invoice file or forwarded supplier email)
  → Guardrails
  → Agent: extract → {supplier, invoice_no, PO_no, amount, currency, due_date, bank_details_present, confidence}
  → If/else: confidence + policy rules?
      high-confidence, low-risk   → MCP: look up PO/vendor → draft posting
      exception / low-confidence  → Human approval → MCP: post bill or queue exception task
      fraud signal                → Human approval → MCP: flag for review
```

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

**Features showcased.** Structured extraction with confidence scoring, confidence-based branching, ERP/finance MCP connector, approval gates for all financial writes, evals against known-good invoice samples.

---

### 7. Legacy System Automation via Computer Use

**Business problem.** Many enterprise back-office systems have no API surface. Traditional RPA requires brittle UI scripting. The computer-use tool lets an agent navigate desktop and browser UIs like a human operator — covering systems that were previously off-limits to automation.

**Production anchor — [Luminai](https://openai.com/index/new-tools-for-building-agents/).** Luminai integrated the computer-use tool to automate complex operational workflows for enterprises with legacy systems lacking APIs. In one pilot with a major community-service organisation, Luminai automated application processing and user enrollment in days — a workflow traditional RPA had failed to automate after months of effort.

**Workflow in Agent Builder.**

```
Start (application or enrollment request)
  → Computer Use tool: navigate legacy UI, fill form fields, extract confirmation data
  → If/else: completion confirmed?
      success   → Set state: record outcome → MCP: log result in tracking system
      failure   → Human approval: flag for manual review + fallback routing
  → Guardrails: monitor for unexpected UI state, abort on deviation
```

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

**Features showcased.** Computer use tool (non-API automation), guardrails as safety monitors, fallback handoffs, state tracking, MCP write-back to logging systems.

---

### 8. Security Questionnaire Response Drafter

**Business problem.** Security questionnaires (CAIQ, SIG, customer-specific) are standardised, repetitive, and document-heavy. B2B software companies receive dozens per year, and responding takes security and sales engineering time that could be spent elsewhere.

**Why it works well.** Because the questions are semi-standardised, it is easier to evaluate reliably than most open-ended chat tasks. File search over an approved policy/evidence corpus is the right retrieval pattern; all answers stay reviewable before release.

**Workflow in Agent Builder.**

```
Start (uploaded questionnaire or pasted questions)
  → Agent: classify framework and section type
  → File search: retrieve approved policy, control, and evidence documents
  → Agent: emit structured answer objects → {question_id, proposed_answer, evidence, confidence, owner}
  → If/else: confidence threshold?
      high-confidence   → Human approval → MCP: export to document/spreadsheet
      low-confidence    → Route to domain specialist agent or reviewer
```

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

**Features showcased.** File search (best-in-class showcase), structured output per question, specialist routing by domain, trace-based quality review, approval before external release.

---

## Prioritisation for the Course

| Use case | Business value | Agent Builder fit | Key features | Complexity | Recommended |
|---|---|---|---|---|---|
| Internal knowledge / policy Q&A | High | Very high | File search, MCP, structured outputs, evals | Low | **Build first** |
| Customer support triage (Klarna pattern) | High | High | Guardrails, approvals, MCP, routing, tracing | Low–medium | **Build first** |
| Sales meeting prep (Clay / Unify pattern) | High | High | MCP connectors, web search, approvals | Medium | **Build first** |
| Security questionnaire drafter | High in B2B | Very high | File search, structured outputs, reviewer routing | Low–medium | Build early if relevant |
| CRM lead qualification | High | High | Structured scoring, CRM writes, approvals | Medium | Build second |
| IT service desk (ServiceNow pattern) | High | High | Guardrails, approvals, state, routing | Medium | Build second |
| Invoice / AP exception routing | Medium–high | Medium–high | Extraction, confidence branching, approvals | Medium–high | Build second |
| Legacy automation via computer use (Luminai) | High where applicable | Medium | Computer use, fallback handoffs, guardrails | High | Advanced demo |

**Recommended demo sequence for the course:** internal knowledge assistant → customer support triage → sales meeting prep. These three collectively cover the most important platform features (file search, guardrails, MCP write-back, human approvals, multi-agent routing, evals) while keeping implementation risk low and narrative coherent: one retrieval-first workflow, one operations-and-control workflow, one connector-heavy revenue workflow.

---

## Sources

**Named production deployments**

- [Klarna — OpenAI case study](https://openai.com/index/klarna/) ✅
- [Clay — OpenAI case study](https://openai.com/index/clay/) ✅
- [Unify — OpenAI case study](https://openai.com/index/unify/) ✅
- [Luminai — New tools for building agents (OpenAI)](https://openai.com/index/new-tools-for-building-agents/) ✅
- [ServiceNow — OpenAI case study](https://openai.com/index/servicenow-powers-actionable-enterprise-ai-with-openai/) ✅

**Platform documentation**

- [Introducing AgentKit — OpenAI](https://openai.com/index/introducing-agentkit/) ✅
- [Agent Builder — OpenAI Developer Docs](https://developers.openai.com/api/docs/guides/agent-builder) ✅
- [Agents SDK Overview — OpenAI Developer Docs](https://developers.openai.com/api/docs/guides/agents) ✅
- [Guardrails — OpenAI Agents Python SDK](https://openai.github.io/openai-agents-python/guardrails/) ✅

---

*Synthesized from OpenAI deep research report and verified production case studies. Workflow specifics derived from Agent Builder platform documentation. Company claims sourced from OpenAI-published case studies.*

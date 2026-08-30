# Aster & Row AI Support Agent

A reliable Retrieval-Augmented Generation (RAG) based customer-support agent built for the Aster & Row AI Agent Intern Take-Home Assignment.

The system is designed to answer customer questions using the supplied knowledge base and mock order data while handling conflicting sources, missing information, prompt injection, privacy-sensitive order data, and multi-turn conversations safely.

---

## Project Overview

Aster & Row is a fictional ecommerce company selling bags, drinkware, and travel accessories.

The goal of this project is to build a small but reliable AI support agent that can:

- Answer policy and product questions using the supplied knowledge base.
- Retrieve only relevant information instead of sending the entire corpus to the model.
- Prefer active and authoritative policy sources.
- Handle conflicting official sources safely.
- Look up order status using the provided order data.
- Avoid inventing order information.
- Maintain relevant context across multiple turns.
- Protect private and internal customer information.
- Resist prompt injection contained inside retrieved documents.
- Clearly abstain when the available information is insufficient.
- Recommend human support when required.
- Provide source references for knowledge-base answers.
- Provide deterministic evaluation results.

---

## Key Features

### 1. Retrieval-Augmented Generation

The agent retrieves relevant passages from the Markdown documents stored in:

```text
knowledge-base/

Retrieved passages contain useful metadata such as:

Filename
Section / heading
Status
Policy authority
Content

The retrieved context is then supplied to the language model for answering.

The agent does not send the entire knowledge base to the model.

2. Source Precedence

The knowledge base intentionally contains:

Current policies
Legacy / superseded policies
Internal notes
Conflicting active sources
Product-specific information

The agent is designed to prefer current authoritative policy sources and avoid treating internal or superseded material as customer-facing policy.

3. Order Lookup Tool

Order information is stored in:

data/orders.json

The application uses an order lookup function rather than placing the complete order dataset into the model prompt.

The lookup behavior supports:

Valid order IDs
Lowercase order IDs
Order IDs with surrounding whitespace
Missing order IDs
Unknown order IDs
Cancelled orders
Shipped orders
Orders without delivery estimates

The agent does not invent an order status or delivery estimate.

Private fields such as customer email, address, internal notes, risk scores, and fraud-review information are not exposed to customers.

4. Multi-Turn Conversation

The agent maintains relevant session context.

For example:

User: Do you ship internationally?

Agent: Aster & Row currently ships internationally only to Canada.

User: What about Canada?

Agent: Canada is supported for international shipping...

The system also remembers an order ID when appropriate so that a follow-up question can refer to the same order.

5. Prompt Injection Protection

Retrieved documents are treated as untrusted data.

The agent does not follow instructions embedded inside retrieved documents.

Application-level rules have higher priority than instructions found inside knowledge-base content.

The system also avoids exposing:

System prompts
Hidden instructions
Credentials
Internal notes
Risk scores
Fraud-review information
Private customer information
6. Source Conflict Handling

Some supplied documents intentionally contain conflicting information.

For example, the Breeze Tumbler sources contain different cleaning instructions.

Instead of silently selecting one source, the agent:

Detects the conflict.
Explains that the official sources disagree.
Recommends human confirmation.
Provides safer interim guidance when appropriate.
7. Safe Abstention

When the available information is insufficient, the agent does not guess.

It explicitly communicates that:

The supplied information is insufficient.

It can also recommend human confirmation when a definitive answer cannot safely be provided.

Architecture

The project follows a simple deterministic-first architecture.

                         User Question
                              |
                              v
                     +----------------+
                     |   Aster & Row  |
                     |     Agent      |
                     +----------------+
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
        Policy Rules     Order Tool       Retriever
              |               |               |
              |               v               v
              |        data/orders.json   knowledge-base/
              |                               |
              +---------------+---------------+
                              |
                              v
                     Response Generation
                              |
                              v
                   Answer + Sources + Handoff

The system uses deterministic handlers for critical policy and safety cases and uses retrieval plus LLM generation for ordinary knowledge-base questions.

Project Structure
ai-agent-intern-test/
│
├── app/
│   ├── __init__.py
│   ├── agent.py
│   ├── retriever.py
│   └── order_tool.py
│
├── data/
│   ├── orders.json
│   └── orders-data-dictionary.md
│
├── evaluation/
│   ├── visible-cases.json
│   └── run_evaluation.py
│
├── knowledge-base/
│   ├── 01-returns-policy-current.md
│   ├── 02-returns-policy-legacy.md
│   ├── 03-final-sale-and-promotions.md
│   ├── 04-damaged-or-wrong-items.md
│   ├── 05-domestic-shipping.md
│   ├── 06-international-shipping.md
│   ├── 07-warranty.md
│   ├── 08-order-changes-and-cancellations.md
│   ├── 09-trailplus-membership.md
│   ├── 10-gift-cards-and-price-adjustments.md
│   ├── 11-product-care.md
│   ├── 12-breeze-tumbler-product-card.md
│   ├── 13-support-escalation.md
│   └── 14-internal-content-migration-notes.md
│
├── app.py
├── .env.example
├── .gitignore
└── README.md
Technology Stack
Component	Technology
Language	Python
Interface	Streamlit
LLM	OpenAI API
Retrieval	Custom knowledge-base retriever
Data	JSON + Markdown
Environment	Python virtual environment
Evaluation	Custom deterministic evaluation suite

The implementation intentionally avoids unnecessary infrastructure such as a production vector database because the assignment prioritizes reliability and practical trade-offs.

Setup
1. Clone the repository
git clone https://github.com/sunali18565/ai-agent-intern-test.git
cd ai-agent-intern-test
2. Create a virtual environment

Windows PowerShell:

python -m venv venv

Activate it:

.\venv\Scripts\Activate.ps1

If PowerShell blocks activation, run:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Then:

.\venv\Scripts\Activate.ps1
3. Install dependencies
python -m pip install -r requirements.txt
4. Configure environment variables

Create a local .env file based on .env.example.

Example:

OPENAI_API_KEY=your_api_key_here

Do not commit real API keys.

The repository contains .gitignore rules to prevent local secrets from being committed.

Running the Application

Start the Streamlit application:

python -m streamlit run app.py

The application will normally be available at:

http://localhost:8501
Running the Evaluation

Run the complete evaluation suite with:

python -m evaluation.run_evaluation

The evaluation reports:

Individual test results
Category results
Overall score
Detailed evaluation output
Evaluation Results
Final Evaluation

The final implementation passes all supplied visible evaluation cases.

Passed: 21/21
Score: 100.0%
Status: EXCELLENT
Category Results
Category	Result
Abstention	2/2 (100%)
Conversation	1/1 (100%)
Groundedness	2/2 (100%)
Multi-source grounding	1/1 (100%)
Privacy	2/2 (100%)
Prompt security	1/1 (100%)
Retrieval	3/3 (100%)
Source conflict	1/1 (100%)
Tool reliability	3/3 (100%)
Tool use	5/5 (100%)
Overall	21/21 (100%)
Baseline vs Final

An early baseline evaluation exposed several reliability problems.

Early Baseline
Passed: 10/21
Score: 47.6%
Status: NEEDS SIGNIFICANT IMPROVEMENT

The early implementation failed cases involving:

TrailPlus return windows
Final-sale damaged exceptions
Canada shipping
Unsupported countries
Missing order IDs
Cancelled orders
Unknown orders
Warranty details
Retrieved prompt injection
Insufficient information
Conflicting product-care sources
Final Version
Passed: 21/21
Score: 100.0%
Status: EXCELLENT

The main improvement was moving critical policy, safety, order, and conflict behavior into deterministic application-level handling instead of relying entirely on unconstrained LLM generation.

Bug Diary
Bug 1 — Incorrect / Missing Return Window
Reproduction

Question:

My TrailPlus membership was active when I ordered. What is my return window?
Initial Problem

The early implementation did not consistently return the TrailPlus-specific 45-calendar-day return window.

Root Cause

The generic return-policy retrieval path could prioritize the standard 30-day policy instead of correctly applying the TrailPlus exception.

Fix

Added a dedicated TrailPlus handler that checks whether TrailPlus was active when the order was placed.

Regression Test

The evaluation case:

trailplus-return-window

now passes.

Bug 2 — Missing Order ID Could Cause Unsupported Status Claims
Reproduction

Question:

Where is my order?
Initial Problem

The agent could attempt to answer an order-status question without having an order ID.

Root Cause

The order path was not strict enough about requiring an identifier before performing a lookup.

Fix

The order handler now requires an order ID before performing an order lookup.

If the ID is missing, the agent asks the customer to provide it.

Regression Test

The evaluation cases:

missing-order-id
original-missing-order-id

now pass.

Bug 3 — Cancelled Order Could Expose Stale ETA
Reproduction

A cancelled order containing an old delivery estimate was queried.

Initial Problem

A generic order response could potentially use the delivery estimate even though the order was cancelled.

Root Cause

The delivery estimate was not being checked against the authoritative current order status before generating the response.

Fix

Cancelled status is handled before delivery information.

The agent explicitly states that the order is cancelled and does not report its stale delivery estimate.

Regression Test

The evaluation case:

cancelled-order-stale-eta

now passes.

Bug 4 — Conflicting Product Information
Reproduction

Question:

Is the Breeze Tumbler dishwasher safe?
Initial Problem

Different active official sources contained conflicting cleaning instructions.

Root Cause

A normal retrieval-and-generation approach could silently select one passage.

Fix

Added explicit source-conflict handling for the Breeze Tumbler.

The response identifies the conflict and recommends human confirmation.

Regression Test

The evaluation case:

genuine-active-source-conflict

now passes.

Bug 5 — Retrieved Prompt Injection
Reproduction

A retrieved migration note contained instruction-like text attempting to change the return policy.

Initial Problem

Retrieved content could influence the response as though it were an application instruction.

Root Cause

Retrieved text was not sufficiently separated from system/application instructions.

Fix

The application treats retrieved documents as untrusted data and applies explicit policy precedence rules.

Regression Test

The evaluation case:

retrieved-prompt-injection

now passes.

Privacy and Security

The agent is designed to avoid exposing sensitive order information.

It does not reveal:

Customer email addresses
Customer addresses
Internal notes
Risk scores
Fraud-review information
Credentials
Hidden prompts
System instructions

For example, a request for private order information receives a safe refusal instead of exposing internal data.

Tool Reliability

The order tool is only used when an order lookup is actually required.

The model does not receive the complete order dataset.

The application:

Extracts and normalizes the order ID.
Performs the lookup.
Checks whether the order exists.
Uses the current order status.
Handles cancelled orders before delivery information.
Avoids inventing unavailable delivery estimates.
Returns only customer-safe information.
Observability

The application supports inspection of the agent's behavior through its evaluation and application flow.

Important information includes:

User input
Retrieved knowledge
Source metadata
Order lookup results
Final response
Handoff decisions
Errors and fallbacks

Sensitive information is not intentionally exposed to customers.

Human Handoff

The agent recommends human support when:

Official sources genuinely conflict.
Available information is insufficient.
A return/refund/replacement requires approval.
A material or composition claim cannot be reliably verified.
A customer-specific action cannot be completed safely.

The agent does not falsely claim that a refund, replacement, cancellation, or other unsupported action has been completed.

Example Interactions
Knowledge Base Question
User:
How long does a regular customer have to return an unused backpack?

Agent:
Customers on the standard plan may request a return within
30 calendar days of delivery...

The response includes the relevant knowledge-base source.

Order Lookup
User:
Where is ORD-1007?

The application performs an actual order lookup rather than guessing the order status.

Multi-Turn Conversation
User:
Do you ship internationally?

Agent:
Aster & Row currently ships internationally only to Canada.

User:
What about Canada?

Agent:
Canada is supported for international shipping...
Safe Conflict Handling
User:
Is the Breeze Tumbler dishwasher safe?

Agent:
The current official sources conflict about Breeze Tumbler
cleaning instructions. Human confirmation is recommended.
Evaluation Command

The complete evaluation can be run with:

python -m evaluation.run_evaluation

Expected final result:

Passed: 21/21
Score: 100.0%
Status: EXCELLENT
Demo

A short 2–4 minute demonstration should cover:

A knowledge-base question with source citation.
An order lookup.
A multi-turn conversation.
A case where the agent abstains or recommends human help.
The evaluation suite running successfully.
Demo Video

Add the final demo GIF or video here:

[Demo video/GIF will be embedded here]
Known Limitations

This project is intentionally designed as a take-home assignment rather than a production support platform.

Known limitations include:

The order dataset is mock data.
Authentication is not implemented because possession of the order ID is sufficient for this assignment.
The system uses a lightweight custom retrieval approach rather than a production vector database.
The interface is intentionally minimal.
The application does not implement real-world refund, replacement, cancellation, or address-change operations.
Production monitoring and distributed tracing are outside the scope of the assignment.

Before production deployment, stronger identity verification, persistent conversation management, production-grade retrieval infrastructure, monitoring, rate limiting, and comprehensive security controls would be appropriate.

AI Coding Tools Used

AI coding assistance was used during development for:

Exploring implementation approaches.
Debugging Python and PowerShell issues.
Improving retrieval and deterministic policy handling.
Reviewing edge cases.
Structuring the evaluation logic.
Improving documentation.

One important lesson from the development process was that AI-generated implementations can be incomplete when handling policy precedence and edge cases.

For example, an early implementation relied too heavily on generic retrieval/LLM generation and did not consistently handle specific exceptions such as the TrailPlus 45-day return window, cancelled-order stale ETA, and source conflicts.

These issues were identified through deterministic evaluation and then fixed with explicit application-level rules and regression coverage.

Design Philosophy

The project follows a simple principle:

Reliability is more important than producing an answer to every question.

The agent should prefer:

Correct answer
     |
     v
Grounded answer
     |
     v
Safe abstention
     |
     v
Human confirmation

rather than guessing when the available information does not support a reliable answer.

Final Result

The completed system achieves:

21/21 evaluation cases passed
100.0% final score
EXCELLENT

The implementation focuses on reliable retrieval, safe order handling, privacy protection, prompt-injection resistance, multi-turn context, source conflict handling, and deterministic evaluation.


---


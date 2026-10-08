# Personal LinkedIn Copilot

A local-first Chrome extension that researches LinkedIn profiles, detects relevant hiring opportunities, matches the person against your resumes, and generates a natural LinkedIn outreach message.

The system uses a **Chrome extension + FastAPI + local Ollama LLM**. No LinkedIn messages are sent automatically.

---

## What it does

The Copilot is designed to answer:

> "I'm looking at this LinkedIn person. Given what I want from this interaction, what should I know, which resume is relevant, and what should I say?"

The user opens a LinkedIn profile and selects an intent:

* **Job opportunity** — identify hiring opportunities, evaluate fit, and select the relevant resume
* **Founder** — understand the founder/company and find the best way to approach
* **Network** — find genuine professional overlap
* **Ask for advice** — find a specific, reasonable question to ask
* **Custom** — provide a custom goal

The user can also select a tone and optionally provide additional context.

The Copilot then handles the research and reasoning internally.

The user only sees the final result and decides whether to copy/send the message.

---

# Core principles

### 1. The LinkedIn person and candidate are different people

The candidate is the person using the Copilot.

For example:

```text
Candidate:
Swayam Gupta

LinkedIn person:
Soman Khazharey R.C.
```

This is completely normal.

A different name must **not** be treated as a candidate/profile mismatch.

---

### 2. Explicit LinkedIn evidence has priority

The system should prioritize information in roughly this order:

```text
Explicit profile hiring signal
        >
Explicit hiring post
        >
Explicit job/recruitment information
        >
Other relevant profile information
        >
Inferred information
        >
Random page content
```

For example, if a profile explicitly says:

```text
Hiring: Machine Learning Engineer
```

that should take priority over an unrelated post mentioning another position.

---

### 3. Internal reasoning should stay internal

The user should not have to inspect:

* LLM reasoning
* retrieval scores
* keyword scores
* intermediate research
* model calls
* resume-ranking internals

For example, the UI should never tell the user:

```text
LOCAL RELEVANCE SCORE = 6
```

Instead:

```text
Resume selected:
ai_ml_resume.pdf

Why:
Your AI/ML resume is the closest match to the Machine Learning Engineer opening.
```

---

### 4. The final message must actually be a message

The generated LinkedIn message should be something the user can paste into LinkedIn.

It should not explain the model's reasoning.

Bad:

```text
The candidate has strong AI/ML skills but the role is not clearly
supported by the resume.
```

Good:

```text
Hi Soman, saw that Ecostel is hiring for an ML Engineer. I'm a 4th-year
CSE student working on AI/ML and would love to understand what you're
looking for in the role. Would be great to connect.
```

The exact message depends on the actual profile and resume.

---

# Architecture

```text
                         LinkedIn
                            │
                            ▼
                  ┌───────────────────┐
                  │ Chrome Extension  │
                  │                   │
                  │ Profile extraction│
                  │ Intent / Tone      │
                  │ Extra context      │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │     FastAPI       │
                  │     /screen       │
                  └─────────┬─────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
          ┌──────────────┐      ┌──────────────┐
          │ LLM Call 1   │      │ Resume       │
          │              │      │ Retrieval    │
          │ LinkedIn     │      │              │
          │ Research     │      │ Local ranking│
          └──────┬───────┘      └──────┬───────┘
                 │                     │
                 └──────────┬──────────┘
                            ▼
                  ┌───────────────────┐
                  │    LLM Call 2     │
                  │                   │
                  │ Final decision    │
                  │ Resume selection  │
                  │ Fit / overlap     │
                  │ Questions         │
                  │ Message generation│
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │ Chrome Extension  │
                  │ Final result      │
                  └─────────┬─────────┘
                            │
                            ▼
                     User reviews
                     and sends
```

---

# Why two LLM calls?

The first version attempted to make one LLM call do everything:

```text
LinkedIn research
+
candidate analysis
+
resume selection
+
hiring detection
+
message generation
```

This caused the model to mix unrelated information.

The current design separates the responsibilities.

## Call 1 — LinkedIn Research

Call 1 only tries to understand the LinkedIn person.

It extracts:

* person
* current role
* company
* person type
* company description
* hiring opportunities
* current projects
* recent relevant topics
* connection points
* useful facts
* warnings

It does **not** decide the final message.

It does **not** treat the LinkedIn person as the candidate.

---

## Resume retrieval

Python performs lightweight resume retrieval/ranking.

This is not the final decision.

It is used to reduce the amount of resume information that needs to be passed to the local LLM when necessary.

For example:

```text
Machine Learning Engineer
        │
        ▼
Local retrieval
        │
        ├── ai_ml_resume.pdf
        └── software_engineer_resume.pdf
```

The LLM can then make the final decision.

---

## Call 2 — Final Decision

Call 2 receives:

* candidate profile
* LinkedIn research
* intent
* tone
* custom goal
* extra context
* relevant resume information

It decides:

* fit
* confidence
* selected resume
* resume reason
* relevant overlap
* useful questions
* reasons
* missing information
* final message

The user only sees the final result.

---

# Technology

## Frontend

* Chrome Extension
* JavaScript
* HTML
* CSS

## Backend

* Python
* FastAPI
* Pydantic
* pypdf
* Requests

## LLM

* Ollama
* Qwen3 4B
* Q4_K_M

The model runs locally.

---

# Local model

Current model:

```text
qwen3:4b
```

Ollama runs at:

```text
http://127.0.0.1:11434
```

The backend communicates with:

```text
http://127.0.0.1:11434/api/chat
```

The current configuration uses approximately:

```text
stream: false
think: false
temperature: 0.2
timeout: 240 seconds
```

The exact model can be changed later if the backend configuration supports it.

---

# Project structure

```text
founder-outreach/
│
├── extension/
│   ├── manifest.json
│   ├── content.js
│   ├── content.css
│   ├── popup.html
│   ├── popup.js
│   └── service-worker.js
│
└── backend/
    ├── main.py
    ├── profile.json
    ├── requirements.txt
    ├── .env
    │
    └── resumes/
        ├── ai_ml_resume.pdf
        ├── software_engineer_resume.pdf
        ├── backend_resume.pdf
        ├── business_analyst_resume.pdf
        ├── fullstack_resume.pdf
        └── product_resume.pdf
```

---

# Candidate profile

The candidate's information is stored in:

```text
backend/profile.json
```

Current profile:

```json
{
  "name": "Swayam Gupta",
  "education": "B.Tech CSE",
  "stage": "4th-year student",
  "location": "India",
  "general_preferences": {
    "message_style": "short, natural, direct, human",
    "avoid": [
      "passionate",
      "dream company",
      "inspired by your journey",
      "honored",
      "I came across your profile",
      "generic flattery",
      "fake familiarity",
      "exaggeration",
      "AI-sounding language"
    ],
    "maximum_connection_message_characters": 280
  }
}
```

This information is used by the final LLM when deciding how to communicate.

---

# Resumes

The system currently supports six resumes:

```text
ai_ml_resume.pdf
software_engineer_resume.pdf
backend_resume.pdf
business_analyst_resume.pdf
fullstack_resume.pdf
product_resume.pdf
```

The goal is for the system to automatically choose the most relevant resume based on the actual opportunity and context.

The user should not have to manually select one.

---

# Chrome extension flow

When a LinkedIn page is open:

```text
⚡ Copilot
```

appears on the page.

Clicking it opens the Copilot panel.

The user selects:

```text
Intent
Tone
Optional extra context
```

and clicks:

```text
Analyze person →
```

The extension extracts relevant profile information and sends it to:

```text
POST http://127.0.0.1:8000/screen
```

The returned result is displayed in the panel.

---

# Profile extraction

The first implementation used:

```javascript
document.body.innerText
```

This caused problems because a LinkedIn page can contain unrelated information such as:

* recommended people
* sidebar content
* unrelated posts
* other profiles
* navigation
* unrelated hiring information

The newer implementation attempts to extract structured information:

```text
profile_name
profile_headline
profile_location
mainText
hiringSignals
```

It prefers the main profile content over the entire document.

Explicit hiring signals are extracted separately.

This reduces contamination from unrelated LinkedIn page content.

---

# `/screen` request

The extension sends approximately:

```json
{
  "page_url": "...",
  "page_title": "...",
  "page_text": "...",
  "profile_name": "...",
  "profile_headline": "...",
  "profile_location": "...",
  "hiring_signals": [],
  "intent": "network",
  "custom_goal": "",
  "extra_context": "",
  "tone": "professional"
}
```

The current limits are approximately:

```text
page_text:       30,000 characters
custom_goal:      5,000 characters
extra_context:   15,000 characters
```

---

# Call 1 input

Call 1 receives structured profile information such as:

```text
LINKEDIN PROFILE

Name:
Soman Khazharey R.C.

Headline:
Founder @ Ecostel | Incubated in IITM | Help product companies and hardware startup to build products and bring to the market.

Location:
Bengaluru, Karnataka, India

EXPLICIT HIRING SIGNALS:
Hiring: Machine Learning Engineer

PROFILE CONTENT:
...
```

It also receives the selected interaction intent.

---

# Call 1 output

The intended structure is:

```json
{
  "person": "...",
  "current_role": "...",
  "company": "...",
  "person_type": "...",
  "company_description": "...",
  "hiring_opportunities": [
    {
      "role": "...",
      "company": "...",
      "location": "...",
      "work_mode": "...",
      "description": "...",
      "evidence": "..."
    }
  ],
  "current_projects": [],
  "recent_topics": [],
  "connection_points": [],
  "useful_facts": [],
  "warnings": []
}
```

The exact implementation can evolve, but these responsibilities should remain separate.

---

# Call 2 input

Call 2 receives:

```text
Candidate profile
+
LinkedIn research
+
Intent
+
Tone
+
Custom goal
+
Extra context
+
Relevant resumes
```

The critical instruction is:

```text
The LinkedIn person and candidate are different people by design.
Do not treat different names as a mismatch.
```

---

# Call 2 output

The final response should contain:

```text
fit
confidence

selected_resume
resume_reason

relevant_overlap
things_to_ask
reasons

message

missing_information
warnings
```

The extension additionally displays:

```text
person
current_role
company
hiring_signal
detected_opportunity
```

---

# Example regression test

A key test case is:

```text
Soman Khazharey R.C.
Founder @ Ecostel
Hiring: Machine Learning Engineer
```

The candidate is:

```text
Swayam Gupta
4th-year B.Tech CSE
```

The system should identify:

```text
Person:
Soman Khazharey R.C.

Role:
Founder @ Ecostel

Company:
Ecostel

Hiring:
Machine Learning Engineer

Relevant resume:
ai_ml_resume.pdf
```

It should NOT conclude:

```text
Soman != Swayam
therefore candidate mismatch
```

That would be incorrect.

---

# Important known bugs

## 1. Hiring signal can be overridden by unrelated content

A previous test returned:

```text
Founder's Office Associate @ Ecostel
```

even though the profile explicitly showed:

```text
Hiring: Machine Learning Engineer
```

The system was picking up another hiring-related piece of page content and incorrectly treating it as the main opportunity.

### Fix direction

Explicit hiring signals need higher priority.

---

## 2. Random page content can become "useful facts"

The system previously returned facts about:

* MSME heat stress
* Tejas Mk1A
* unrelated engineering topics

These came from page/post content but were not necessarily useful for contacting the founder.

### Fix direction

Useful facts should be filtered based on:

```text
person relevance
company relevance
intent relevance
outreach usefulness
```

---

## 3. Internal scoring leaked into the UI

The output contained:

```text
LOCAL RELEVANCE SCORE is 6
```

This should never be shown to the user.

The score can exist internally for retrieval, but the user should receive a human-readable reason.

---

## 4. Wrong resume selected

The previous result selected:

```text
fullstack_resume.pdf
```

for:

```text
Machine Learning Engineer
```

The expected relevant resume is:

```text
ai_ml_resume.pdf
```

The wrong opportunity detection contributed to this mistake.

---

## 5. `not_applicable` was incorrectly returned

The system returned:

```text
not_applicable
```

despite an explicit:

```text
Hiring: Machine Learning Engineer
```

This should be corrected.

---

## 6. Final message contained reasoning instead of outreach

The model generated messages such as:

```text
The candidate has strong full-stack and AI/ML skills...
```

This is not a LinkedIn message.

The final message must be directly usable by the user.

---

# Important design rule for hiring detection

Hiring evidence should be prioritized:

```text
1. Explicit profile hiring signal
2. Explicit hiring post
3. Explicit job listing/recruitment information
4. Other attributed hiring evidence
5. Inferred opportunity
```

If an explicit profile signal exists:

```text
Hiring: Machine Learning Engineer
```

the system should not replace it with a weaker inferred opportunity.

---

# Important design rule for facts

Do not return facts just to fill the UI.

A fact should be included only if it is:

```text
Supported by the page
AND
Relevant to the person/company
AND
Useful for the selected interaction
```

It is better to return two strong facts than ten random ones.

---

# Important design rule for resume selection

The user should not manually select a resume.

The intended process is:

```text
LinkedIn opportunity
        ↓
Relevant role/context
        ↓
Resume retrieval
        ↓
LLM final decision
```

The local ranker is only a retrieval mechanism.

It should not be treated as the final source of truth.

---

# Performance consideration

The local model is:

```text
Qwen3 4B
```

Running locally.

Passing all six resumes plus a large LinkedIn page to the model can create a large context and slow inference.

The current implementation can pass all resumes to the final decision stage, but this may need optimization.

A better future approach is:

```text
Call 1
   ↓
Research
   ↓
Local resume retrieval
   ↓
Top 2 resumes
   ↓
Call 2
   ↓
Final LLM decision
```

This preserves automatic resume selection while reducing context size.

The user should still never be asked to choose the resume.

---

# Installation

## 1. Install Ollama

Install Ollama for the local machine.

Then pull the model:

```bash
ollama pull qwen3:4b
```

Verify:

```bash
ollama list
```

The model should appear as:

```text
qwen3:4b
```

---

## 2. Start Ollama

Make sure Ollama is running.

The expected API endpoint is:

```text
http://127.0.0.1:11434
```

---

## 3. Set up the backend

Open:

```text
backend/
```

Create/activate a Python virtual environment.

Windows example:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 4. Start FastAPI

From the backend directory:

```bash
uvicorn main:app --reload --port 8000
```

The backend should be available at:

```text
http://127.0.0.1:8000
```

Check:

```text
http://127.0.0.1:8000/health
```

Expected result:

```json
{
  "ok": true,
  "ollama": true,
  "model": "qwen3:4b"
}
```

---

# Installing the Chrome extension

Open Chrome:

```text
chrome://extensions/
```

Enable:

```text
Developer mode
```

Choose:

```text
Load unpacked
```

Select:

```text
founder-outreach/extension/
```

Open a LinkedIn profile.

The Copilot launcher should appear.

---

# Typical usage

1. Open a LinkedIn profile.
2. Wait for the profile to load.
3. Click:

```text
⚡ Copilot
```

4. Select an intent.
5. Select a tone.
6. Optionally enter additional context.
7. Click:

```text
Analyze person →
```

8. Wait for the local model to process the page.
9. Review:

   * person
   * role/company
   * opportunity
   * resume
   * overlap
   * questions
   * message
10. Copy the message if useful.
11. Manually send it on LinkedIn.

---

# No automatic messaging

This project intentionally does not automatically send LinkedIn messages.

The Copilot only assists with:

```text
research
analysis
resume selection
message generation
```

The final decision and sending action remain with the user.

---

# Development philosophy

The project is intentionally local-first.

Preferred:

```text
local LLM
local FastAPI
local resume files
local processing
```

rather than requiring paid AI APIs or external infrastructure.

The goal is to make the tool useful without sending private resume/profile context to a third-party LLM API.

---

# Current limitations

The system is a prototype and LinkedIn's DOM can change.

Potential problems include:

* LinkedIn changing CSS/selectors
* hidden/stale DOM content
* profile content loaded dynamically
* unrelated page content leaking into extraction
* local LLM inference latency
* Qwen3 4B occasionally making incorrect inferences
* large resume/page context increasing latency
* LinkedIn UI variations between profiles

The extraction layer should therefore remain separate from the reasoning layer.

---

# Debugging

If the extension does not work:

### Check Ollama

Verify that:

```text
qwen3:4b
```

exists and Ollama is running.

### Check backend

Open:

```text
http://127.0.0.1:8000/health
```

Expected:

```json
{
  "ok": true,
  "ollama": true,
  "model": "qwen3:4b"
}
```

### Check Chrome

Open:

```text
chrome://extensions/
```

and inspect the extension for errors.

### Check backend terminal

The FastAPI terminal should show the incoming `/screen` request and any exceptions.

---

# Current priority for development

The next improvements should focus on correctness rather than adding more UI features.

Priority:

```text
1. Correct explicit hiring detection
2. Prevent random page content from becoming important facts
3. Fix automatic resume selection
4. Prevent internal reasoning from leaking into output
5. Improve final LinkedIn message quality
6. Reduce LLM context/latency
7. Add more regression tests
```

Do not add unnecessary features before these are reliable.

---

# Desired final behavior

For a profile like:

```text
Soman Khazharey R.C.
Founder @ Ecostel
Hiring: Machine Learning Engineer
```

the Copilot should effectively understand:

```text
Who is this?
→ Founder at Ecostel

What is important?
→ Explicitly hiring a Machine Learning Engineer

Which resume matters?
→ ai_ml_resume.pdf

What does Swayam have that's relevant?
→ Actual AI/ML experience from the resume

What should Swayam say?
→ A short, natural message based on the real evidence
```

The user should not need to perform any of that reasoning manually.

---

# Guiding rules

The most important rules for future development are:

```text
LINKEDIN PERSON ≠ CANDIDATE

EXPLICIT EVIDENCE > INFERENCE > RANDOM PAGE CONTENT

RETRIEVAL SCORE ≠ FINAL DECISION

INTERNAL REASONING ≠ USER-FACING MESSAGE

RESEARCH FIRST → DECIDE SECOND → WRITE LAST

USER REVIEWS MESSAGE → USER SENDS MESSAGE
```

These rules should remain intact even if the implementation changes.

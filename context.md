# Personal LinkedIn Copilot — Complete Project Context

## 1. Project goal

I am building a **Personal LinkedIn Copilot** as a Chrome extension + local FastAPI backend + local Ollama LLM.

The purpose is:

> Given the LinkedIn profile/page currently open in Chrome, research the person, understand why I am interacting with them, identify relevant hiring/opportunity signals, determine which of my resumes is relevant, find genuine overlap/context, and draft a natural LinkedIn message.

The user must **never have to manually inspect intermediate AI reasoning**.

The system can internally make multiple calls and perform research/selection, but the user should ultimately see:

* who the person is
* their current role/company
* relevant hiring/opportunity
* selected resume
* useful overlap/facts
* things worth asking
* warnings/missing information
* a natural final LinkedIn message

The user manually reviews/copies/sends the message.

The extension must **NOT automatically send LinkedIn messages**.

---

# 2. Main design principle

The copilot should do the work itself.

The user should NOT have to answer things like:

> "Which resume should I use?"

or

> "What job is this person hiring for?"

or

> "Which part of their profile should I look at?"

The system should inspect the page and decide.

The user only chooses the **interaction intent** and optionally provides extra context.

---

# 3. Current UI

Current UI is:

```text
Personal LinkedIn Copilot
Research the person. Pick your intent. Write naturally.
×

What do you want from this interaction?

💼 Job opportunity
Check hiring, fit and relevant resume.

🚀 Founder
Research the founder, company and best way to approach.

🤝 Network
Find genuine overlap and connect.

💬 Ask for advice
Find something specific to ask.

✏️ Custom
Tell the copilot exactly what you want.

Tone

Natural
Casual
Professional
Technical
Direct

Extra context (optional)

Paste a hiring post, message, role description, something you noticed, or any context you want the AI to know.

Analyze person →
```

After analysis:

```text
Person
Current role · Company

Hiring / opportunity
...

Resume selected
...

Relevant overlap
...

Useful facts
...

Things you could ask
...

Why
...

Message
...

Copy
Shorter

Missing information
...

Warnings
...

Confidence: ...
```

The user wants this UI concept retained.

---

# 4. Interaction intents

There are currently five presets:

```text
job
founder
network
advice
custom
```

### Job opportunity

Meaning:

> Check whether this person/company is hiring, identify relevant roles, assess fit, and choose the relevant resume.

### Founder

Meaning:

> Research the founder/company and determine the best natural way to approach them.

Important:

"Founder" is primarily an interaction/person-type context, NOT automatically a job request.

However, if the founder is explicitly hiring, that hiring signal should still be surfaced.

### Network

Meaning:

> Find genuine overlap and suggest a natural networking approach.

### Ask for advice

Meaning:

> Find something specific and legitimate to ask this person based on their background.

### Custom

The user can describe exactly what they want.

Example:

```text
I want to talk to this person about backend engineering and ask how they got into distributed systems.
```

---

# 5. Tone options

Current options:

```text
natural
casual
professional
technical
direct
```

The user's preferred general style is:

```text
short
natural
direct
human
```

Avoid AI-sounding LinkedIn writing.

---

# 6. User profile

Current `profile.json`:

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

The candidate is Swayam Gupta.

This is critical:

> The LinkedIn person and the candidate are normally two completely different people.

For example:

```text
LinkedIn person:
Soman Khazharey R.C.

Candidate:
Swayam Gupta
```

This is NOT a mismatch.

The model previously incorrectly interpreted different names as a candidate/profile mismatch. That behavior must never happen.

---

# 7. Candidate resumes

There are six resumes.

Backend folder:

```text
backend/
└── resumes/
    ├── ai_ml_resume.pdf
    ├── software_engineer_resume.pdf
    ├── backend_resume.pdf
    ├── business_analyst_resume.pdf
    ├── fullstack_resume.pdf
    └── product_resume.pdf
```

The copilot should choose among these automatically.

The user should not have to manually select the resume.

---

# 8. Project structure

Current project structure:

```text
founder-outreach/
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
    └── resumes/
        ├── ai_ml_resume.pdf
        ├── software_engineer_resume.pdf
        ├── backend_resume.pdf
        ├── business_analyst_resume.pdf
        ├── fullstack_resume.pdf
        └── product_resume.pdf
```

The main active UI logic is in:

```text
extension/content.js
```

The backend logic is in:

```text
backend/main.py
```

---

# 9. Local LLM setup

The project intentionally uses a local model.

Ollama is installed and working.

Current model:

```text
qwen3:4b
```

Approximate model size:

```text
~2.5 GB
```

Quantization:

```text
Q4_K_M
```

Hardware for this test:

```text
RTX 3050
```

Ollama endpoint:

```text
http://127.0.0.1:11434
```

The model was tested with:

```text
ollama run qwen3:4b "Reply with only: OK"
```

It returned:

```text
OK
```

and took roughly 2 seconds for that tiny request.

Ollama model listing confirmed:

```text
qwen3:4b
```

---

# 10. FastAPI backend

Backend runs locally on:

```text
http://127.0.0.1:8000
```

Health endpoint:

```text
GET /health
```

Returned:

```json
{
  "ok": true,
  "ollama": true,
  "model": "qwen3:4b"
}
```

The backend communicates with Ollama through:

```text
http://127.0.0.1:11434/api/chat
```

Current Ollama request behavior:

```text
stream = false
think = false
temperature = 0.2
timeout = 240 seconds
```

Structured JSON/schema output is used.

---

# 11. High-level architecture

Current intended architecture:

```text
                 LinkedIn page
                      │
                      ▼
             Chrome Extension
                      │
                      │ profile/page data
                      ▼
                FastAPI backend
                      │
          ┌───────────┴────────────┐
          │                        │
          ▼                        ▼
      LLM Call 1              Local resume
   LinkedIn research            ranking
          │                        │
          └───────────┬────────────┘
                      ▼
                LLM Call 2
            final decision maker
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Resume      reasoning    message
       choice       context      draft
                      │
                      ▼
                Chrome UI
                      │
                      ▼
               User reviews/copies
```

Important:

There are two LLM calls.

The user does NOT see Call 1.

The user does NOT see Call 2 reasoning.

Only the final result is displayed.

---

# 12. Why two LLM calls

The first version used one giant LLM call containing:

* LinkedIn page
* candidate information
* resume
* intent
* message generation

This caused bad behavior.

The model mixed together:

* the LinkedIn person
* candidate identity
* arbitrary page content
* resume selection
* hiring detection
* message writing

The solution was to separate the responsibilities.

---

# 13. LLM Call 1 — LinkedIn research

Call 1's job is ONLY to understand the LinkedIn person/page.

It should determine:

```text
person
current_role
company
person_type
company_description
hiring_opportunities
current_projects
recent_topics
connection_points
useful_facts
warnings
```

It receives:

```text
profile header
explicit hiring signals
full relevant profile content
user intent
custom goal
```

It should NOT decide the final message.

It should NOT judge the candidate's resume.

It should NOT treat the LinkedIn person as the candidate.

---

# 14. LinkedIn research output

Conceptually:

```json
{
  "person": "Soman Khazharey R.C.",
  "current_role": "Founder @ Ecostel",
  "company": "Ecostel",
  "person_type": "Founder",
  "company_description": "...",
  "hiring_opportunities": [
    {
      "role": "Machine Learning Engineer",
      "company": "Ecostel",
      "location": "...",
      "work_mode": "...",
      "description": "...",
      "evidence": "Hiring: Machine Learning Engineer"
    }
  ],
  "current_projects": [],
  "recent_topics": [],
  "connection_points": [],
  "useful_facts": [],
  "warnings": []
}
```

Exact fields may vary depending on the current implementation, but this is the intended semantic structure.

---

# 15. Chrome extraction problem

The first version simply did:

```javascript
document.body.innerText
```

This was a problem.

LinkedIn pages contain lots of unrelated material:

* sidebar recommendations
* suggested people
* other profiles
* posts
* navigation
* unrelated job information
* page elements not belonging to the actual person

The LLM therefore received a noisy page.

This caused the model to confuse people and opportunities.

---

# 16. Current extraction approach

The newer `content.js` introduced:

```javascript
getProfileData()
```

Instead of blindly sending the entire document, it attempts to extract:

```text
name
headline
location
mainText
hiringSignals
```

The important idea is:

```text
main
```

is preferred over:

```text
document.body
```

because the main profile content is more useful than the entire page.

The extension also scans links/page content for explicit hiring signals and sends them separately.

---

# 17. Current request sent by extension

The `/screen` request now contains roughly:

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

`page_text` is currently capped around:

```text
30000 characters
```

Custom goal:

```text
5000 characters
```

Extra context:

```text
15000 characters
```

---

# 18. Current content.js behavior

The extension:

1. Creates a floating `⚡ Copilot` button.
2. Clicking it opens the panel.
3. User selects intent.
4. User selects tone.
5. User optionally enters extra context.
6. User clicks Analyze.
7. Extension extracts LinkedIn profile information.
8. Sends it to FastAPI.
9. Backend performs research/decision.
10. Result is rendered in the panel.
11. User can copy the message.
12. User can use the Shorter button.
13. User manually sends the message on LinkedIn.

It does not send messages automatically.

---

# 19. Resume extraction

Backend uses PDF parsing through:

```text
pypdf
```

The six resumes are loaded from:

```text
backend/resumes/
```

Resume text is extracted and made available to the decision stage.

---

# 20. Local resume ranking

There is currently a lightweight local ranker.

It has role/context keyword mappings such as:

```python
ROLE_KEYWORDS
```

The mapping includes categories such as:

```text
AI/ML
backend
fullstack
software engineering
business analyst
product
```

Importantly, it now includes:

```text
machine learning engineer
```

under AI/ML.

The local ranker gives a relevance score based on:

* context match
* keyword matches in resume

Conceptually:

```text
+5 for context/category match
+1 for keyword match
```

The ranker is intended to be a **retrieval/relevance signal**, not the final decision maker.

---

# 21. Final decision LLM — Call 2

Call 2 is the actual decision-making stage.

It receives:

```text
candidate profile
user intent
custom goal
tone
extra context
Call 1 research
resume information
local resume relevance signals
```

The intended job of Call 2 is to decide:

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
```

The LLM should make the final resume selection.

The local score should NOT be treated as truth.

---

# 22. Critical candidate/profile distinction

Call 2 explicitly needs to know:

```text
Candidate:
Swayam Gupta

LinkedIn person:
the person currently being researched
```

These are intentionally different.

Example:

```text
LinkedIn person:
Soman Khazharey R.C.

Candidate:
Swayam Gupta
```

This is normal.

Never say:

```text
Candidate mismatch because LinkedIn person has a different name.
```

That was a major bug in an earlier version.

---

# 23. Final response schema

The final backend response contains approximately:

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
person
current_role
company
hiring_signal
detected_opportunity
```

The extension renders these fields.

---

# 24. Major mistake #1 — identity confusion

### Bad behavior

The model saw:

```text
Soman Khazharey R.C.
```

and candidate:

```text
Swayam Gupta
```

and treated this as a mismatch.

### Why this is wrong

The entire purpose of the tool is to research another LinkedIn person.

Different names are expected.

### Fix

The prompts explicitly say:

> The LinkedIn person and candidate are different people by design.

Example:

> Soman Khazharey R.C. vs Swayam Gupta is NOT a mismatch.

---

# 25. Major mistake #2 — arbitrary hiring opportunity

Current test page:

```text
Soman Khazharey R.C.
· 1st

Founder @ Ecostel | Incubated in IITM | Help product companies and hardware startup to build products and bring to the market.

Bengaluru, Karnataka, India

Contact info

Ecostel
Rajalakshmi Institute of Technology
www.ecostel.co

4,840 followers
500+ connections

Message

- Hiring: Machine Learning Engine...
```

The important hiring signal is:

```text
Hiring: Machine Learning Engineer
```

However, the current system produced:

```text
Founder's Office Associate @ Ecostel
```

as the detected opportunity.

This indicates that the model found another hiring-related piece of content somewhere in the page and incorrectly promoted it over the explicit profile hiring signal.

### Required fix

Hiring evidence must be prioritized.

Priority should conceptually be:

```text
1. Explicit profile hiring signal
2. Explicit recent hiring post
3. Explicit job listing/recruitment content
4. Other clearly attributed hiring evidence
5. Inferred opportunity
```

If the page explicitly says:

```text
Hiring: Machine Learning Engineer
```

that should dominate unrelated hiring information.

---

# 26. Major mistake #3 — random "useful facts"

The current output produced things like:

```text
92% of surveyed MSMEs in Coimbatore, Chennai, and Surat experienced operational disruptions due to heat stress
```

and:

```text
The Tejas Mk1A fighter jet program in India faces constraints due to engine availability, not aircraft assembly
```

and:

```text
Ecostel has rebuilt electronics supply chains
```

The first two are not necessarily useful for contacting the founder.

The model is treating arbitrary page/post content as equally important.

### Required fix

"Useful facts" must be filtered based on:

```text
person relevance
company relevance
intent relevance
message usefulness
```

A random post should not automatically become a useful outreach fact.

For a founder interaction, useful facts should preferably relate to:

* company
* founder's work
* current product
* hiring
* technology
* relevant project
* clearly stated business focus
* a genuine connection point

---

# 27. Major mistake #4 — internal reasoning leaking into final output

Current output says:

```text
The LOCAL RELEVANCE SCORE is 6...
```

This is bad.

The user should never see internal retrieval/scoring machinery.

The final UI should NOT mention:

```text
LOCAL RELEVANCE SCORE
```

or:

```text
The model thinks...
```

or internal ranking details.

Instead:

```text
Resume selected:
ai_ml_resume.pdf

Why:
Your AI/ML resume is the closest match to the Machine Learning Engineer opening.
```

The implementation can still use scores internally.

---

# 28. Major mistake #5 — wrong resume selection

For the Soman/Ecostel example, the system selected:

```text
fullstack_resume.pdf
```

while the explicit opportunity is:

```text
Machine Learning Engineer
```

The user's relevant resume is expected to be:

```text
ai_ml_resume.pdf
```

The model instead focused on the wrong opportunity and therefore made the wrong resume decision.

### Required fix

Correct hiring detection should happen BEFORE resume selection.

Correct flow:

```text
Explicit hiring signal
        ↓
Machine Learning Engineer
        ↓
AI/ML context
        ↓
ai_ml_resume.pdf
```

not:

```text
Random page content
        ↓
Founder's Office Associate
        ↓
Full-stack-ish interpretation
        ↓
fullstack_resume.pdf
```

---

# 29. Major mistake #6 — `not_applicable` when an obvious opportunity exists

The current output was:

```text
not_applicable
```

even though the page explicitly showed:

```text
Hiring: Machine Learning Engineer
```

This is another consequence of incorrect opportunity extraction.

The presence of an explicit relevant hiring signal should strongly affect the result.

---

# 30. Major mistake #7 — unnatural final message

Current bad message was essentially:

```text
The candidate has strong full-stack and AI/ML skills, but the specific role (ML Engineer at Ecostel) isn't clearly supported by the resume. The LOCAL RELEVANCE SCORE is 6...
```

This is not a LinkedIn outreach message.

It is an explanation to the developer/user.

### Correct behavior

The message should sound like a human contacting the founder.

For example, conceptually:

```text
Hi Soman, saw that Ecostel is hiring for an ML Engineer. I'm a 4th-year CSE student working on AI/ML and would love to understand what you're looking for in the role. Would be great to connect.
```

The exact wording should be generated from the actual resume/profile/context.

The model should never write:

```text
The candidate...
```

inside the LinkedIn message.

---

# 31. Major architectural decision

Do NOT solve this by making the user manually select a resume.

The entire point of the copilot is automatic research and decision-making.

The user should not have to inspect:

```text
Call 1 research
resume ranking
model reasoning
tool calls
```

The user only reviews:

```text
final answer
```

---

# 32. Another important architectural constraint

The current implementation gives Call 2 access to all six resumes.

Conceptually:

```text
Candidate profile
+
Research
+
all six resumes
+
local relevance signals
```

This allows the LLM to make the final choice.

However, there is a performance concern.

The Qwen 3 4B model is running locally on an RTX 3050.

Sending:

```text
six full resumes
+
large LinkedIn page
+
research
```

can become expensive in context and inference time.

An earlier large request took long enough to approach the:

```text
240 second
```

timeout.

Therefore this is an important future optimization.

---

# 33. Recommended performance optimization

Do NOT ask the user to choose the resume.

Instead:

```text
Call 1
   ↓
research opportunity
   ↓
local ranker retrieves top 2 resumes
   ↓
Call 2 receives top 2
   ↓
LLM makes final decision
```

The local ranker is only narrowing retrieval.

The LLM still makes the final choice.

For example:

```text
Machine Learning Engineer
        ↓
local ranker:
1. ai_ml_resume.pdf
2. software_engineer_resume.pdf
        ↓
LLM decides:
ai_ml_resume.pdf
```

This preserves automatic behavior while reducing context size.

---

# 34. Important distinction: retrieval vs reasoning

The local ranker should be treated as:

```text
retrieval
```

not:

```text
final reasoning
```

Its job:

> Find the most plausible resumes to give the LLM.

The LLM's job:

> Decide which resume actually fits.

This is important because the user explicitly wants the AI to make the final decision rather than relying on a crude keyword score.

---

# 35. Current `content.js` extraction behavior

The earlier implementation had:

```javascript
function cleanText(text) {
  return (text || "")
    .replace(/\u00a0/g, " ")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
```

and:

```javascript
function getVisiblePageText() {
  return cleanText(document.body?.innerText || "");
}
```

That was replaced/improved with a more structured `getProfileData()` approach.

The newer approach extracts:

```text
profile_name
profile_headline
profile_location
mainText
hiringSignals
```

and sends these separately.

The UI itself stayed essentially the same.

---

# 36. Current content.js UI implementation details

The launcher is:

```text
⚡ Copilot
```

It uses:

```text
#foc-launcher
#foc-panel
```

The extension prevents duplicate initialization with:

```javascript
window.__FOC_INITIALIZED__
```

The panel has:

```text
foc-header
foc-body
foc-label
foc-intent-grid
foc-intent
foc-input
foc-select
foc-analyze
foc-result
foc-card
foc-message
foc-actions
foc-confidence
```

The user can:

```text
Copy
Shorter
Analyze again
```

---

# 37. Current `/screen` flow

Backend roughly does:

```text
receive ScreenRequest
        ↓
research_linkedin()
        ↓
extract role/company/opportunity/context
        ↓
rank_resumes()
        ↓
make_decision()
        ↓
construct final response
        ↓
return ScreenResponse
```

---

# 38. `ScreenRequest` fields

Current conceptual schema:

```python
page_url: str
page_title: str
page_text: str

profile_name: str
profile_headline: str
profile_location: str

hiring_signals: list[HiringSignal]

intent: str
custom_goal: str
extra_context: str
tone: str
```

One implementation detail to improve:

Instead of:

```python
hiring_signals: list[HiringSignal] = []
```

prefer:

```python
from pydantic import Field

hiring_signals: list[HiringSignal] = Field(default_factory=list)
```

This avoids a mutable default.

---

# 39. Current `ScreenResponse` concept

Final response includes:

```text
person
current_role
company

fit
confidence

hiring_signal
detected_opportunity

selected_resume
resume_reason

relevant_overlap
useful_facts
things_to_ask
reasons

message

missing_information
warnings
```

---

# 40. Current Call 1 context

Call 1 should receive something similar to:

```text
LINKEDIN PROFILE HEADER

Name:
Soman Khazharey R.C.

Headline:
Founder @ Ecostel | Incubated in IITM | Help product companies and hardware startup to build products and bring to the market.

Location:
Bengaluru, Karnataka, India

EXPLICIT HIRING SIGNALS

Hiring: Machine Learning Engineer

PROFILE CONTENT

...

USER INTENT

Founder / Job / Network / Advice / Custom

CUSTOM GOAL

...

TASK

Research ONLY the LinkedIn person.

Do not treat the LinkedIn person as the candidate.

Identify explicit hiring opportunities and distinguish them from generic posts.

Do not invent opportunities.

Prioritize explicit hiring evidence.

Return structured JSON.
```

---

# 41. Call 2 context

Call 2 should receive:

```text
CANDIDATE PROFILE

Name:
Swayam Gupta

Education:
B.Tech CSE

Stage:
4th-year student

Location:
India

Candidate preferences:
short, natural, direct, human

LINKEDIN RESEARCH

...

USER INTENT

...

TONE

...

CUSTOM GOAL

...

EXTRA CONTEXT

...

CANDIDATE RESUMES

Resume A:
...

Resume B:
...

...

TASK

Choose the most relevant resume.

Evaluate fit using the actual opportunity.

Do not treat different names between candidate and LinkedIn person as a mismatch.

Do not expose internal scores.

Do not mention internal reasoning in the LinkedIn message.

Write a natural message.

Use only supported facts.

Do not invent experience.

Return structured JSON.
```

---

# 42. Final message constraints

The generated LinkedIn message should:

* sound human
* be short
* be direct
* use real information
* avoid generic flattery
* avoid fake familiarity
* avoid "I came across your profile"
* avoid "passionate"
* avoid "dream company"
* avoid "inspired by your journey"
* avoid "honored"
* avoid exaggerated claims
* avoid AI-style language
* avoid explaining internal reasoning
* avoid saying "the candidate"
* avoid mentioning relevance scores
* avoid claiming experience not present in the resume
* stay within approximately 280 characters when it is a connection request

---

# 43. What the model must NOT do

Never:

```text
invent a job
```

Never:

```text
invent a company project
```

Never:

```text
assume every post is relevant
```

Never:

```text
treat LinkedIn person's name as candidate identity
```

Never:

```text
show internal scoring
```

Never:

```text
use arbitrary page facts just to fill "useful facts"
```

Never:

```text
make the user manually choose the resume
```

Never:

```text
write a message explaining its own reasoning
```

Never:

```text
claim unsupported experience
```

Never:

```text
automatically send the LinkedIn message
```

---

# 44. The Soman/Ecostel test case

This is the most important current regression test.

Input page:

```text
Soman Khazharey R.C
· 1st

Founder @ Ecostel | Incubated in IITM | Help product companies and hardware startup to build products and bring to the market.

Bengaluru, Karnataka, India

Contact info

Ecostel
Rajalakshmi Institute of Technology
www.ecostel.co

4,840 followers
500+ connections

Message

- Hiring: Machine Learning Engineer
```

Expected identity:

```text
person:
Soman Khazharey R.C.

current_role:
Founder @ Ecostel

company:
Ecostel

person_type:
Founder
```

Expected explicit hiring signal:

```text
Machine Learning Engineer
```

Expected relevant resume:

```text
ai_ml_resume.pdf
```

Expected behavior:

```text
Do not mark candidate mismatch because Soman != Swayam.
```

Expected final output should NOT claim:

```text
Founder's Office Associate
```

unless that is independently confirmed as a higher-priority explicit opportunity.

It should NOT produce random facts about:

```text
Tejas Mk1A
heat stress
MSME survey
```

unless they are genuinely relevant to the selected interaction.

It should NOT mention:

```text
LOCAL RELEVANCE SCORE
```

anywhere in the user-facing result.

---

# 45. Example of correct final result shape for Soman

Conceptually:

```text
Soman Khazharey R.C.
Founder @ Ecostel · Ecostel

Hiring / opportunity
Machine Learning Engineer

Resume selected
ai_ml_resume.pdf

Why
Your AI/ML resume is the closest match to the Machine Learning Engineer opening.

Relevant overlap
- AI/ML experience
- Relevant engineering/project work
- Any genuine Ecostel/company overlap found from the actual resume/profile

Useful facts
- Founder @ Ecostel
- Ecostel works with product companies and hardware startups
- Explicitly hiring for Machine Learning Engineer

Things you could ask
- What kind of ML work would the engineer own?
- Is the role more focused on model development, deployment, or product integration?

Message
[short natural LinkedIn message]

Warnings
[Any actual uncertainty]

Confidence
[reasonable confidence]
```

This is illustrative. The actual message/facts must be generated from the real extracted page and resume.

---

# 46. Another problem: "Useful facts" should be intent-dependent

For:

```text
Job
```

useful facts should focus on:

```text
role
requirements
company
hiring
technology
team
work
```

For:

```text
Founder
```

focus on:

```text
founder
company
product
market
current work
specific company/project facts
```

For:

```text
Network
```

focus on:

```text
genuine shared interests
technology
education
projects
location if relevant
professional overlap
```

For:

```text
Advice
```

focus on:

```text
specific experience
career path
technical expertise
questions that person can realistically answer
```

For:

```text
Custom
```

follow the user's custom goal.

---

# 47. "Founder" intent does NOT mean ignore hiring

This is important.

Suppose:

```text
intent = founder
```

and the page says:

```text
Hiring: Machine Learning Engineer
```

The system should still surface:

```text
Hiring / opportunity:
Machine Learning Engineer
```

The intent determines the approach/message.

It does not erase important facts.

---

# 48. User extra context

The extra context box exists because sometimes the user has information that LinkedIn doesn't expose.

Examples:

```text
Paste a hiring post
```

or:

```text
I met this person at a conference.
```

or:

```text
I specifically want to ask about their backend architecture.
```

or:

```text
They accepted my connection request yesterday.
```

This should be incorporated into the final decision.

---

# 49. Important performance issue

Current model:

```text
Qwen3 4B
```

on:

```text
RTX 3050
```

is capable enough for the prototype, but context size matters.

A previous large request with:

```text
large LinkedIn page
+
multiple resumes
```

was slow enough to approach the:

```text
240s
```

timeout.

Therefore:

### Current architecture

```text
Call 1:
large-ish LinkedIn research

Call 2:
research + six resumes
```

### Better architecture if latency becomes a problem

```text
Call 1:
research

Python:
retrieve top 2 resumes

Call 2:
research + top 2 resumes
```

This is preferred over asking the user to select a resume.

---

# 50. Why not one LLM call?

One-call architecture was tested conceptually and produced mixed responsibilities.

Problems:

```text
person identification
+
candidate identity
+
resume matching
+
hiring detection
+
message generation
```

were all mixed together.

Separating research from final decision gives cleaner boundaries:

```text
Call 1 = understand LinkedIn person

Call 2 = decide what Swayam should do
```

This separation should remain.

---

# 51. Why not three/four LLM calls?

There is no need yet.

A possible future architecture could have:

```text
Call 1:
profile research

Call 2:
resume selection

Call 3:
message generation
```

but this increases latency significantly on a local 4B model.

The current two-call architecture is preferable.

The main problem currently is not insufficient LLM calls.

It is **bad input prioritization and bad output discipline**.

---

# 52. Most important next fixes, in order

## Fix 1 — explicit hiring signal priority

If LinkedIn says:

```text
Hiring: Machine Learning Engineer
```

preserve that as a first-class signal.

Do not let arbitrary page content override it.

---

## Fix 2 — clean Call 1 research

Make Call 1 distinguish:

```text
explicit hiring
recent hiring
job listing
inferred
```

and prioritize them.

---

## Fix 3 — useful-fact filtering

Only return facts that are:

```text
relevant
supported
useful for outreach
```

Limit to around 2-5.

---

## Fix 4 — remove internal score from final output

Never expose:

```text
LOCAL RELEVANCE SCORE
```

to the user.

---

## Fix 5 — fix resume selection

For:

```text
Machine Learning Engineer
```

AI/ML resume should be strongly considered.

If all six resumes are passed, the LLM should choose.

If latency becomes bad, locally retrieve top two and let the LLM choose between them.

---

## Fix 6 — message must actually be a message

The output under:

```text
Message
```

must be something the user could paste into LinkedIn.

It must not be an explanation of fit.

---

## Fix 7 — don't overuse `not_applicable`

If there is a genuine hiring opportunity and the user's background has relevant overlap, the result should not casually become:

```text
not_applicable
```

---

# 53. Current known backend issue

The current Pydantic declaration:

```python
hiring_signals: list[HiringSignal] = []
```

should eventually become:

```python
hiring_signals: list[HiringSignal] = Field(default_factory=list)
```

with:

```python
from pydantic import Field
```

This is a code-quality fix rather than the primary behavioral bug.

---

# 54. Potential extraction issue

The newer profile extraction may use selectors such as:

```text
main
.text-body-small
```

The location extraction must be handled carefully.

A generic LinkedIn selector like:

```text
.text-body-small
```

can potentially match unrelated small text.

If location becomes wrong in future tests, use more specific profile-header selectors or structured DOM relationships rather than simply taking the first matching element.

---

# 55. Testing strategy

Do not judge the system based on one successful API call.

Use several LinkedIn page types.

### Test A — Founder + explicit hiring

Expected:

```text
Founder identified correctly
Hiring identified correctly
Relevant resume selected
```

### Test B — Founder, no hiring

Expected:

```text
No fabricated hiring opportunity
```

### Test C — Recruiter + job

Expected:

```text
Role/company/job detected
```

### Test D — Engineer

Expected:

```text
technical overlap
```

### Test E — Advice

Expected:

```text
specific question
```

not a job pitch.

### Test F — No relevant overlap

Expected:

```text
honest weak/limited fit
```

but still a useful message if appropriate.

### Test G — noisy page

Expected:

```text
sidebar/recommended profiles ignored
```

---

# 56. Success criteria

The project is successful when the user can open a LinkedIn profile and do:

```text
Click Copilot
        ↓
Choose intent
        ↓
Choose tone
        ↓
Optional context
        ↓
Analyze
        ↓
Receive useful result
```

without manually doing:

```text
research person
find job
read posts
choose resume
compare resume
write message
```

The user should only verify the final result before sending.

---

# 57. Current status

### Working

```text
Ollama
Qwen3 4B
FastAPI
Chrome extension
LinkedIn extraction
structured LLM calls
candidate profile
multiple resumes
automatic resume selection architecture
final message generation
copy button
tone selection
intent selection
extra context
```

### Improved from previous version

```text
Person identity handling
Main profile extraction
Explicit hiring signal extraction
Two-stage LLM architecture
Candidate/resume distinction
Machine Learning Engineer keyword support
```

### Still broken / needs refinement

```text
Hiring signal prioritization
Random page facts
Resume selection in some cases
Internal score leakage
Message quality in bad-context cases
`not_applicable` classification
Potential context/latency issue with six resumes
```

---

# 58. The key conceptual bug right now

The system has moved from:

> "The model doesn't understand who the LinkedIn person is."

to:

> "The model understands the person, but it doesn't yet reliably distinguish important profile facts from arbitrary page content."

That is the current bottleneck.

The next version should therefore focus on:

```text
signal prioritization
```

rather than adding more features.

---

# 59. Final desired pipeline

The ideal pipeline is:

```text
LinkedIn page
      ↓
structured extraction
      ↓
profile identity
      ↓
explicit hiring detection
      ↓
LLM research
      ↓
relevant opportunity/context
      ↓
resume retrieval
      ↓
LLM final selection
      ↓
fit + overlap + questions
      ↓
natural message
      ↓
user review
```

With the following hard rule:

```text
EXPLICIT LINKEDIN EVIDENCE > INFERRED INFORMATION > RANDOM PAGE CONTENT
```

And another:

```text
FINAL USER MESSAGE ≠ INTERNAL REASONING
```

And another:

```text
LINKEDIN PERSON ≠ CANDIDATE
```

unless the system has actual evidence that they are the same person, which is not the normal use case.

---

# 60. The exact current regression that should be fixed first

Input:

```text
Soman Khazharey R.C.
Founder @ Ecostel
Hiring: Machine Learning Engineer
```

Candidate:

```text
Swayam Gupta
4th-year B.Tech CSE
```

Current bad output:

```text
Founder's Office Associate @ Ecostel
fullstack_resume.pdf
not_applicable
LOCAL RELEVANCE SCORE = 6
random MSME/Tejas facts
message explaining resume mismatch
```

Desired direction:

```text
Soman Khazharey R.C.
Founder @ Ecostel

Hiring / opportunity
Machine Learning Engineer

Resume selected
ai_ml_resume.pdf

Why
AI/ML resume is the most relevant resume for this opening.

Relevant overlap
Actual supported AI/ML overlap from Swayam's resume.

Useful facts
Actual relevant facts about Soman/Ecostel.

Message
Short, natural, human LinkedIn outreach.

No internal scores.
No candidate/person identity confusion.
No random unrelated facts.
No invented job.
```

That regression test should pass before adding more functionality.

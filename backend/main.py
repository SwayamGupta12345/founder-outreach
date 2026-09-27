import json
import os
import re
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pypdf import PdfReader

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
RESUME_DIR = BASE_DIR / "resumes"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

app = FastAPI(title="Personal LinkedIn Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ============================================================
# MODELS
# ============================================================

class HiringSignal(BaseModel):
    text: str = ""
    href: str = ""

class ScreenRequest(BaseModel):
    page_url: str = ""
    page_title: str = ""
    page_text: str = Field(min_length=1, max_length=30000)
    profile_name: str = ""
    profile_headline: str = ""
    profile_location: str = ""
    hiring_signals: list[HiringSignal] = []
    intent: str = "network"
    custom_goal: str = Field(default="", max_length=5000)
    extra_context: str = Field(default="", max_length=15000)
    tone: str = "natural"

class ScreenResponse(BaseModel):
    person: str
    current_role: str
    company: str
    person_type: str
    hiring_signal: str
    detected_opportunity: str
    fit: str
    confidence: str
    selected_resume: str
    resume_reason: str
    relevant_overlap: list[str]
    useful_facts: list[str]
    things_to_ask: list[str]
    reasons: list[str]
    message: str
    missing_information: list[str]
    warnings: list[str]

# ============================================================
# PROFILE
# ============================================================

def load_profile() -> dict[str, Any]:
    path = BASE_DIR / "profile.json"

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

# ============================================================
# RESUMES
# ============================================================

def extract_pdf_text(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
        pages = []

        for page in reader.pages:
            pages.append(page.extract_text() or "")

        return "\n".join(pages).strip()

    except Exception as error:
        print(f"[RESUME ERROR] {path.name}: {error}")
        return ""

def load_resumes() -> list[dict[str, str]]:
    RESUME_DIR.mkdir(parents=True, exist_ok=True)

    resumes = []

    for path in sorted(RESUME_DIR.glob("*.pdf")):
        print(f"[RESUME] Reading {path.name}")

        text = extract_pdf_text(path)

        if not text:
            print(f"[RESUME] Empty/unreadable: {path.name}")
            continue

        resumes.append({
            "filename": path.name,
            "text": text
        })

    print(f"[RESUME] Loaded {len(resumes)} resumes")

    return resumes

# ============================================================
# RESUME RANKING
# ============================================================

ROLE_KEYWORDS = {
    "ai_ml_resume.pdf": [
        "ai",
        "machine learning",
        "ml",
        "machine learning engineer",
        "genai",
        "generative ai",
        "rag",
        "agentic",
        "llm",
        "nlp",
        "transformer",
        "sapbert"
    ],
    "software_engineer_resume.pdf": [
        "software engineer",
        "software development",
        "backend",
        "api",
        "database",
        "javascript",
        "typescript",
        "python",
        "c++",
        "react"
    ],
    "backend_resume.pdf": [
        "backend",
        "backend engineer",
        "api",
        "fastapi",
        "node",
        "server",
        "database",
        "sql",
        "mongodb",
        "websocket",
        "distributed",
        "load balancer"
    ],
    "fullstack_resume.pdf": [
        "full stack",
        "fullstack",
        "frontend",
        "backend",
        "react",
        "next.js",
        "nextjs",
        "typescript",
        "javascript",
        "api",
        "mongodb"
    ],
    "product_resume.pdf": [
        "product",
        "product engineering",
        "product development",
        "user",
        "prototype",
        "startup",
        "requirements",
        "analytics",
        "ai"
    ],
    "business_analyst_resume.pdf": [
        "business analyst",
        "business analysis",
        "analytics",
        "data analysis",
        "sql",
        "requirements",
        "stakeholder",
        "business requirements",
        "process",
        "dashboard",
        "reporting",
        "excel",
        "power bi"
    ]
}

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())

def rank_resumes(
    resumes: list[dict[str, str]],
    context: str
) -> list[dict[str, Any]]:
    context_normalized = normalize(context)
    ranked = []

    for resume in resumes:
        filename = resume["filename"].lower()
        resume_text = normalize(resume["text"])

        score = 0
        matched = []

        for keyword in ROLE_KEYWORDS.get(filename, []):
            if keyword in context_normalized:
                score += 5
                matched.append(keyword)
            elif keyword in resume_text:
                score += 1

        ranked.append({
            "filename": resume["filename"],
            "text": resume["text"],
            "score": score,
            "matched": matched
        })

    ranked.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return ranked

# ============================================================
# OLLAMA
# ============================================================

def call_ollama(
    system_prompt: str,
    user_prompt: str,
    schema: dict
) -> dict:
    payload = {
        "model": OLLAMA_MODEL,
        "think": False,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "format": schema,
        "options": {
            "temperature": 0.2
        }
    }

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=240
    )

    response.raise_for_status()

    data = response.json()

    content = (
        data
        .get("message", {})
        .get("content", "")
    )

    if not content:
        raise ValueError(
            "Ollama returned empty content"
        )

    return json.loads(content)

# ============================================================
# CALL 1: RESEARCH
# ============================================================

RESEARCH_SYSTEM_PROMPT = """
You are the research engine of a personal LinkedIn copilot.

The user will NOT manually inspect your intermediate reasoning.
You must independently research and understand the supplied LinkedIn
page before making any recommendation.

Identify:

- exact person
- current role
- current company
- person type
- hiring signals
- concrete open roles
- job descriptions
- company/product
- current work
- technical interests
- business interests
- relevant recent posts
- genuine connection points
- useful facts

The profile header supplied separately is especially important.

Do not confuse:
- current role with old experience
- company with previous companies
- the profile owner with people mentioned in posts
- recommendations/sidebar people with the profile owner

If explicit hiring information exists, preserve it.

If the page contains:
"Hiring: Machine Learning Engineer"
that is a concrete hiring signal.

Do not invent hiring.

Do not invent shared interests.

Do not infer facts that are not supported by the supplied page.

The candidate is NOT the person being researched.

Return only JSON.
"""

RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "person": {"type": "string"},
        "current_role": {"type": "string"},
        "company": {"type": "string"},
        "person_type": {"type": "string"},
        "company_description": {"type": "string"},
        "hiring_opportunities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "company": {"type": "string"},
                    "location": {"type": "string"},
                    "work_mode": {"type": "string"},
                    "description": {"type": "string"},
                    "evidence": {"type": "string"}
                },
                "required": [
                    "role",
                    "company",
                    "location",
                    "work_mode",
                    "description",
                    "evidence"
                ]
            }
        },
        "current_projects": {
            "type": "array",
            "items": {"type": "string"}
        },
        "recent_topics": {
            "type": "array",
            "items": {"type": "string"}
        },
        "connection_points": {
            "type": "array",
            "items": {"type": "string"}
        },
        "useful_facts": {
            "type": "array",
            "items": {"type": "string"}
        },
        "warnings": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": [
        "person",
        "current_role",
        "company",
        "person_type",
        "company_description",
        "hiring_opportunities",
        "current_projects",
        "recent_topics",
        "connection_points",
        "useful_facts",
        "warnings"
    ]
}

def research_linkedin(
    request: ScreenRequest
) -> dict:
    hiring_signals = [
        {
            "text": item.text,
            "href": item.href
        }
        for item in request.hiring_signals
    ]

    user_prompt = f"""
PROFILE HEADER - TRUST THIS AS THE PRIMARY IDENTITY:

Name:
{request.profile_name or "(not extracted)"}

Headline:
{request.profile_headline or "(not extracted)"}

Location:
{request.profile_location or "(not extracted)"}

EXPLICIT HIRING SIGNALS EXTRACTED FROM LINKEDIN:
{json.dumps(hiring_signals, ensure_ascii=False, indent=2)}

FULL PROFILE CONTENT:
{request.page_text[:30000]}

USER INTENT:
{request.intent}

CUSTOM GOAL:
{request.custom_goal or "(none)"}

Perform the research yourself.

The user should not have to manually identify the person,
company, hiring role, or useful overlap.

Return only JSON.
"""

    print("[OLLAMA] Call 1: researching LinkedIn...")

    result = call_ollama(
        RESEARCH_SYSTEM_PROMPT,
        user_prompt,
        RESEARCH_SCHEMA
    )

    print(
        "[RESEARCH] Person:",
        result.get("person")
    )

    print(
        "[RESEARCH] Company:",
        result.get("company")
    )

    print(
        "[RESEARCH] Role:",
        result.get("current_role")
    )

    print(
        "[RESEARCH] Opportunities:",
        result.get("hiring_opportunities")
    )

    return result

# ============================================================
# CALL 2: COMPLETE DECISION
# ============================================================

DECISION_SYSTEM_PROMPT = """
You are the final decision and communication engine of a personal
LinkedIn copilot.

You must independently perform ALL reasoning required to produce the
final useful result.

The user does not manually inspect intermediate research.

You receive:
- researched LinkedIn facts
- candidate profile
- candidate resumes
- user intent
- custom goal
- extra context

Your responsibilities:

1. Determine what the person actually does.
2. Determine whether there is a real hiring opportunity.
3. Determine which opportunity is relevant.
4. Compare the candidate against the relevant opportunity.
5. Select the most relevant resume.
6. Identify genuine overlap.
7. Identify useful facts.
8. Decide whether the user should approach for a job, networking,
   advice, product discussion, or the custom goal.
9. Write the final message.

Never invent facts.

Never confuse the candidate with the LinkedIn person.

The candidate's name is Swayam Gupta.

If the LinkedIn person has a different name, that is NORMAL.
Do NOT treat different names as a mismatch.

The candidate and LinkedIn person are supposed to be different people.

For example:

LinkedIn person:
Soman Khazharey R.C.

Candidate:
Swayam Gupta

This is NOT a mismatch.

For JOB intent:
- detect the actual role
- compare against the resumes
- select the most relevant resume
- explain the actual overlap
- identify missing requirements if relevant
- write a concise job-related message

For FOUNDER intent:
- research the founder/company
- determine whether hiring is relevant
- determine whether networking/product/advice is more appropriate
- use hiring if there is a concrete relevant opportunity
- do not automatically ask for a job

For NETWORK intent:
- find genuine professional overlap
- do not force a job request

For ADVICE intent:
- find one specific question based on the person's actual work

For CUSTOM intent:
- follow the user's goal

The selected resume must be one of the supplied resumes or
"not_needed".

Do not choose a resume just because its filename sounds appropriate.
Use its actual contents.

Do not claim the candidate has a skill unless the supplied resume
supports it.

Do not claim the candidate and person share something unless both
sides support it.

Message style:
- short
- natural
- direct
- human
- no fake familiarity
- no generic praise
- no corporate/AI networking language

Avoid:
"I came across your profile"
"I am passionate"
"dream company"
"inspired by your journey"
"honored"
"would love an opportunity"
"hope you're doing well"
"your impressive journey"
"your amazing work"

Keep message below 280 characters.

Return only JSON.
"""

DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "fit": {
            "type": "string",
            "enum": [
                "strong",
                "possible",
                "weak",
                "not_applicable"
            ]
        },
        "confidence": {
            "type": "string",
            "enum": [
                "high",
                "medium",
                "low"
            ]
        },
        "selected_resume": {
            "type": "string"
        },
        "resume_reason": {
            "type": "string"
        },
        "relevant_overlap": {
            "type": "array",
            "items": {"type": "string"}
        },
        "things_to_ask": {
            "type": "array",
            "items": {"type": "string"}
        },
        "reasons": {
            "type": "array",
            "items": {"type": "string"}
        },
        "message": {
            "type": "string"
        },
        "missing_information": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": [
        "fit",
        "confidence",
        "selected_resume",
        "resume_reason",
        "relevant_overlap",
        "things_to_ask",
        "reasons",
        "message",
        "missing_information"
    ]
}

def make_decision(
    request: ScreenRequest,
    profile: dict[str, Any],
    research: dict,
    ranked_resumes: list[dict[str, Any]]
) -> dict:
    resume_blocks = []

    for resume in ranked_resumes:
        resume_blocks.append(
            f"""
===== RESUME: {resume["filename"]} =====
LOCAL RELEVANCE SCORE: {resume["score"]}
MATCHED ROLE TERMS: {", ".join(resume["matched"]) or "none"}

{resume["text"][:10000]}
"""
        )

    resumes_text = "\n".join(resume_blocks)

    user_prompt = f"""
CANDIDATE PROFILE:
{json.dumps(profile, ensure_ascii=False, indent=2)}

USER INTENT:
{request.intent}

CUSTOM GOAL:
{request.custom_goal or "(none)"}

TONE:
{request.tone}

EXTRA CONTEXT:
{request.extra_context or "(none)"}

LINKEDIN RESEARCH:
{json.dumps(research, ensure_ascii=False, indent=2)}

ALL CANDIDATE RESUMES:
{resumes_text}

Perform the complete decision yourself.

Important:

The LinkedIn person and candidate are DIFFERENT people.

Do not say:
"The names are different, so this is not a match."

That is incorrect.

Instead compare:
LinkedIn person -> their role/company/opportunity
Candidate -> their actual skills/experience

If there is an ML Engineer opening at Ecostel and the candidate's
AI/ML resume supports it, evaluate that opportunity.

Do not select a resume based only on the LinkedIn person's name.

Return only JSON.
"""

    print("[OLLAMA] Call 2: final reasoning + message...")

    return call_ollama(
        DECISION_SYSTEM_PROMPT,
        user_prompt,
        DECISION_SCHEMA
    )

# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    try:
        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=5
        )

        response.raise_for_status()

        return {
            "ok": True,
            "ollama": True,
            "model": OLLAMA_MODEL
        }

    except Exception as error:
        return {
            "ok": True,
            "ollama": False,
            "model": OLLAMA_MODEL,
            "error": str(error)
        }

# ============================================================
# SCREEN
# ============================================================

@app.post(
    "/screen",
    response_model=ScreenResponse
)
def screen(request: ScreenRequest):
    print("\n" + "=" * 70)
    print("[SCREEN] Request received")
    print("[SCREEN] URL:", request.page_url)
    print("[SCREEN] Intent:", request.intent)
    print("[SCREEN] Page chars:", len(request.page_text))
    print("[SCREEN] Profile name:", request.profile_name)
    print("[SCREEN] Profile headline:", request.profile_headline)
    print("[SCREEN] Hiring signals:", request.hiring_signals)

    profile = load_profile()
    resumes = load_resumes()

    if not resumes:
        raise HTTPException(
            status_code=400,
            detail="No PDF resumes found. Put your resumes inside backend/resumes/"
        )

    try:
        # ====================================================
        # CALL 1
        # ====================================================

        research = research_linkedin(request)

        # ====================================================
        # RESUME RANKING
        # ====================================================

        opportunities = research.get(
            "hiring_opportunities",
            []
        )

        opportunity_text = json.dumps(
            opportunities,
            ensure_ascii=False
        )

        research_context = "\n".join([
            research.get("current_role", ""),
            research.get("company", ""),
            research.get("company_description", ""),
            opportunity_text,
            " ".join(
                research.get("current_projects", [])
            ),
            " ".join(
                research.get("recent_topics", [])
            )
        ])

        ranked_resumes = rank_resumes(
            resumes,
            research_context
        )

        print("[RESUME] Ranking:")

        for resume in ranked_resumes:
            print(
                " ",
                resume["filename"],
                "score=",
                resume["score"],
                "matched=",
                resume["matched"]
            )

        # ====================================================
        # CALL 2
        # ====================================================

        decision = make_decision(
            request,
            profile,
            research,
            ranked_resumes
        )

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        hiring_signal = "No explicit hiring signal found."

        if opportunities:
            roles = []

            for opportunity in opportunities:
                role = opportunity.get("role", "")
                company = opportunity.get("company", "")

                if role:
                    if company:
                        roles.append(
                            f"{role} @ {company}"
                        )
                    else:
                        roles.append(role)

            if roles:
                hiring_signal = "; ".join(roles)

        detected_opportunity = "None detected."

        if opportunities:
            descriptions = []

            for opportunity in opportunities:
                role = opportunity.get("role", "")
                company = opportunity.get("company", "")
                location = opportunity.get("location", "")
                work_mode = opportunity.get("work_mode", "")

                text = role

                if company:
                    text += f" @ {company}"

                details = []

                if location:
                    details.append(location)

                if work_mode:
                    details.append(work_mode)

                if details:
                    text += " (" + ", ".join(details) + ")"

                descriptions.append(text)

            detected_opportunity = "; ".join(
                descriptions
            )

        result = {
            "person": research.get(
                "person",
                request.profile_name or "Unknown"
            ),
            "current_role": research.get(
                "current_role",
                "Unknown"
            ),
            "company": research.get(
                "company",
                "Unknown"
            ),
            "person_type": research.get(
                "person_type",
                "professional"
            ),
            "hiring_signal": hiring_signal,
            "detected_opportunity": detected_opportunity,
            "fit": decision.get(
                "fit",
                "not_applicable"
            ),
            "confidence": decision.get(
                "confidence",
                "low"
            ),
            "selected_resume": decision.get(
                "selected_resume",
                "not_needed"
            ),
            "resume_reason": decision.get(
                "resume_reason",
                ""
            ),
            "relevant_overlap": decision.get(
                "relevant_overlap",
                []
            ),
            "useful_facts": research.get(
                "useful_facts",
                []
            ),
            "things_to_ask": decision.get(
                "things_to_ask",
                []
            ),
            "reasons": decision.get(
                "reasons",
                []
            ),
            "message": decision.get(
                "message",
                ""
            ),
            "missing_information": decision.get(
                "missing_information",
                []
            ),
            "warnings": research.get(
                "warnings",
                []
            )
        }

        if len(result["message"]) > 280:
            result["message"] = (
                result["message"][:277] + "..."
            )

        print("[SUCCESS] Person:", result["person"])
        print("[SUCCESS] Company:", result["company"])
        print("[SUCCESS] Role:", result["current_role"])
        print("[SUCCESS] Opportunity:", result["detected_opportunity"])
        print("[SUCCESS] Fit:", result["fit"])
        print("[SUCCESS] Resume:", result["selected_resume"])
        print("[SUCCESS] Message:", result["message"])
        print("=" * 70 + "\n")

        return result

    except requests.RequestException as error:
        print("[OLLAMA ERROR]", error)

        raise HTTPException(
            status_code=502,
            detail=f"Ollama request failed: {error}"
        )

    except json.JSONDecodeError as error:
        print("[JSON ERROR]", error)

        raise HTTPException(
            status_code=502,
            detail=f"Ollama did not return valid JSON: {error}"
        )

    except Exception as error:
        print("[ERROR]", error)

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
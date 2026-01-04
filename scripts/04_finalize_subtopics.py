from openai import OpenAI
from mongoengine import connect
from models.upsc_syllabus import UPSCSyllabus
from models.subtopics import SubTopic
from models.pydantic_models import GeneratedSubTopics

# ---------------- DB ----------------
connect(
    db="upsc",
    host="mongodb+srv://user:user@cluster0.rgocxdb.mongodb.net/upsc"
)

client = OpenAI()


# ---------------- NAME NORMALIZATION ----------------
def normalize_name(name: str) -> str:
    """
    VERY conservative normalization:
    - strip extra spaces
    - single spaces only
    - title case preserved as-is (UPSC wording)
    """
    return " ".join(name.strip().split())


# ---------------- ORDERING CALL ----------------
def order_subtopics(subject: str, paper: str, stage: str, names: list[str]) -> list[str]:
    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a UPSC syllabus authority. "
                    "Your task is ONLY to order syllabus headings logically."
                )
            },
            {
                "role": "user",
                "content": f"""
Order the following UPSC subtopics logically.

Context:
Subject: {subject}
Paper: {paper}
Stage: {stage}

Rules:
- Do NOT rename, rephrase, merge, or remove anything
- Preserve EXACT wording
- Order from foundational → advanced
- Use strict UPSC syllabus logic
- Return ONLY the ordered list

Subtopics:
{names}
"""
            }
        ],
        text_format=GeneratedSubTopics
    )

    return response.output_parsed.subtopics


# ---------------- FINALIZE ONE SUBJECT ----------------
def finalize_subject(subject: str, paper: str, stage: str):
    print(f"\n🔒 Finalizing subject: {subject}")

    syllabi = UPSCSyllabus.objects(
        subject=subject,
        paper=paper,
        stage=stage
    )

    if not syllabi:
        return

    syllabus = syllabi.first()

    # Fetch subtopics
    subtopics = list(syllabus.subtopics)
    if not subtopics:
        return

    # ---- Step 1: Normalize names ----
    name_map = {}
    for s in subtopics:
        clean = normalize_name(s.name)
        if clean != s.name:
            s.name = clean
            s.save()
        name_map[clean] = s

    names = list(name_map.keys())

    # ---- Step 2: Order via LLM ----
    ordered_names = order_subtopics(
        subject=subject,
        paper=paper,
        stage=stage,
        names=names
    )

    # ---- Step 3: Re-attach in order ----
    syllabus.subtopics = [name_map[n] for n in ordered_names if n in name_map]

    # ---- Step 4: Freeze flags ----
    for s in syllabus.subtopics:
        s.v4_finalized = True
        s.save()

    syllabus.v4 = True
    syllabus.save()

    print(f"✅ Finalized {len(syllabus.subtopics)} subtopics")


# ---------------- ENTRY (SUBJECT-WISE) ----------------
if __name__ == "__main__":
    processed = set()

    for s in UPSCSyllabus.objects():
        key = (s.subject, s.paper, s.stage)
        if key in processed:
            continue

        finalize_subject(
            subject=s.subject,
            paper=s.paper,
            stage=s.stage
        )

        processed.add(key)

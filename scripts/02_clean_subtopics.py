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


# ---------------- LLM VERIFICATION CALL ----------------
def check_missing_subtopics(syllabus: UPSCSyllabus, existing_names: list[str]) -> list[str]:
    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {
                "role": "system",
                "content": "You are a UPSC syllabus auditor. Your job is to find missing syllabus items only."
            },
            {
                "role": "user",
                "content": f"""
You are a UPSC syllabus auditor.

Your task is NOT to expand the syllabus.
Your task is ONLY to check for MAJOR, ESSENTIAL omissions.

Context:
Exam: {syllabus.exam}
Stage: {syllabus.stage}
Paper: {syllabus.paper}
Subject: {syllabus.subject}

Already covered subtopics:
{existing_names}

Rules (VERY IMPORTANT):
- Judge coverage at a MACRO level, not micro
- If the existing list covers MOST of the official UPSC syllabus (≈80% or more), return an EMPTY list
- Ignore minor, derivative, overlapping, or optional areas
- Add items ONLY if their absence would make preparation INCOMPLETE
- Do NOT suggest improvements or refinements
- Do NOT aim for exhaustiveness
- Use strict UPSC wording only
- If nothing ESSENTIAL is missing, return an empty list

"""
            }
        ],
        text_format=GeneratedSubTopics
    )

    return response.output_parsed.subtopics


# ---------------- STRICT VERIFICATION ----------------
def verify_syllabus_unit(syllabus: UPSCSyllabus):
    print(f"\n🔍 Verifying: {syllabus.exam} | {syllabus.paper} | {syllabus.subject}")

    existing_subtopics = list(
        SubTopic.objects(subject=syllabus.subject).values_list("name")
    )

    missing = check_missing_subtopics(syllabus, existing_subtopics)

    if not missing:
        print("✅ Nothing missing")
        syllabus.v1 = True
        syllabus.save()
        return

    print(f"⚠️ Missing {len(missing)} subtopics")

    for name in missing:
        sub = SubTopic(
            name=name,
            subject=syllabus.subject,
            v1_generated=True
        )
        sub.save()
        syllabus.subtopics.append(sub)
        print(f"➕ Added: {name}")

    syllabus.v1 = True
    syllabus.save()


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    for syllabus in UPSCSyllabus.objects():
        verify_syllabus_unit(syllabus)

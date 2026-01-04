from openai import OpenAI
from mongoengine import connect
from models.upsc_syllabus import UPSCSyllabus
from models.subtopics import SubTopic
from models.pydantic_models import CleanupDecision

# ---------------- DB ----------------
connect(
    db="upsc",
    host="mongodb+srv://user:user@cluster0.rgocxdb.mongodb.net/upsc"
)

client = OpenAI()


# ---------------- LLM CLEANUP ----------------
def audit_subject(subject: str, paper: str, stage: str):
    print(f"\n🧹 Auditing subject: {subject}")

    subtopics = list(SubTopic.objects(subject=subject))
    if not subtopics:
        return

    name_map = {s.name: s for s in subtopics}

    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a UPSC syllabus authority and data auditor. "
                    "You must strictly follow official UPSC syllabus scope."
                )
            },
            {
                "role": "user",
                "content": f"""
You are a UPSC syllabus authority and data auditor.

Subject: {subject}
Paper: {paper}
Stage: {stage}

Existing subtopics:
{list(name_map.keys())}

IMPORTANT:
Your default action is to DO NOTHING.

Your task is to decide WHETHER ANY CHANGE IS REQUIRED AT ALL.

Only if the current list is CLEARLY WRONG or CORRUPTED, then act.

Allowed actions (ONLY if necessary):
1. MERGE topics that are clearly duplicates or exact synonyms
2. REMOVE topics that are clearly NOT part of the official UPSC syllabus for this subject & paper

STRICT RULES:
- If the current list is reasonably clean and within UPSC scope, return EMPTY merge_groups and EMPTY remove
- Do NOT “improve”, “refine”, or “optimize”
- Do NOT act for stylistic reasons
- Do NOT remove borderline or debatable topics
- If unsure → KEEP the topic
- Use official UPSC wording only
- Be extremely conservative



Return empty lists unless action is unavoidable.
"""
            }
        ],
        text_format=CleanupDecision
    )

    decision = response.output_parsed

    # ---------------- MERGE ----------------
    for group in decision.merge_groups:
        keep_topic = name_map.get(group.keep)
        if not keep_topic:
            continue

        for merge_name in group.merge:
            merge_topic = name_map.get(merge_name)
            if not merge_topic or merge_topic == keep_topic:
                continue

            # Re-link syllabi
            for syllabus in UPSCSyllabus.objects(subtopics=merge_topic):
                syllabus.subtopics.remove(merge_topic)
                if keep_topic not in syllabus.subtopics:
                    syllabus.subtopics.append(keep_topic)
                syllabus.save()

            merge_topic.delete()
            print(f"🔀 Merged '{merge_name}' → '{group.keep}'")

    # ---------------- REMOVE ----------------
    for removal in decision.remove:
        topic = SubTopic.objects(
            name=removal.name,
            subject=subject
        ).first()

        if not topic:
            continue

        # Unlink safely
        for syllabus in UPSCSyllabus.objects(subtopics=topic):
            syllabus.subtopics.remove(topic)
            syllabus.save()

        topic.delete()
        print(f"❌ Removed '{removal.name}' | Reason: {removal.reason}")


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    processed = set()

    for s in UPSCSyllabus.objects():
        key = (s.subject, s.paper, s.stage)
        if key in processed:
            continue

        audit_subject(
            subject=s.subject,
            paper=s.paper,
            stage=s.stage
        )
        processed.add(key)

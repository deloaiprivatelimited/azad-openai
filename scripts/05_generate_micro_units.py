from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from mongoengine import connect

from models.upsc_syllabus import UPSCSyllabus
from models.subtopics import SubTopic
from models.micro_units import MicroUnit
from models.pydantic_models import GeneratedMicroUnits

# ---------------- DB ----------------
connect(
    db="upsc",
    host="mongodb+srv://user:user@cluster0.rgocxdb.mongodb.net/upsc"
)

client = OpenAI()


def generate_micro_units(syllabus: UPSCSyllabus, subtopic: SubTopic):
    # Skip if already generated (double safety)
    if MicroUnit.objects(subtopic=subtopic).first():
        return

    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a UPSC syllabus decomposition expert.\n\n"
                    "You break ONE official UPSC subtopic into exam-oriented micro-units.\n\n"
                    "Rules:\n"
                    "- STRICT UPSC syllabus scope only\n"
                    "- Use official UPSC wording\n"
                    "- No explanations or examples\n"
                    "- No overlap with other subtopics\n"
                    "- No artificial limits on count\n"
                    "- Output only a flat list"
                )
            },
            {
                "role": "user",
                "content": f"""
Subject: {syllabus.subject}
Stage: {syllabus.stage}
Paper: {syllabus.paper}

SubTopic:
{subtopic.name}

Task:
Generate MICRO-UNITS strictly within the scope of this subtopic.
"""
            }
        ],
        text_format=GeneratedMicroUnits
    )

    parsed = response.output_parsed

    for idx, name in enumerate(parsed.micro_units):
        MicroUnit(
            name=name,
            subject=subtopic.subject,
            subtopic=subtopic,
            order=idx,
            v5_generated=True
        ).save()


# ---------------- ENTRY POINT ----------------
if __name__ == "__main__":
    tasks = []
    count=0

    with ThreadPoolExecutor(max_workers=6) as executor:
        for syllabus in UPSCSyllabus.objects(v4=True):
            for subtopic in syllabus.subtopics:
                count+=1
                print(f"\n🔬 Processing ({count}): {syllabus.subject} | {subtopic.name}")
                if not MicroUnit.objects(subtopic=subtopic).first():
                    tasks.append(
                        executor.submit(generate_micro_units, syllabus, subtopic)
                    )

        for future in as_completed(tasks):
            try:
                future.result()
            except Exception as e:
                print("❌ Error:", e)

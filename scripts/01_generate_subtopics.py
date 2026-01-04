from openai import OpenAI
from models.upsc_syllabus import UPSCSyllabus
from models.subtopics import SubTopic
from models.pydantic_models import GeneratedSubTopics

client = OpenAI()


def generate(syllabus: UPSCSyllabus):
    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {"role": "system", "content": "You are a UPSC syllabus expert."},
            {
                "role": "user",
                "content": f"""
Generate SUBTOPICS.

Exam: {syllabus.exam}
Stage: {syllabus.stage}
Paper: {syllabus.paper}
Subject: {syllabus.subject}

Rules:
- Broad syllabus buckets
- UPSC wording only
- No explanations
"""
            }
        ],
        text_format=GeneratedSubTopics
    )

    parsed = response.output_parsed

    for name in parsed.subtopics:
        sub = SubTopic.objects(
            name=name,
            subject=syllabus.subject
        ).first() or SubTopic(
            name=name,
            subject=syllabus.subject
        )

        sub.v1_generated = True
        sub.save()

        if sub not in syllabus.subtopics:
            syllabus.subtopics.append(sub)

    syllabus.v1 = True
    syllabus.save()


if __name__ == "__main__":
    for s in UPSCSyllabus.objects(v1=False):
        generate(s)

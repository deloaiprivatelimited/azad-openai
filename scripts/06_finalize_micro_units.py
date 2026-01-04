from openai import OpenAI
from mongoengine import connect
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

from models.upsc_syllabus import UPSCSyllabus
from models.subtopics import SubTopic
from models.micro_units import MicroUnit
from models.pydantic_models import MicroUnitAuditResult

# ---------------- DB ----------------
connect(
    db="upsc",
    host="mongodb+srv://user:user@cluster0.rgocxdb.mongodb.net/upsc"
)

client = OpenAI()


def finalize_micro_units(syllabus, subtopic):
    try:
        micro_units = list(
            MicroUnit.objects(subtopic=subtopic).order_by("order")
        )

        if not micro_units:
            return f"SKIPPED: {subtopic.name}"

        names = [mu.name for mu in micro_units]

        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a UPSC syllabus micro-structure auditor.\n"
                        "Default action is DO NOTHING.\n"
                        "Only reorder, remove redundant/out-of-scope items, "
                        "or add missing MAJOR micro-units.\n"
                        "Preserve exact wording."
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

Existing Micro-Units:
""" + "\n".join(f"{i+1}. {n}" for i, n in enumerate(names))
                }
            ],
            text_format=MicroUnitAuditResult
        )

        result = response.output_parsed

        # -------- REMOVALS --------
        for name in result.removed:
            MicroUnit.objects(
                subtopic=subtopic,
                name=name
            ).delete()

        # -------- ADDITIONS --------
        existing_names = set(names)
        for name in result.added:
            if name not in existing_names:
                MicroUnit(
                    name=name,
                    subject=subtopic.subject,
                    subtopic=subtopic
                ).save()

        # -------- REORDER --------
        for idx, name in enumerate(result.final_order):
            mu = MicroUnit.objects(
                subtopic=subtopic,
                name=name
            ).first()

            if mu:
                mu.order = idx
                mu.v6_verified = True
                mu.v6_finalized = True
                mu.save()

        return f"DONE: {subtopic.name}"

    except Exception as e:
        traceback.print_exc()
        return f"ERROR: {subtopic.name} | {str(e)}"

def run_threaded(max_workers=6):
    tasks = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for syllabus in UPSCSyllabus.objects(v4=True):
            for subtopic in syllabus.subtopics:
                tasks.append(
                    executor.submit(
                        finalize_micro_units,
                        syllabus,
                        subtopic
                    )
                )

        for future in as_completed(tasks):
            print(future.result())


def print_completion_stats():
    total_micro_units = MicroUnit.objects.count()
    completed_micro_units = MicroUnit.objects(v6_finalized=True).count()
    
    total_subtopics = SubTopic.objects.count()
    completed_subtopics = SubTopic.objects(v6_finalized=True).count()
    
    print("\n" + "="*50)
    print("COMPLETION STATISTICS")
    print("="*50)
    print(f"Micro Units: {completed_micro_units}/{total_micro_units} completed")
    print(f"SubTopics: {completed_subtopics}/{total_subtopics} completed")
    print("="*50)


if __name__ == "__main__":
    run_threaded(max_workers=8)
    print_completion_stats()

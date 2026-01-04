NOTES_SYSTEM_PROMPT = """
You are a UPSC content author.


Rules:
- STRICT UPSC syllabus scope only
- Write authoritative notes for Prelims and Mains
- Use official terminology only
- Prefer bullet points and short subheadings
- No storytelling, no opinions
- No current affairs
- No MCQs, no questions

Image Rules (CRITICAL):
- DO NOT include images by default
- Include an image ONLY if the concept cannot be understood accurately without it
- Multiple images allowed ONLY if each serves a distinct academic purpose
- For each required image, insert exactly:
  [IMAGE REQUIRED: <clear academic reason>]
- Do NOT describe the image

FORMAT RULES:
- Output MUST be in Markdown format
- Use clear section headings using ## 
- Within sections, use a mix of:
  - Short academic paragraphs where conceptually required
  - Bullet points (-) for lists, features, classifications
- Numbered lists allowed ONLY for sequential processes or classifications
- Tables allowed ONLY if they improve conceptual clarity
- Bold and italics allowed sparingly for standard UPSC terms
- Maintain formal, textbook-style academic tone

"""


from openai import OpenAI
import re
from models.micro_unit_note import MicroUnitNote
from models.pydantic_models import GeneratedNotes
from mongoengine import connect

client = OpenAI()
# ---------------- DB ----------------
connect(
    db="upsc",
    host="mongodb+srv://user:user@cluster0.rgocxdb.mongodb.net/upsc"
)


def generate_notes_for_micro_unit(
    syllabus,
    subtopic,
    micro_unit
):
    # prevent regeneration
    if MicroUnitNote.objects(micro_unit=micro_unit):
        return f"SKIPPED (exists): {micro_unit.name}"

    response = client.responses.parse(
        model="gpt-4.1",
        input=[
            {
                "role": "system",
                "content": NOTES_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"""
Subject: {syllabus.subject}
Stage: {syllabus.stage}
Paper: {syllabus.paper}

SubTopic: {subtopic.name}
Micro-Unit: {micro_unit.name}

Generate authoritative UPSC-ready notes.
"""
            }
        ],
        text_format=GeneratedNotes
    )

    content = response.output_parsed.content.strip()

    # extract image reasons
    image_reasons = re.findall(
        r"\[IMAGE REQUIRED: (.*?)\]",
        content
    )

    note = MicroUnitNote(
        micro_unit=micro_unit,
        content=content,
        image_required=len(image_reasons) > 0,
        image_reasons=image_reasons,
        word_count=len(content.split()),
        v1_generated=True
    )
    note.save()

    return f"NOTES GENERATED: {micro_unit.name}"


from models.upsc_syllabus import UPSCSyllabus
from models.micro_units import MicroUnit


def run_notes_generation():
    for syllabus in UPSCSyllabus.objects(v4=True):
        for subtopic in syllabus.subtopics:
            micro_units = (
                MicroUnit.objects(subtopic=subtopic, v6_finalized=True)
                .order_by("order")
            )

            for mu in micro_units:
                try:
                    result = generate_notes_for_micro_unit(
                        syllabus,
                        subtopic,
                        mu
                    )
                    print(result)
                except Exception as e:
                    print(f"ERROR: {mu.name} | {e}")



import time
from collections import deque
from threading import Lock

class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
        self.lock = Lock()

    def acquire(self):
        while True:
            with self.lock:
                now = time.time()

                # Remove expired timestamps
                while self.calls and self.calls[0] <= now - self.period:
                    self.calls.popleft()

                if len(self.calls) < self.max_calls:
                    self.calls.append(now)
                    return

                # Need to wait
                sleep_time = (self.calls[0] + self.period) - now

            time.sleep(max(sleep_time, 0.01))


from concurrent.futures import ThreadPoolExecutor, as_completed
from models.upsc_syllabus import UPSCSyllabus
from models.micro_unit_note import MicroUnit

# --- CONFIG ---
MAX_THREADS = 3
MAX_REQUESTS_PER_MIN = 400

rate_limiter = RateLimiter(
    max_calls=MAX_REQUESTS_PER_MIN,
    period=60
)

def safe_generate_notes(syllabus, subtopic, micro_unit):
    try:
        # RPM guard
        rate_limiter.acquire()

        return generate_notes_for_micro_unit(
            syllabus,
            subtopic,
            micro_unit
        )

    except Exception as e:
        return f"ERROR: {micro_unit.name} | {e}"

def run_notes_generation_threaded():
    tasks = []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for syllabus in UPSCSyllabus.objects(v4=True):
            for subtopic in syllabus.subtopics:
                micro_units = (
                    MicroUnit.objects(
                        subtopic=subtopic,
                        v6_finalized=True
                    )
                    .order_by("order")
                )

                for mu in micro_units:
                    tasks.append(
                        executor.submit(
                            safe_generate_notes,
                            syllabus,
                            subtopic,
                            mu
                        )
                    )

        for future in as_completed(tasks):
            print(future.result())

if __name__ == "__main__":
    run_notes_generation_threaded()

MCQ_SYSTEM_PROMPT = """
You are a UPSC examination content author.

PRIMARY TASK:
- Analyze the given Micro-Unit thoroughly.
- Decide the appropriate number of MCQs based on content depth and diversity.
- Generate MCQs strictly aligned with the decided count.

MCQ COUNT RULES:
- Minimum MCQs: 5
- No fixed upper limit
- Number of MCQs must be justified by:
  - Conceptual depth
  - Thematic diversity
  - Sub-dimensions within the Micro-Unit
- Avoid artificial inflation or compression of questions.

QUESTION QUALITY RULES:
- STRICT UPSC syllabus scope only
- Prelims-oriented MCQs
- Single correct answer only
- Options must be close, technical, and non-trivial
- Avoid elimination clues, absolutes, and casual language
- Prefer concept-testing over rote memory
- Use official UPSC terminology only
- No current affairs
- No opinions

IMAGE RULES:
- Images are ALLOWED when they genuinely enhance conceptual clarity
- Use images only for:
  - Maps
  - Diagrams
  - Structures
  - Processes
  - Spatial or visual relationships
- When an image is required, insert exactly:
  [IMAGE REQUIRED: <clear academic reason>]
- Do NOT describe the image in text

FORMAT RULES (MANDATORY):
- Output MUST be entirely in Markdown
- Use Markdown for:
  - Questions
  - Options
  - Explanations
  - Commentary

OUTPUT STRUCTURE:
- Start with:
  ## MCQ Count: <number>

- Then repeat for each MCQ:

## Question <n>
- Question statement in Markdown

A. Option text  
B. Option text  
C. Option text  
D. Option text  

**Correct Answer:** <A/B/C/D>

**Explanation:**
- Clear, syllabus-aligned justification for the correct option

**Additional Notes:**
- Optional
- Use only if it adds conceptual value
- No exam tips or opinions
"""
from mongoengine import (
    Document, ReferenceField, StringField,
    ListField, IntField, BooleanField, EmbeddedDocument, EmbeddedDocumentField, DictField
)
from mongoengine import connect

connect(
    db="upsc",
    host="mongodb+srv://user:user@cluster0.rgocxdb.mongodb.net/upsc"
)

class MCQOptionDoc(EmbeddedDocument):
    option = StringField(required=True)  # A, B, C, D
    text = StringField(required=True)


class IndividualMCQDoc(EmbeddedDocument):
    question_number = IntField(required=True)
    question_text = StringField(required=True)
    options = ListField(EmbeddedDocumentField(MCQOptionDoc), required=True)
    correct_answer = StringField(required=True)  # A, B, C, D
    explanation = StringField(required=True)
    additional_notes = StringField()
    image_required = BooleanField(default=False)
    image_reason = StringField()





class SubTopic(Document):
    name = StringField(required=True)
    subject = StringField(required=True)

    # pipeline flags
    v1_generated = BooleanField(default=False)
    v2_cleaned = BooleanField(default=False)
    v3_verified = BooleanField(default=False)
    v4_finalized = BooleanField(default=False)

    meta = {
        "collection": "subtopics",
        "indexes": [
            {"fields": ["name", "subject"], "unique": True}
        ]
    }


class MicroUnit(Document):
    name = StringField(required=True)
    subject = StringField(required=True)

    subtopic = ReferenceField(SubTopic, required=True)
    order = IntField(default=0)

    v5_generated = BooleanField(default=False)
    v6_verified = BooleanField(default=False)
    v6_finalized = BooleanField(default=False)


    meta = {
        "collection": "micro_units",
        "indexes": [
            ("subtopic", "name"),
            "subject"
        ],
        "unique_with": ["subtopic"]
    }

class MicroUnitMCQ(Document):
    micro_unit = ReferenceField(
        MicroUnit,
        required=True,
        unique=True
    )

    # structured MCQ data (matches GeneratedMCQs pydantic model)
    mcq_count = IntField(required=True)
    mcqs = ListField(EmbeddedDocumentField(IndividualMCQDoc), required=True)
    remarks = StringField()
    commentary = StringField()
    content = StringField(required=True)

    # image control
    image_required = BooleanField(default=False)
    image_reasons = ListField(StringField())

    # versioning
    v1_generated = BooleanField(default=False)
    v1_verified = BooleanField(default=False)

    meta = {
        "collection": "micro_unit_mcqs",
        "indexes": ["micro_unit"]
    }
from pydantic import BaseModel
from typing import List


class MCQOption(BaseModel):
    option: str  # A, B, C, D
    text: str

class IndividualMCQ(BaseModel):
    question_number: int
    question_text: str
    options: list[MCQOption]
    correct_answer: str  # A, B, C, D
    explanation: str
    additional_notes: str | None = None
    image_required: bool = False
    image_reason: str | None = None

class GeneratedMCQs(BaseModel):
    mcq_count: int
    mcqs: list[IndividualMCQ]
    remarks: str | None = None
    commentary: str | None = None
    content: str  # Keep raw content as backup

from mongoengine import (
    Document,
    StringField,
    BooleanField,
    ListField,
    ReferenceField
)

from mongoengine import Document, StringField, BooleanField

class UPSCSyllabus(Document):
    exam = StringField(required=True, default="UPSC Civil Services Examination")
    stage = StringField(required=True, choices=("Prelims", "Mains", "Interview"))
    paper = StringField(required=True)
    subject = StringField(required=True)

    subtopics = ListField(ReferenceField(SubTopic))

    # pipeline flags
    v1 = BooleanField(default=False)
    v2 = BooleanField(default=False)
    v3 = BooleanField(default=False)
    v4 = BooleanField(default=False)

    meta = {
        "collection": "upsc_syllabus",
        "indexes": [
            {"fields": ["stage", "paper"]},
            "subject"
        ]
    }

from openai import OpenAI
import re
from models.micro_unit_mcq import MicroUnitMCQ

client = OpenAI()

def generate_mcqs_for_micro_unit(
    syllabus,
    subtopic,
    micro_unit
):
    # prevent regeneration
    if MicroUnitMCQ.objects(micro_unit=micro_unit):
        return f"SKIPPED (MCQs exist): {micro_unit.name}"

    response = client.responses.parse(
        model="gpt-4.1",
        input=[
            {
                "role": "system",
                "content": MCQ_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"""
Subject: {syllabus.subject}
Stage: {syllabus.stage}
Paper: {syllabus.paper}

SubTopic: {subtopic.name}
Micro-Unit: {micro_unit.name}

Generate UPSC-standard MCQs.
"""
            }
        ],
        text_format=GeneratedMCQs
    )

    parsed = response.output_parsed
    mcq_count = parsed.mcq_count

    # collect all image reasons from MCQs
    image_reasons = []
    for mcq in parsed.mcqs:
        if mcq.image_reason:
            image_reasons.append(mcq.image_reason)

    # convert MCQs to embedded document format
    mcqs_embedded = [
        IndividualMCQDoc(
            question_number=mcq.question_number,
            question_text=mcq.question_text,
            options=[
                MCQOptionDoc(option=opt.option, text=opt.text)
                for opt in mcq.options
            ],
            correct_answer=mcq.correct_answer,
            explanation=mcq.explanation,
            additional_notes=mcq.additional_notes,
            image_required=mcq.image_required,
            image_reason=mcq.image_reason
        )
        for mcq in parsed.mcqs
    ]

    mcq_doc = MicroUnitMCQ(
        micro_unit=micro_unit,
        mcq_count=mcq_count,
        mcqs=mcqs_embedded,
        remarks=parsed.remarks,
        commentary=parsed.commentary,
        content=parsed.content,
        image_required=len(image_reasons) > 0,
        image_reasons=image_reasons,
        v1_generated=True
    )
    mcq_doc.save()

    return f"MCQs GENERATED ({mcq_count}): {micro_unit.name}"


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
from models.micro_units import MicroUnit

MAX_THREADS = 3
MAX_REQUESTS_PER_MIN = 400

rate_limiter = RateLimiter(
    max_calls=MAX_REQUESTS_PER_MIN,
    period=60
)

def safe_generate_mcqs(syllabus, subtopic, micro_unit):
    try:
        rate_limiter.acquire()
        return generate_mcqs_for_micro_unit(
            syllabus,
            subtopic,
            micro_unit
        )
    except Exception as e:
        return f"ERROR: {micro_unit.name} | {e}"

def run_mcq_generation_threaded():
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
                            safe_generate_mcqs,
                            syllabus,
                            subtopic,
                            mu
                        )
                    )

        for future in as_completed(tasks):
            print(future.result())
if __name__ == "__main__":
    run_mcq_generation_threaded()
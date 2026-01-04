from mongoengine import (
    Document,
    StringField,
    BooleanField,
    ListField,
    ReferenceField
)

from .subtopics import SubTopic


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

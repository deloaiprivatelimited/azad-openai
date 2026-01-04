from mongoengine import (
    Document, StringField, ReferenceField,
    BooleanField, IntField
)
from models.subtopics import SubTopic

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

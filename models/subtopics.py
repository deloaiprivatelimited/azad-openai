from mongoengine import Document, StringField, BooleanField


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

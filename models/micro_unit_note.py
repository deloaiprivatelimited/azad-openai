from mongoengine import (
    Document, ReferenceField, StringField,
    BooleanField, IntField, ListField
)
from models.micro_units import MicroUnit


class MicroUnitNote(Document):
    micro_unit = ReferenceField(
        MicroUnit,
        required=True,
        unique=True
    )

    content = StringField(required=True)

    # image control
    image_required = BooleanField(default=False)
    image_reasons = ListField(StringField())

    word_count = IntField()

    # versioning
    v1_generated = BooleanField(default=False)
    v1_verified = BooleanField(default=False)

    meta = {
        "collection": "micro_unit_notes",
        "indexes": ["micro_unit"]
    }

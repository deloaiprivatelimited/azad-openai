from mongoengine import (
    Document, ReferenceField, StringField,
    ListField, IntField, BooleanField
)
from models.micro_units import MicroUnit


class MicroUnitMCQ(Document):
    micro_unit = ReferenceField(
        MicroUnit,
        required=True,
        unique=True
    )

    content = StringField(required=True)

    mcq_count = IntField(required=True)

    # image control (same philosophy as notes)
    image_required = BooleanField(default=False)
    image_reasons = ListField(StringField())

    # versioning
    v1_generated = BooleanField(default=False)
    v1_verified = BooleanField(default=False)

    meta = {
        "collection": "micro_unit_mcqs",
        "indexes": ["micro_unit"]
    }

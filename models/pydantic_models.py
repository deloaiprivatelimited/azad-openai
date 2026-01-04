from pydantic import BaseModel
from typing import List


class GeneratedSubTopics(BaseModel):
    subtopics: List[str]


class CleanedSubTopics(BaseModel):
    subtopics: List[str]

from pydantic import BaseModel
from typing import List


from pydantic import BaseModel
from typing import List


class MergeGroup(BaseModel):
    keep: str
    merge: List[str]


class RemovalDecision(BaseModel):
    name: str
    reason: str   # why it is out of scope


class CleanupDecision(BaseModel):
    merge_groups: List[MergeGroup]
    remove: List[RemovalDecision]

from pydantic import BaseModel
from typing import List

class GeneratedMicroUnits(BaseModel):
    micro_units: List[str]
from pydantic import BaseModel


class GeneratedNotes(BaseModel):
    content: str

class MicroUnitAuditResult(BaseModel):
    final_order: list[str]
    added: list[str]
    removed: list[str]

# models/pydantic_models.py
from pydantic import BaseModel
from typing import List


from pydantic import BaseModel
from typing import List


class VerifiedSubTopics(BaseModel):
    final_subtopics: List[str]
    added_subtopics: List[str]
    removed_subtopics: List[str]

class FinalSubTopics(BaseModel):
    subtopics: List[str]

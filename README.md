# UPSC Syllabus Pipeline - Models & Scripts Documentation

## Overview
This project is a 4-stage pipeline to generate, clean, verify, and finalize UPSC Civil Services Examination subtopics using OpenAI's GPT-4 and MongoDB for storage.

---

## Database Models

### 1. `SubTopic` (models/subtopics.py)
Represents individual subtopics for UPSC subjects.

**Fields:**
- `name` (String, required): The subtopic name
- `subject` (String, required): Subject this subtopic belongs to
- `v1_generated` (Boolean, default=False): Flag - subtopic was AI-generated in stage 1
- `v2_cleaned` (Boolean, default=False): Flag - subtopic passed stage 2 validation
- `v3_verified` (Boolean, default=False): Flag - subtopic passed stage 3 audit
- `v4_finalized` (Boolean, default=False): Flag - subtopic is finalized in stage 4

**Collection:** `subtopics`
**Unique Index:** (name, subject)

---

### 2. `UPSCSyllabus` (models/upsc_syllabus.py)
Represents UPSC syllabus structure with references to subtopics.

**Fields:**
- `exam` (String): Exam name (default: "UPSC Civil Services Examination")
- `stage` (String, choices): "Prelims", "Mains", or "Interview"
- `paper` (String): Paper/section name
- `subject` (String): Subject name
- `subtopics` (List[ReferenceField]): References to SubTopic documents
- `v1` (Boolean): Stage 1 completion flag
- `v2` (Boolean): Stage 2 completion flag
- `v3` (Boolean): Stage 3 completion flag
- `v4` (Boolean): Stage 4 completion flag

**Collection:** `upsc_syllabus`
**Indexes:** (stage, paper), subject

---

## Pydantic Models

### 1. `GeneratedSubTopics` (models/pydantic_models.py)
For API responses with generated subtopic lists.
```
subtopics: List[str]
```

### 2. `CleanedSubTopics`
For cleaned/verified subtopic lists.
```
subtopics: List[str]
```

### 3. `MergeGroup`
Defines subtopic merging decisions.
```
keep: str (subtopic to keep)
merge: List[str] (subtopics to merge into 'keep')
```

### 4. `RemovalDecision`
Defines subtopic removal decisions.
```
name: str (subtopic name)
reason: str (why it's out of scope)
```

### 5. `CleanupDecision`
Complete cleanup/audit decision output.
```
merge_groups: List[MergeGroup]
remove: List[RemovalDecision]
```

### 6. `VerifiedSubTopics`
For verification stage output.
```
final_subtopics: List[str]
added_subtopics: List[str]
removed_subtopics: List[str]
```

### 7. `FinalSubTopics`
For finalized subtopic lists.
```
subtopics: List[str]
```

---

## Pipeline Scripts

### Stage 1: `01_generate_subtopics.py`
**Purpose:** Generate initial subtopics using OpenAI GPT-4.

**Entry Point:** `if __name__ == "__main__"`

**Process:**
1. Connects to MongoDB (upsc database)
2. Iterates through all `UPSCSyllabus` records where `v1=False`
3. For each syllabus:
   - Calls OpenAI GPT-4 with system prompt: "You are a UPSC syllabus expert"
   - Requests broad, UPSC-worded subtopic buckets
   - Creates or retrieves SubTopic documents
   - Marks subtopics with `v1_generated=True`
   - Links subtopics to syllabus
   - Sets syllabus `v1=True`

**Output:** Initial subtopics created and linked to syllabi

---

### Stage 2: `02_clean_subtopics.py`
**Purpose:** Verify completeness and add missing essential subtopics.

**Key Function:** `check_missing_subtopics(syllabus, existing_names) -> List[str]`
- Calls GPT-4 as "UPSC syllabus auditor"
- Checks for MAJOR/ESSENTIAL omissions only (≈80% coverage threshold)
- Ignores minor, derivative, or overlapping areas
- Uses strict UPSC wording

**Entry Point:** `if __name__ == "__main__"`

**Process:**
1. For each UPSCSyllabus record:
   - Fetches existing subtopics
   - Calls `check_missing_subtopics()` for essential gaps
   - If none missing → marks `v1=True` and continues
   - If gaps found:
     - Creates new SubTopic documents
     - Links to syllabus
     - Prints status
   - Marks syllabus `v1=True`

**Output:** Completed syllabi with missing essential subtopics added

---

### Stage 3: `03_verify_subtopics.py`
**Purpose:** Audit subtopics for duplicates/merges and remove out-of-scope items.

**Key Function:** `audit_subject(subject, paper, stage)`
- Calls GPT-4 as "UPSC syllabus authority and data auditor"
- Conservative approach: default action is DO NOTHING
- Only acts if list is CLEARLY WRONG or CORRUPTED
- Allowed actions:
  - MERGE: Duplicate or exact synonym topics
  - REMOVE: Topics clearly not in official UPSC syllabus

**Merge Logic:**
- Re-links all syllabi from merged topic to keep topic
- Deletes the merged topic

**Removal Logic:**
- Unlinks topic from all syllabi
- Deletes the topic

**Entry Point:** `if __name__ == "__main__"`

**Process:**
1. Tracks processed (subject, paper, stage) combinations
2. For each unique combination:
   - Calls `audit_subject()`
   - Executes merge and removal decisions
   - Prints merge/removal actions

**Output:** Cleaned subtopic database with duplicates merged and out-of-scope items removed

---

### Stage 4: `04_finalize_subtopics.py`
**Purpose:** Normalize names, order subtopics logically, and mark as finalized.

**Key Functions:**

1. `normalize_name(name: str) -> str`
   - Very conservative normalization
   - Strips extra spaces, keeps single spaces only
   - Preserves UPSC wording and title case

2. `order_subtopics(subject, paper, stage, names) -> List[str]`
   - Calls GPT-4 as "UPSC syllabus authority"
   - Orders topics logically: foundational → advanced
   - Does NOT rename, rephrase, merge, or remove
   - Preserves exact wording

3. `finalize_subject(subject, paper, stage)`
   - Step 1: Normalize all subtopic names
   - Step 2: Call `order_subtopics()` for logical ordering
   - Step 3: Re-attach subtopics in ordered sequence
   - Step 4: Mark all subtopics `v4_finalized=True`
   - Step 5: Mark syllabus `v4=True`

**Entry Point:** `if __name__ == "__main__"`

**Process:**
1. Tracks processed (subject, paper, stage) combinations
2. For each unique combination:
   - Calls `finalize_subject()`
   - Normalizes names
   - Orders via LLM
   - Saves final state

**Output:** Finalized, ordered, normalized subtopics with all flags set

---

## Execution Flow

```
Stage 1: Generate
├─ Input: Empty or partial UPSCSyllabus records
├─ Action: AI-generate subtopics per subject
└─ Output: v1=True

Stage 2: Clean
├─ Input: v1=True syllabi
├─ Action: Add missing essential subtopics
└─ Output: Compete coverage

Stage 3: Verify
├─ Input: All subtopics
├─ Action: Merge duplicates, remove out-of-scope
└─ Output: Clean, deduplicated data

Stage 4: Finalize
├─ Input: Clean subtopics
├─ Action: Normalize names, order logically
└─ Output: v4=True (production ready)
```

---

## Database Connection
All scripts connect to:
```
Database: upsc
Host: mongodb+srv://user:user@cluster0.rgocxdb.mongodb.net/upsc
```

---

## OpenAI Configuration
- **Model:** gpt-4o-2024-08-06
- **API Feature:** Structured responses (`.responses.parse()`)
- **Pydantic Models:** Used for response schema validation

---

## Key Design Principles
1. **Conservative Approach:** Default is to DO NOTHING unless clearly necessary
2. **UPSC Authenticity:** Strict UPSC wording only, no improvements or refinements
3. **Macro-level Judgments:** Quality assessments at broad level, not detail
4. **Reversible Operations:** Each stage can be run independently
5. **Flag-based Tracking:** Version flags (v1-v4) track pipeline progress
6. **Database Integrity:** Safe unlinking before deletions, atomic operations

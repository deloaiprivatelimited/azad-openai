from mongoengine import connect
from models.upsc_syllabus import UPSCSyllabus
from models.subtopics import SubTopic
# 🔹 MongoDB connection
connect(
    db="upsc",
    host="mongodb+srv://user:user@cluster0.rgocxdb.mongodb.net/upsc"
)



from bson import ObjectId




def clean_invalid_subtopic_references(dry_run=False):
    """
    Removes SubTopic references from UPSCSyllabus.subtopics
    if the referenced SubTopic does not exist in DB.
    """

    total_syllabus = UPSCSyllabus.objects.count()
    cleaned_docs = 0
    removed_refs = 0

    print(f"Scanning {total_syllabus} UPSCSyllabus documents...\n")

    for syllabus in UPSCSyllabus.objects:
        valid_subtopics = []
        removed_for_this_doc = []

        for subtopic_ref in syllabus.subtopics:
            try:
                # MongoEngine dereference safety check
                SubTopic.objects.get(id=subtopic_ref.id)
                valid_subtopics.append(subtopic_ref)
            except SubTopic.DoesNotExist:
                removed_for_this_doc.append(str(subtopic_ref.id))

        if removed_for_this_doc:
            removed_refs += len(removed_for_this_doc)
            cleaned_docs += 1

            print(
                f"[CLEANED] {syllabus.stage} | {syllabus.paper} | {syllabus.subject}"
            )
            print(f"  Removed subtopic IDs: {removed_for_this_doc}\n")

            if not dry_run:
                syllabus.subtopics = valid_subtopics
                syllabus.save()

    print("===== SUMMARY =====")
    print(f"Total syllabus docs scanned : {total_syllabus}")
    print(f"Docs cleaned                : {cleaned_docs}")
    print(f"Invalid references removed  : {removed_refs}")
    print(f"Dry run                     : {dry_run}")

if __name__ == "__main__":
    # Set dry_run=True first to preview changes
    clean_invalid_subtopic_references(dry_run=False)

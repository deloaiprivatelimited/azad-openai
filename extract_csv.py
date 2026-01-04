import csv
from mongoengine import connect
from models.upsc_syllabus import UPSCSyllabus

# 🔹 MongoDB connection
connect(
    db="upsc",
    host="mongodb+srv://user:user@cluster0.rgocxdb.mongodb.net/upsc"
)

OUTPUT_FILE = "upsc_subtopics_export.csv"


def export_subtopics_to_csv():
    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # 🔹 Header
        writer.writerow([
            "exam",
            "stage",
            "paper",
            "subject",
            "subtopic",
            "v1_generated",
            "v2_cleaned",
            "v3_verified",
            "v4_finalized"
        ])

        row_count = 0

        # ✅ select_related() ensures dereferencing
        for syllabus in UPSCSyllabus.objects().select_related():
            for subtopic in syllabus.subtopics:

                # Defensive guard (very rare, but safe)
                if not hasattr(subtopic, "name"):
                    continue

                writer.writerow([
                    syllabus.exam,
                    syllabus.stage,
                    syllabus.paper,
                    syllabus.subject,
                    subtopic.name,
                    subtopic.v1_generated,
                    subtopic.v2_cleaned,
                    subtopic.v3_verified,
                    subtopic.v4_finalized
                ])

                row_count += 1

    print(f"✅ Exported {row_count} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    export_subtopics_to_csv()

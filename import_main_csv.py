import csv
from mongoengine import connect
from models.upsc_syllabus import UPSCSyllabus

# 🔗 MongoDB connection
connect(
    db="upsc",
    host="mongodb+srv://user:user@cluster0.rgocxdb.mongodb.net/upsc"
)

CSV_FILE = "main.csv"


def import_main_csv():
    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        count = 0
        for row in reader:
            syllabus = UPSCSyllabus(
                exam=row["exam"],
                stage=row["stage"],
                paper=row["paper"],
                subject=row["subject"],
                # remarks column is intentionally ignored
            )
            syllabus.save()
            count += 1

        print(f"✅ Imported {count} records into upsc_syllabus")


if __name__ == "__main__":
    import_main_csv()

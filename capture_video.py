import csv
import sys
import qscript

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

qscript.PATH_TO_VIDEO_FOLDER = "./video"
CSV_PATH = "input.csv"

def main():
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for row in reader:
            print(f"Processing: {row['Company Name']} ({row['City']})")
            path = qscript.CaptureVideo_Magento(
                url=row["URL"],
                company_name=row["Company Name"],
                language=row["Language"],
                country=row["Country"],
                postcode=row["Postcode"],
                city=row["City"],
                street=row["Street"],
                house_no=row["HouseNo"],
            )
            if path:
                print(f"  -> saved: {path}")
            else:
                print(f"  -> FAILED")

if __name__ == "__main__":
    main()
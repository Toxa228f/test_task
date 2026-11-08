import csv
import sys
import argparse
import time
import qscript
import video_client

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

qscript.PATH_TO_VIDEO_FOLDER = "./video"
CSV_PATH = "input.csv"

def preview_video(url, view_seconds):
    from playwright.sync_api import sync_playwright
    print(f"  -> Previewing: {url}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(url)
            
            if view_seconds > 0:
                time.sleep(view_seconds)
            else:
                print("  -> Press Enter to close the preview...")
                input()
                
            browser.close()
    except Exception as e:
        print(f"  -> Preview failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="CSV-driven video recorder")
    parser.add_argument("--server", type=str, help="URL of the web service (e.g. http://127.0.0.1:8000)")
    parser.add_argument("--view-seconds", type=int, default=0, help="Seconds to keep preview open (0 = wait for Enter)")
    args = parser.parse_args()

    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        for row in reader:
            company_name = row["Company Name"]
            print(f"Processing: {company_name} ({row['City']})")
            
            path = qscript.CaptureVideo_Magento(
                url=row["URL"],
                company_name=company_name,
                language=row["Language"],
                country=row["Country"],
                postcode=row["Postcode"],
                city=row["City"],
                street=row["Street"],
                house_no=row["HouseNo"],
            )
            
            if path:
                print(f"  -> saved: {path}")
                
                if args.server:
                    try:
                        video_url = video_client.UploadVideo(args.server, path, company_name)
                        print(f"  -> uploaded: {video_url}")
                        preview_video(video_url, args.view_seconds)
                    except Exception as e:
                        print(f"  -> Upload/Preview error: {e}")
            else:
                print(f"  -> FAILED")

if __name__ == "__main__":
    main()
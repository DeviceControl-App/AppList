import requests
from bs4 import BeautifulSoup
import csv
import os
import re
import time

input_file = "applist"
output_file = "play_store_apps.csv"
icons_dir = "icons"

os.makedirs(icons_dir, exist_ok=True)

# 1. קריאת האפליקציות שכבר קיימות ב-CSV כדי למנוע כפילויות
existing_packages = set()
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None) # דילוג על שורת הכותרת
        for row in reader:
            if row and len(row) > 0:
                existing_packages.add(row[0]) # שם החבילה נמצא בעמודה הראשונה

# 2. קריאת רשימת החבילות המלאה
with open(input_file, "r", encoding="utf-8") as f:
    packages = [line.strip() for line in f if line.strip()]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

# הגדרת מצב פתיחת הקובץ: 'a' להוספה לשורות קיימות, 'w' ליצירה מחדש
mode = "a" if os.path.exists(output_file) else "w"

with open(output_file, mode, newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    
    # כתיבת שורת הכותרות רק אם הקובץ חדש לחלוטין
    if mode == "w":
        writer.writerow(["Package Name", "App Name", "Status", "Icon Downloaded"])

    for pkg in packages:
        # דילוג על אפליקציה שכבר קיימת בקובץ
        if pkg in existing_packages:
            print(f"Skipping {pkg} - already exists in CSV.")
            continue

        url = f"https://play.google.com/store/apps/details?id={pkg}&hl=iw&gl=IL"
        icon_downloaded = "No"
        
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                title_tag = soup.find("h1")
                
                if not title_tag:
                    title_tag = soup.find("title")
                    
                if title_tag:
                    app_name = title_tag.text.strip()
                    if title_tag.name == "title":
                         app_name = app_name.replace(" - Apps on Google Play", "").strip()
                         
                    status = "Exists"
                    meta_icon = soup.find("meta", property="og:image")
                    
                    if meta_icon and meta_icon.get("content"):
                        icon_url = meta_icon["content"]
                        safe_app_name = re.sub(r'[\\/*?:"<>|]', "", app_name)
                        img_response = requests.get(icon_url, headers=headers, timeout=10)
                        
                        if img_response.status_code == 200:
                            icon_path = os.path.join(icons_dir, f"{safe_app_name}.png")
                            with open(icon_path, "wb") as img_file:
                                img_file.write(img_response.content)
                            icon_downloaded = "Yes"
                else:
                    app_name = ""
                    status = "Found but no title"
            else:
                app_name = ""
                status = f"Not Found (HTTP {r.status_code})"
        except Exception as e:
            app_name = ""
            status = f"Error: {e}"

        writer.writerow([pkg, app_name, status, icon_downloaded])
        print(f"Added: {pkg} => {app_name} ({status}) | Icon: {icon_downloaded}")
        
        # השהייה של 3 שניות כדי למנוע חסימה מגוגל פליי
        time.sleep(3)

print("Update process finished.")

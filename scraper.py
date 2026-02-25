import requests
import pandas as pd
import os
from datetime import datetime

API_URL = "https://kozut.bkkinfo.hu/api/changes"
EXCEL_FILE = "data.xlsx"

def fetch_and_save():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(API_URL, headers=headers, timeout=15)
        data = response.json()
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Ha az API egy szótárat ad vissza, amiben benne van a lista
        if isinstance(data, dict) and "changes" in data:
            entries = data["changes"]
        elif isinstance(data, list):
            entries = data
        else:
            entries = []

        new_rows = []
        for entry in entries:
            start_date = entry.get("start_date")
            end_date = entry.get("end_date")
            
            for effect in entry.get("effects", []):
                pivot = effect.get("pivot", {})
                if pivot:
                    new_rows.append({
                        "Rogzites_Ideje": current_timestamp,
                        "Pivot_ID": pivot.get("id"),
                        "Change_ID": pivot.get("change_id"),
                        "Start_Date": start_date,
                        "End_Date": end_date
                    })

        # Ha nincs adat, rögzítsünk egy hiba-sort, hogy lássuk: a kód lefutott
        if not new_rows:
            new_rows.append({
                "Rogzites_Ideje": current_timestamp,
                "Pivot_ID": "NINCS ADAT",
                "Change_ID": "API ÜRES VOLT",
                "Start_Date": "-",
                "End_Date": "-"
            })

        df_new = pd.DataFrame(new_rows)

        if os.path.exists(EXCEL_FILE):
            try:
                df_old = pd.read_excel(EXCEL_FILE)
                df_final = pd.concat([df_old, df_new], ignore_index=True)
            except:
                df_final = df_new
        else:
            df_final = df_new

        df_final.to_excel(EXCEL_FILE, index=False)
        print(f"Kész! Mentett sorok: {len(new_rows)}")

    except Exception as e:
        print(f"Hiba: {str(e)}")

if __name__ == "__main__":
    fetch_and_save()

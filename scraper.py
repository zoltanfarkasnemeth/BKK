import requests
import pandas as pd
import os
from datetime import datetime

API_URL = "https://kozut.bkkinfo.hu/api/changes"
EXCEL_FILE = "data.xlsx"

def fetch_and_save():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_rows = []

        for entry in data:
            start_date = entry.get("start_date")
            end_date = entry.get("end_date")
            for effect in entry.get("effects", []):
                pivot = effect.get("pivot", {})
                new_rows.append({
                    "Rogzites_Ideje": current_timestamp,
                    "Pivot_ID": pivot.get("id"),
                    "Change_ID": pivot.get("change_id"),
                    "Start_Date": start_date,
                    "End_Date": end_date
                })

        if not new_rows: return

        df_new = pd.DataFrame(new_rows)

        if os.path.exists(EXCEL_FILE):
            df_old = pd.read_excel(EXCEL_FILE)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new

        df_final.to_excel(EXCEL_FILE, index=False)
        print("Excel frissítve.")

    except Exception as e:
        print(f"Hiba: {e}")

if __name__ == "__main__":
    fetch_and_save()

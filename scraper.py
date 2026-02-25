import requests
import pandas as pd
import os
from datetime import datetime

# Beállítások
API_URL = "https://kozut.bkkinfo.hu/api/changes"
EXCEL_FILE = "data.xlsx"

def fetch_and_save():
    # Fejlécek, hogy valódi böngészőnek tűnjünk
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://kozut.bkkinfo.hu/"
    }

    try:
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Lekérés indítása: {current_timestamp}")
        
        response = requests.get(API_URL, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"Hiba: HTTP {response.status_code}")
            return

        data = response.json()
        new_rows = []

        # Az adatok feldolgozása a kért struktúra alapján
        if isinstance(data, list):
            for entry in data:
                # Alapadatok az esemény szintjén
                start_date = entry.get("start_date")
                end_date = entry.get("end_date")
                
                # Végigmegyünk az effects listán
                effects = entry.get("effects", [])
                for effect in effects:
                    pivot = effect.get("pivot", {})
                    if pivot:
                        # Csak a kért mezőket mentjük el
                        new_rows.append({
                            "Rogzites_Ideje": current_timestamp,
                            "id": pivot.get("id"),
                            "change_id": pivot.get("change_id"),
                            "start_date": start_date,
                            "end_date": end_date
                        })

        # Ha az API válaszolt, de nem találtunk releváns rekordot
        if not new_rows:
            new_rows.append({
                "Rogzites_Ideje": current_timestamp,
                "id": "NINCS_ADAT",
                "change_id": "API_VALASZ_URES",
                "start_date": "-",
                "end_date": "-"
            })

        # Pandas DataFrame létrehozása
        df_new = pd.DataFrame(new_rows)

        # Excel mentése (hozzáfűzés vagy új fájl)
        if os.path.exists(EXCEL_FILE) and os.path.getsize(EXCEL_FILE) > 0:
            try:
                df_old = pd.read_excel(EXCEL_FILE)
                df_final = pd.concat([df_old, df_new], ignore_index=True)
            except Exception:
                df_final = df_new
        else:
            df_final = df_new

        # Mentés tényleges végrehajtása
        df_final.to_excel(EXCEL_FILE, index=False)
        print(f"Sikeres mentés: {len(new_rows)} sor hozzáadva a(z) {EXCEL_FILE} fájlhoz.")

    except Exception as e:
        print(f"Váratlan hiba történt: {e}")

if __name__ == "__main__":
    fetch_and_save()

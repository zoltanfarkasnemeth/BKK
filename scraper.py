import requests
import pandas as pd
import os
from datetime import datetime

API_URL = "https://kozut.bkkinfo.hu/api/changes"
EXCEL_FILE = "data.xlsx"

def fetch_and_save():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = requests.get(API_URL, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"Hiba: {response.status_code}")
            return

        data = response.json()
        new_rows = []

        # A beküldött JSON struktúra pontos lekövetése
        if isinstance(data, list):
            for entry in data:
                # Alapadatok kimentése
                s_date = entry.get("start_date")
                e_date = entry.get("end_date")
                
                # Végigmegyünk az effects listán
                for effect in entry.get("effects", []):
                    pivot = effect.get("pivot", {})
                    if pivot:
                        # Itt gyűjtjük össze az általad kért 4 mezőt + az aktuális időt
                        new_rows.append({
                            "Aktualis_Ido": current_timestamp,
                            "id": pivot.get("id"),
                            "change_id": pivot.get("change_id"),
                            "start_date": s_date,
                            "end_date": e_date
                        })

        # Ha nincs adat az API-ban, csinálunk egy jelzősort, hogy ne legyen üres az Excel
        if not new_rows:
            new_rows.append({
                "Aktualis_Ido": current_timestamp,
                "id": "NINCS ADAT",
                "change_id": "API URES",
                "start_date": "-",
                "end_date": "-"
            })

        df_new = pd.DataFrame(new_rows)

        # Excel kezelés: ha már van fájl, beolvassuk és alárakjuk (concat)
        if os.path.exists(EXCEL_FILE):
            try:
                df_old = pd.read_excel(EXCEL_FILE)
                df_final = pd.concat([df_old, df_new], ignore_index=True)
            except:
                df_final = df_new
        else:
            df_final = df_new

        # Mentés - index=False fontos, hogy ne legyen felesleges első oszlop
        df_final.to_excel(EXCEL_FILE, index=False)
        print(f"Sikeres mentés: {len(new_rows)} sor hozzáadva.")

    except Exception as e:
        print(f"Hiba történt: {e}")

if __name__ == "__main__":
    fetch_and_save()

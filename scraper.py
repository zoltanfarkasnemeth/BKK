import requests
import pandas as pd
import os
from datetime import datetime

# Beállítások
API_URL = "https://kozut.bkkinfo.hu/api/changes"
EXCEL_FILE = "data.xlsx"

def fetch_and_save():
    # Fejlécek a blokkolás elkerülése érdekében
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = requests.get(API_URL, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"Hiba: HTTP {response.status_code}")
            return

        data = response.json()
        new_rows = []

        # Adatfeldolgozás a megadott JSON struktúra alapján
        if isinstance(data, list) and len(data) > 0:
            for entry in data:
                start_date = entry.get("start_date")
                end_date = entry.get("end_date")
                
                # Az 'effects' listán belüli 'pivot' adatokat keressük
                effects = entry.get("effects", [])
                for effect in effects:
                    pivot = effect.get("pivot", {})
                    if pivot:
                        new_rows.append({
                            "Rogzites_Ideje": current_timestamp,
                            "id": pivot.get("id"),
                            "change_id": pivot.get("change_id"),
                            "start_date": start_date,
                            "end_date": end_date
                        })

        # Ha lefutott, de az API válasza üres volt
        if not new_rows:
            new_rows.append({
                "Rogzites_Ideje": current_timestamp,
                "id": "NINCS_AKTIV_ESEMENY",
                "change_id": "API_URES",
                "start_date": "-",
                "end_date": "-"
            })

        df_new = pd.DataFrame(new_rows)

        # Excel fájl írása/hozzáfűzése
        if os.path.exists(EXCEL_FILE) and os.path.getsize(EXCEL_FILE) > 0:
            try:
                df_old = pd.read_excel(EXCEL_FILE)
                # Csak akkor fűzzük hozzá, ha nem teljesen üres a beolvasott fájl
                df_final = pd.concat([df_old, df_new], ignore_index=True)
            except:
                df_final = df_new
        else:
            df_final = df_new

        # Mentés
        df_final.to_excel(EXCEL_FILE, index=False)
        print(f"Sikeres futás: {len(new_rows)} sor rögzítve.")

    except Exception as e:
        print(f"Hiba történt: {e}")

if __name__ == "__main__":
    fetch_and_save()

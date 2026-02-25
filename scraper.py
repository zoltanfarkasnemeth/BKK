import requests
import pandas as pd
import os
from datetime import datetime

API_URL = "https://kozut.bkkinfo.hu/api/changes"
EXCEL_FILE = "data.xlsx"

def fetch_and_save():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = requests.get(API_URL, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"Hiba: {response.status_code}")
            return

        data = response.json()
        new_rows = []

        # Nagyon alapos keresés a JSON-ban
        if isinstance(data, list) and len(data) > 0:
            for entry in data:
                # Kért adatok kinyerése
                change_id = entry.get("id")
                start_date = entry.get("start_date")
                end_date = entry.get("end_date")
                
                effects = entry.get("effects", [])
                
                if effects:
                    for effect in effects:
                        pivot = effect.get("pivot", {})
                        if pivot:
                            new_rows.append({
                                "Rogzites_Ideje": current_timestamp,
                                "id": pivot.get("id"),
                                "change_id": change_id,
                                "start_date": start_date,
                                "end_date": end_date
                            })
                else:
                    # Ha van bejegyzés, de nincs effect, akkor is mentsünk valamit
                    new_rows.append({
                        "Rogzites_Ideje": current_timestamp,
                        "id": "NINCS_PIVOT",
                        "change_id": change_id,
                        "start_date": start_date,
                        "end_date": end_date
                    })
        else:
            # Ha az API válasza teljesen üres vagy más formátumú
            new_rows.append({
                "Rogzites_Ideje": current_timestamp,
                "id": "HIBA",
                "change_id": "URES_API_VALASZ",
                "start_date": "-",
                "end_date": "-"
            })

        df_new = pd.DataFrame(new_rows)

        # Excel összefűzés
        if os.path.exists(EXCEL_FILE):
            try:
                # Megpróbáljuk beolvasni, ha hibás, újat kezdünk
                df_old = pd.read_excel(EXCEL_FILE)
                if not df_old.empty:
                    df_final = pd.concat([df_old, df_new], ignore_index=True)
                else:
                    df_final = df_new
            except:
                df_final = df_new
        else:
            df_final = df_new

        # Mentés - index=False a tiszta táblázatért
        df_final.to_excel(EXCEL_FILE, index=False)
        print(f"Sikeresen rögzítve {len(new_rows)} sor.")

    except Exception as e:
        print(f"Hiba történt: {e}")

if __name__ == "__main__":
    fetch_and_save()

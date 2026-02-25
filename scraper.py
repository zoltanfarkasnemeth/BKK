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
        print(f"[{current_timestamp}] API lekérés indítása...")
        
        response = requests.get(API_URL, headers=headers, timeout=20)
        print(f"HTTP státusz: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Hiba: {response.status_code}")
            print(f"Válasz tartalom: {response.text[:500]}")
            return

        # Debug: nyers válasz kiírása
        raw = response.text
        print(f"Nyers válasz (első 500 kar): {raw[:500]}")

        data = response.json()
        print(f"JSON típusa: {type(data)}")
        
        if isinstance(data, list):
            print(f"Bejegyzések száma: {len(data)}")
            if len(data) > 0:
                print(f"Első bejegyzés kulcsai: {list(data[0].keys())}")
        elif isinstance(data, dict):
            print(f"Dict kulcsok: {list(data.keys())}")

        new_rows = []

        if isinstance(data, list) and len(data) > 0:
            for entry in data:
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
                            # Van effect, de nincs pivot
                            new_rows.append({
                                "Rogzites_Ideje": current_timestamp,
                                "id": "NINCS_PIVOT",
                                "change_id": change_id,
                                "start_date": start_date,
                                "end_date": end_date
                            })
                else:
                    # Nincs effect
                    new_rows.append({
                        "Rogzites_Ideje": current_timestamp,
                        "id": "NINCS_EFFECT",
                        "change_id": change_id,
                        "start_date": start_date,
                        "end_date": end_date
                    })

        elif isinstance(data, dict):
            # Ha dict formátumban jön az adat (pl. {"data": [...]} )
            items = data.get("data", data.get("changes", data.get("results", [])))
            print(f"Dict-ből kinyert lista hossza: {len(items)}")
            for entry in items:
                change_id = entry.get("id")
                start_date = entry.get("start_date")
                end_date = entry.get("end_date")
                effects = entry.get("effects", [])

                if effects:
                    for effect in effects:
                        pivot = effect.get("pivot", {})
                        new_rows.append({
                            "Rogzites_Ideje": current_timestamp,
                            "id": pivot.get("id") if pivot else "NINCS_PIVOT",
                            "change_id": change_id,
                            "start_date": start_date,
                            "end_date": end_date
                        })
                else:
                    new_rows.append({
                        "Rogzites_Ideje": current_timestamp,
                        "id": "NINCS_EFFECT",
                        "change_id": change_id,
                        "start_date": start_date,
                        "end_date": end_date
                    })
        else:
            print("FIGYELEM: Üres vagy ismeretlen API válasz!")
            new_rows.append({
                "Rogzites_Ideje": current_timestamp,
                "id": "HIBA",
                "change_id": "URES_API_VALASZ",
                "start_date": "-",
                "end_date": "-"
            })

        print(f"Új sorok száma: {len(new_rows)}")

        df_new = pd.DataFrame(new_rows)

        # Excel összefűzés
        if os.path.exists(EXCEL_FILE):
            try:
                df_old = pd.read_excel(EXCEL_FILE)
                print(f"Meglévő Excel sorok száma: {len(df_old)}")
                if not df_old.empty:
                    df_final = pd.concat([df_old, df_new], ignore_index=True)
                else:
                    df_final = df_new
            except Exception as e:
                print(f"Excel olvasási hiba (új fájl kezdése): {e}")
                df_final = df_new
        else:
            print("Excel fájl nem létezik, új fájl létrehozása.")
            df_final = df_new

        df_final.to_excel(EXCEL_FILE, index=False)
        print(f"Sikeresen mentve. Összes sor az Excelben: {len(df_final)}")

    except requests.exceptions.Timeout:
        print("Hiba: Az API nem válaszolt időben (timeout).")
    except requests.exceptions.ConnectionError:
        print("Hiba: Nem sikerült csatlakozni az API-hoz.")
    except ValueError as e:
        print(f"JSON feldolgozási hiba: {e}")
    except Exception as e:
        print(f"Ismeretlen hiba: {e}")
        raise

if __name__ == "__main__":
    fetch_and_save()

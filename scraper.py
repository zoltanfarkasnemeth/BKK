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
            print(f"Hiba: {response.status_code} - {response.text[:300]}")
            return

        data = response.json()
        print(f"JSON típusa: {type(data)}, hossza: {len(data) if isinstance(data, list) else 'dict'}")

        # --- API adatok feldolgozása ---
        api_rows = []
        items = data if isinstance(data, list) else data.get("data", data.get("changes", data.get("results", [])))

        for entry in items:
            change_id  = str(entry.get("id", ""))
            start_date = entry.get("start_date", "-")
            end_date   = entry.get("end_date", "-")
            effects    = entry.get("effects", [])

            if effects:
                for effect in effects:
                    pivot = effect.get("pivot", {})
                    api_rows.append({
                        "change_id":      change_id,
                        "pivot_id":       str(pivot.get("id", "NINCS_PIVOT")) if pivot else "NINCS_PIVOT",
                        "start_date":     start_date,
                        "end_date":       end_date,
                        "statusz":        "AKTIV",
                        "Rogzites_Ideje": current_timestamp,
                        "Lejarva_Ideje":  ""
                    })
            else:
                api_rows.append({
                    "change_id":      change_id,
                    "pivot_id":       "NINCS_EFFECT",
                    "start_date":     start_date,
                    "end_date":       end_date,
                    "statusz":        "AKTIV",
                    "Rogzites_Ideje": current_timestamp,
                    "Lejarva_Ideje":  ""
                })

        df_api = pd.DataFrame(api_rows)

        # Duplikáció szűrés az API válaszon belül is (change_id + pivot_id együtt egyedi)
        df_api = df_api.drop_duplicates(subset=["change_id", "pivot_id"], keep="first")
        print(f"API-ból feldolgozott sorok (duplikáció után): {len(df_api)}")

        # ================================================================
        # ELSŐ FUTÁS: Excel nem létezik VAGY üres/hibás → mindent mentünk
        # ================================================================
        first_run = False
        if not os.path.exists(EXCEL_FILE):
            first_run = True
        else:
            try:
                df_check = pd.read_excel(EXCEL_FILE)
                if df_check.empty or "statusz" not in df_check.columns:
                    first_run = True
            except:
                first_run = True

        if first_run:
            print("ELSŐ FUTÁS – az összes jelenlegi API adat mentése.")
            df_api.to_excel(EXCEL_FILE, index=False)
            print(f"Elmentve {len(df_api)} sor.")
            return

        # ================================================================
        # KÖVETKEZŐ FUTÁSOK
        # ================================================================
        df_old = pd.read_excel(EXCEL_FILE)
        df_old["change_id"]     = df_old["change_id"].astype(str)
        df_old["pivot_id"]      = df_old["pivot_id"].astype(str)
        df_old["start_date"]    = df_old["start_date"].astype(str)
        df_old["end_date"]      = df_old["end_date"].astype(str)
        df_old["statusz"]       = df_old["statusz"].astype(str)
        df_old["Lejarva_Ideje"] = df_old["Lejarva_Ideje"].fillna("").astype(str).replace("nan", "")

        # Összetett kulcs: change_id + pivot_id
        api_keys      = set(zip(df_api["change_id"].astype(str), df_api["pivot_id"].astype(str)))
        existing_keys = set(zip(df_old["change_id"].astype(str), df_old["pivot_id"].astype(str)))
        változott     = False

        # 1. LEZÁRT: AKTIV volt, de eltűnt az API-ból
        for idx, row in df_old.iterrows():
            key = (str(row["change_id"]), str(row["pivot_id"]))
            if row["statusz"] == "AKTIV" and key not in api_keys:
                print(f"LEZÁRT: change_id={row['change_id']}, pivot_id={row['pivot_id']} eltűnt az API-ból.")
                df_old.at[idx, "statusz"]       = "LEZART"
                df_old.at[idx, "Lejarva_Ideje"] = current_timestamp
                változott = True

        # 2. ÚJ: API-ban van, de Excelben még nincs (change_id + pivot_id páros alapján)
        new_keys = api_keys - existing_keys
        if new_keys:
            mask = [
                (str(r["change_id"]), str(r["pivot_id"])) in new_keys
                for _, r in df_api.iterrows()
            ]
            df_uj = df_api[mask].copy()
            print(f"ÚJ bejegyzések: {len(df_uj)} db")
            df_old = pd.concat([df_old, df_uj], ignore_index=True)
            változott = True

        if not változott:
            print("Nincs változás – Excel nem módosul.")
            return

        # Oszlop sorrend
        col_order = ["change_id", "pivot_id", "start_date", "end_date",
                     "statusz", "Rogzites_Ideje", "Lejarva_Ideje"]
        df_old = df_old.reindex(columns=col_order)

        df_old.to_excel(EXCEL_FILE, index=False)
        print(f"Excel frissítve. Összes sor: {len(df_old)}")

    except requests.exceptions.Timeout:
        print("Hiba: Timeout – az API nem válaszolt.")
    except requests.exceptions.ConnectionError:
        print("Hiba: Nem sikerült csatlakozni az API-hoz.")
    except ValueError as e:
        print(f"JSON hiba: {e}")
    except Exception as e:
        print(f"Ismeretlen hiba: {e}")
        raise

if __name__ == "__main__":
    fetch_and_save()

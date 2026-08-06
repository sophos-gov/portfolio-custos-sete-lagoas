# -*- coding: utf-8 -*-
import requests
import sys

API = "https://sapl.setelagoas.mg.leg.br/api/norma/normajuridica/"
HEAD = {"Accept": "application/json", "User-Agent": "AuditoriaFolhaBot/1.0 (auditoria folha municipal)"}

TYPES = [19, 8, 12, 6, 7, 11, 13, 14, 15, 10]

print("--- NORM COUNT BY TYPE ID ---")
for t in TYPES:
    try:
        r = requests.get(API, params={"tipo": t, "page": 1}, headers=HEAD, timeout=10)
        if r.status_code == 200:
            count = r.json().get("count", 0)
            # Fetch first item to see what it is
            results = r.json().get("results", [])
            first_item = results[0].get("__str__") if results else "None"
            print(f"Type ID {t:2d} | Count: {count:5d} | First item example: {first_item}")
        else:
            print(f"Type ID {t:2d} | HTTP Error: {r.status_code}")
    except Exception as e:
        print(f"Type ID {t:2d} | Exception: {e}")

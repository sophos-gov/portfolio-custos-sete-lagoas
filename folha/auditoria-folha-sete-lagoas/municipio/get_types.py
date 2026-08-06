# -*- coding: utf-8 -*-
import requests
import json

API_TYPES = "https://sapl.setelagoas.mg.leg.br/api/norma/tiponormajuridica/"
HEAD = {"Accept": "application/json", "User-Agent": "AuditoriaFolhaBot/1.0 (auditoria folha municipal)"}

try:
    r = requests.get(API_TYPES, headers=HEAD, timeout=40)
    if r.status_code == 200:
        data = r.json()
        results = data.get("results", [])
        print("--- TYPES OF JURIDICAL NORMS IN SETE LAGOAS SAPL ---")
        for x in results:
            print(f"ID: {x.get('id')} | Sigla: {x.get('sigla')} | Nome: {x.get('nome')}")
    else:
        print(f"Error: {r.status_code}")
except Exception as e:
    print(f"Exception: {e}")

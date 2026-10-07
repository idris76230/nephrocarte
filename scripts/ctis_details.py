"""Télécharge les fiches détaillées CTIS des essais néphro FR/BE encore actifs (codes 2-5)."""
import json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from rules import ONCO, NEPH
s = json.load(open(sys.argv[1])); out = {}
# fiches déjà téléchargées réutilisées si leur date de mise à jour n'a pas changé
cache = json.load(open(sys.argv[2])) if os.path.exists(sys.argv[2]) else {}
for k, x in s.items():
    c = x.get("conditions") or ""; t = x.get("ctTitle") or ""
    if x["ctStatus"] not in (2, 3, 4, 5): continue
    if not NEPH.search(ONCO.sub(" ", c + " | " + t)) or (ONCO.search(c) and not NEPH.search(ONCO.sub(" ", c))): continue
    if k in cache and cache[k].get("_lu") == x.get("lastUpdated"):
        out[k] = cache[k]; continue
    for i in range(3):
        try:
            out[k] = json.load(urllib.request.urlopen(f"https://euclinicaltrials.eu/ctis-public-api/retrieve/{k}", timeout=60))
            out[k]["_lu"] = x.get("lastUpdated"); break
        except Exception as e:
            time.sleep(2)
    time.sleep(0.15)
json.dump(out, open(sys.argv[2], "w"))
print(len(out), "fiches")

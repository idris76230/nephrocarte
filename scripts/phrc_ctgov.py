"""Cherche sur ClinicalTrials.gov, par acronyme, les PHRC néphro récents (2019+) et garde les fiches encore actives.
Usage : python3 phrc_ctgov.py data/phrc_nephro.json data/raw/ctgov_phrc.json
"""
import json, re, sys, time, unicodedata, urllib.parse, urllib.request
def k(s): return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
def acro(s): return re.sub(r"[^a-z0-9]", "", re.sub(r"\b(study|trial|etude|essai)\b", "", k(s)))
ACTIVE = {"RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION", "ACTIVE_NOT_RECRUITING", "UNKNOWN"}
out = {}
for p in json.load(open(sys.argv[1])):
    if int(p["annee"] or 0) < 2019 or len(acro(p["acro"])) < 3: continue
    q = urllib.parse.urlencode({"query.term": f'AREA[Acronym]"{p["acro"].strip()}"', "pageSize": 10})
    try:
        res = json.load(urllib.request.urlopen("https://clinicaltrials.gov/api/v2/studies?" + q, timeout=60))["studies"]
    except Exception:
        continue
    for s in res:
        ps = s["protocolSection"]
        if acro(ps["identificationModule"].get("acronym", "")) == acro(p["acro"]) and ps["statusModule"]["overallStatus"] in ACTIVE:
            if ps["statusModule"]["overallStatus"] == "UNKNOWN" and ps["statusModule"].get("lastUpdatePostDateStruct", {}).get("date", "") < "2024":
                continue
            out[ps["identificationModule"]["nctId"]] = s
    time.sleep(0.1)
json.dump(out, open(sys.argv[2], "w"))
print(len(out), "fiches PHRC actives récupérées :", ", ".join(v["protocolSection"]["identificationModule"].get("acronym", "") for v in out.values()))

"""Ajoute aux études filtrées (sortie de process.py + norm.py) : pathologies, contacts,
statut et coordonnées GPS par centre, identifiant EU CT, résumé court.
Usage : python3 enrich.py data/raw/ctgov_frbe.json data/trials_n.json app/data.json
"""
import json, os, re, sys

raw = json.load(open(sys.argv[1]))
_extra = os.path.join(os.path.dirname(sys.argv[1]), "ctgov_phrc.json")
if os.path.exists(_extra):
    for _k, _v in json.load(open(_extra)).items(): raw.setdefault(_k, _v)
rows = json.load(open(sys.argv[2]))

sys.path.insert(0, __import__("os").path.dirname(__file__))
from rules import PATHO
SITE_ST = {"RECRUITING": "Ouvert", "NOT_YET_RECRUITING": "À venir", "ACTIVE_NOT_RECRUITING": "Fermé",
           "ENROLLING_BY_INVITATION": "Sur invitation", "SUSPENDED": "Suspendu"}
SKIP_SITE = {"WITHDRAWN", "COMPLETED", "TERMINATED"}
ST_SHORT = {"Recrutement ouvert": "Ouvert", "Pas encore ouvert": "À venir",
            "Sur invitation": "Sur invitation", "Actif, recrutement clos": "Fermé", "Statut non précisé": "Non précisé"}

def contact(c):
    return {k: v for k, v in {"n": c.get("name", "").strip(), "r": c.get("role", ""),
            "e": c.get("email", ""), "t": c.get("phone", "")}.items() if v}

out = []
for r in rows:
    p = raw[r["id"]]["protocolSection"]
    idm = p["identificationModule"]; cl = p.get("contactsLocationsModule", {})
    cm = p.get("conditionsModule", {})
    text = " | ".join(cm.get("conditions", []) + cm.get("keywords", []) + [idm.get("briefTitle", ""), idm.get("officialTitle", "")])
    patho = [(th, n) for th, n, pat in PATHO if th in r["th"] and re.search(pat, text, re.I)]
    euct = [x["id"] for x in idm.get("secondaryIdInfos", []) if re.match(r"^\d{4}-\d{5,6}-\d{2}", x.get("id", "")) ]
    # site-level info, keeping only FR/BE active sites
    by_key = {}
    for l in cl.get("locations", []):
        if l.get("country") not in ("France", "Belgium") or l.get("status") in SKIP_SITE:
            continue
        by_key[(l.get("facility", ""), l.get("city", ""))] = l
    sites = []
    for c in r["ce"]:
        l = by_key.get((c["f"], c["c"]))
        if l is None:
            continue
        g = l.get("geoPoint") or {}
        sites.append({"f": c["f"], "v": c["v"], "p": c["p"], "z": l.get("zip", ""),
                      "s": SITE_ST.get(l.get("status"), "Non précisé" if not l.get("status") else l["status"]),
                      "la": round(g["lat"], 4) if g else None, "lo": round(g["lon"], 4) if g else None,
                      "k": [contact(x) for x in l.get("contacts", [])]})
    summ = re.sub(r"\s+", " ", p.get("descriptionModule", {}).get("briefSummary", "")).strip()
    out.append({
        "id": r["id"], "eu": euct[:1], "ac": r["ac"], "t": r["t"], "st": ST_SHORT[r["st"]],
        "cat": r["cat"], "fund": r["fund"], "th": r["th"], "pa": sorted({n for _, n in patho}),
        "ph": r["ph"], "sp": r["sp"], "ped": r["ped"], "n": r["n"], "start": r["start"],
        "sum": (summ[:420] + "…") if len(summ) > 420 else summ,
        "cc": [contact(x) for x in cl.get("centralContacts", [])][:2],
        "ce": sites,
    })
json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False, separators=(",", ":"))
import collections
print(len(out), "études ;", sum(len(o["ce"]) for o in out), "centres actifs ;",
      sum(1 for o in out if o["pa"]), "avec pathologie ;", sum(1 for o in out if o["eu"]), "avec EU CT")
print(collections.Counter(n for o in out for n in o["pa"]).most_common(40))
json.dump({n: th for th, n, _ in PATHO}, open(sys.argv[3].replace("data.json", "pmap.json"), "w"), ensure_ascii=False)

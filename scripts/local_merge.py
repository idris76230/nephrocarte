"""Ajoute les sources locales (pages « recherche » des services, listes transmises par les centres) : data/local/*.json
- étude déjà connue (même NCT) : le centre local est ajouté ou passé « Ouvert », la présentation en français et le financement sont repris ;
- étude inconnue : ajoutée à partir de la fiche locale (et de ClinicalTrials.gov si un NCT est donné).
Usage : python3 local_merge.py app/data.json data/local app/data.json
"""
import glob, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from rules import theme, PATHO, PHRC

data = json.load(open(sys.argv[1]))
by_nct = {}
for d in data:
    n = d["id"] if d["id"].startswith("NCT") else d.get("nct", "")
    if n: by_nct[n] = d

def coords(city):
    pts = [(c["la"], c["lo"]) for d in data for c in d["ce"] if c["v"] == city and c.get("la") is not None]
    return (round(sum(p[0] for p in pts) / len(pts), 4), round(sum(p[1] for p in pts) / len(pts), 4)) if pts else (None, None)

def funding(fin, sponsor_text):
    if re.search(r"\bPHRC|PHRCI|PHRC-?I|PHRC-?N|PRME|PREPS|DGOS", fin or "", re.I): return "PHRC / DGOS"
    return None

def ctgov(nct):
    try:
        s = json.load(urllib.request.urlopen(f"https://clinicaltrials.gov/api/v2/studies/{nct}", timeout=60))["protocolSection"]
    except Exception:
        return None
    return s

added = updated = 0
for f in sorted(glob.glob(os.path.join(sys.argv[2], "*.json"))):
    src = json.load(open(f))
    la, lo = coords(src["centre"]["v"])
    centre = dict(src["centre"], s="Ouvert", la=la, lo=lo)
    label = src["source"].split(" — ")[0]
    for r in src["projects"]:
        fund = funding(r.get("fin"), r.get("sp"))
        fr = " ".join(x for x in [r.get("pres", ""), ("Population : " + r["pop"]) if r.get("pop") else "",
                                  ("Objectif : " + r["obj"]) if r.get("obj") else ""] if x)
        d = by_nct.get(r.get("nct"))
        if d:
            updated += 1
            here = [c for c in d["ce"] if c["v"] == centre["v"]]
            if here:
                for c in here:
                    if c["s"] in ("À venir", "Non précisé"): c["s"] = "Ouvert"
                    if not any(k.get("e") or k.get("t") for k in c["k"]): c["k"] = centre["k"]
            else:
                d["ce"].append(dict(centre))
            if fund and d["fund"] != "Industriel": d["fund"] = fund
            if d["st"] in ("À venir", "Fermé") and not here: pass  # on ne contredit pas le registre au niveau de l'étude
            d.setdefault("loc", []).append({"src": label, "url": r["url"]})
            d["fr"] = d.get("fr") or fr
            if not d["ac"]: d["ac"] = r["ac"]
            continue
        # étude absente : fiche locale, complétée par ClinicalTrials.gov si possible
        s = ctgov(r["nct"]) if r.get("nct") else None
        title = r.get("long") or r.get("pres") or r["ac"]
        cat = "Observationnel / cohorte" if r["obs"] else "Interventionnel"
        sp = r.get("sp", "")
        ph, ped, n, st = "", False, None, "Ouvert"
        th, pa = r["th"], r["pa"]
        if s:
            title = title if (r.get("long") or r.get("pres")) else s["identificationModule"].get("briefTitle", title)
            cat = "Interventionnel" if s["designModule"]["studyType"] == "INTERVENTIONAL" else cat
            # statut du registre s'il est explicite ; « UNKNOWN » (non mis à jour) : on suit la page du centre
            st = {"RECRUITING": "Ouvert", "NOT_YET_RECRUITING": "À venir", "ENROLLING_BY_INVITATION": "Sur invitation",
                  "ACTIVE_NOT_RECRUITING": "Fermé", "COMPLETED": "Fermé", "TERMINATED": "Fermé"}.get(s["statusModule"]["overallStatus"], "Ouvert")
            ph = ", ".join(x.replace("PHASE", "Phase ") for x in s["designModule"].get("phases", []) if x != "NA")
            ped = "CHILD" in s.get("eligibilityModule", {}).get("stdAges", [])
            n = s["designModule"].get("enrollmentInfo", {}).get("count")
            cm = s.get("conditionsModule", {})
            en = " | ".join(cm.get("conditions", []) + cm.get("keywords", []) + [s["identificationModule"].get("briefTitle", "")])
            t2 = theme(en)
            if t2 != ["Autre néphrologie"]: th = sorted(set(th) | set(t2))
            pa = sorted(set(pa) | {p for t, p, pat in PATHO if t in th and re.search(pat, en, re.I)})
        industry = bool(re.search(r"pharma|therapeutics|novartis|astrazeneca|alexion|bayer|vertex|glaxo|boehringer|calico|roche|sanofi|lilly|inc\b|ag\b", sp, re.I))
        data.append({"id": r.get("nct") or r["url"], "nct": r.get("nct", ""), "eu": [], "ac": r["ac"], "t": title,
                     "st": st, "cat": cat, "fund": "Industriel" if industry else (fund or "Académique (autre)"),
                     "th": th, "pa": pa, "ph": ph, "sp": sp, "ped": ped, "n": n, "start": "", "sum": "", "fr": fr,
                     "cc": [], "ce": [dict(centre, s=st)], "src": label, "loc": [{"src": label, "url": r["url"]}]})
        added += 1
        if r.get("nct"): by_nct[r["nct"]] = data[-1]
json.dump(data, open(sys.argv[3], "w"), ensure_ascii=False, separators=(",", ":"))
print(f"sources locales : {updated} études complétées, {added} ajoutées -> {len(data)} études")

"""Rapproche les PHRC néphro (listes DGOS) des études de l'outil, par acronyme (+ cohérence de l'établissement).
- étude trouvée : financement « PHRC / DGOS » + libellé (ex. « PHRC-N 2020 »)
- non trouvée : recherche de l'acronyme sur ClinicalTrials.gov pour connaître le NCT et le statut (rapport à valider)
Usage : python3 phrc_match.py app/data.json data/phrc_nephro.json app/data.json data/phrc_rapport.csv
"""
import csv, json, re, sys, unicodedata, urllib.parse, urllib.request

data = json.load(open(sys.argv[1])); phrc = json.load(open(sys.argv[2]))
def k(s): return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
def acro(s): return re.sub(r"[^a-z0-9]", "", re.sub(r"\b(study|trial|etude|essai)\b", "", k(s)))
CITY = ["paris", "ap-hp", "aphp", "marseille", "aphm", "ap-hm", "lyon", "hcl", "toulouse", "bordeaux", "nantes", "rennes", "brest",
        "lille", "strasbourg", "hus", "nancy", "reims", "amiens", "rouen", "caen", "tours", "poitiers", "angers", "limoges",
        "clermont", "saint-etienne", "saint etienne", "grenoble", "dijon", "besancon", "montpellier", "nimes", "nice", "foch",
        "la roche", "vendee", "annecy"]
ALIAS = {"ap-hp": "paris", "aphp": "paris", "assistance publique - hopitaux de paris": "paris", "aphm": "marseille", "ap-hm": "marseille",
         "hcl": "lyon", "hospices civils": "lyon", "hus": "strasbourg", "foch": "suresnes", "vendee": "la roche", "charles nicolle": "rouen",
         "bocage": "dijon"}
def cities(s):
    s = k(s); out = {c for c in CITY if c in s}
    out |= {v for a, v in ALIAS.items() if a in s}
    return {ALIAS.get(c, c) for c in out}

_al = __import__("os").path.join(__import__("os").path.dirname(sys.argv[2]), "phrc_alias.json")
ALIAS_NCT = {a: n for a, n in json.load(open(_al)).items() if not a.startswith("_")} if __import__("os").path.exists(_al) else {}
idx = {}
for d in data:
    if d.get("ac"): idx.setdefault(acro(d["ac"]), []).append(d)
rows, matched = [], 0
for p in phrc:
    a = acro(p["acro"]); label = f'{p["type"]} {p["annee"]}'
    cands = idx.get(a, []) if len(a) >= 3 else []
    if not cands and ALIAS_NCT.get(p["acro"].strip()):
        cands = [d for d in data if ALIAS_NCT[p["acro"].strip()] in (d["id"], d.get("nct"))]
    pc = cities(p["etab"])
    good = [d for d in cands if not pc or pc & cities(d["sp"]) or d["fund"] != "Industriel"]
    status, nct, note = "", "", ""
    if good:
        matched += 1
        for d in good:
            if d["fund"] != "Industriel": d["fund"] = "PHRC / DGOS"
            d["phrc"] = label
        nct = good[0]["id"] if good[0]["id"].startswith("NCT") else good[0].get("nct", "")
        status, note = "dans l'outil", good[0]["st"]
    else:
        # recherche de l'acronyme sur ClinicalTrials.gov (tous statuts), avec un promoteur français cohérent
        try:
            q = urllib.parse.urlencode({"query.term": f'AREA[Acronym]"{p["acro"].strip()}"', "pageSize": 10,
                                        "fields": "NCTId,Acronym,OverallStatus,LeadSponsorName,BriefTitle"})
            res = json.load(urllib.request.urlopen("https://clinicaltrials.gov/api/v2/studies?" + q, timeout=60))["studies"]
        except Exception:
            res = []
        best = None
        for s in res:
            ps = s["protocolSection"]; sp = ps["sponsorCollaboratorsModule"]["leadSponsor"]["name"]
            if acro(ps["identificationModule"].get("acronym", "")) == a and (not pc or pc & cities(sp)):
                best = ps; break
        if best:
            nct = best["identificationModule"]["nctId"]; st = best["statusModule"]["overallStatus"]
            status = "sur ClinicalTrials.gov, hors outil"
            note = {"COMPLETED": "terminé", "TERMINATED": "arrêté", "WITHDRAWN": "retiré", "UNKNOWN": "statut non mis à jour",
                    "SUSPENDED": "suspendu"}.get(st, st.lower()) + " — ou thème non retenu par le filtre"
        else:
            status, note = "introuvable", "pas encore enregistré, ou enregistré sous un autre acronyme"
    rows.append({"PHRC": label, "numero": p["num"], "acronyme": p["acro"], "porteur": p["porteur"], "etablissement": p["etab"],
                 "titre": p["titre"], "resultat": status, "NCT": nct, "detail": note})
# lauréats récents (2021+) introuvables dans les registres : ajoutés « À venir », centre = établissement porteur
CITYNAME = {"paris": "Paris & IDF", "suresnes": "Paris & IDF", "marseille": "Marseille", "lyon": "Lyon", "toulouse": "Toulouse",
            "bordeaux": "Bordeaux", "nantes": "Nantes", "rennes": "Rennes", "brest": "Brest", "lille": "Lille", "strasbourg": "Strasbourg",
            "nancy": "Nancy", "reims": "Reims", "amiens": "Amiens", "rouen": "Rouen", "caen": "Caen", "tours": "Tours", "poitiers": "Poitiers",
            "angers": "Angers", "limoges": "Limoges", "clermont": "Clermont-Ferrand", "saint-etienne": "Saint-Étienne",
            "saint etienne": "Saint-Étienne", "grenoble": "Grenoble", "dijon": "Dijon", "besancon": "Besançon", "montpellier": "Montpellier",
            "nimes": "Nîmes", "nice": "Nice", "annecy": "Annecy", "la roche": "La Roche-sur-Yon"}
def pt(v):
    pts = [(c["la"], c["lo"]) for d in data for c in d["ce"] if c["v"] == v and c.get("la") is not None]
    return (round(sum(a for a, _ in pts) / len(pts), 4), round(sum(b for _, b in pts) / len(pts), 4)) if pts else (None, None)
sys.path.insert(0, __import__("os").path.dirname(__file__))
from rules import PATHO
FR_TH = [(r"greffe|transplant|greffon|rejet|donneur", "Transplantation"), (r"dialys|épuration extra", "Dialyse / suppléance"),
         (r"insuffisance rénale aigu|IRA\b|néphroprotection", "Insuffisance rénale aiguë"),
         (r"lupique|IgA|ANCA|vascularite|néphrotique|glomérul|extramembraneuse|SHU", "Glomérulopathies / néphropathies immunes"),
         (r"polykystose|cystinose|hyperoxalurie|Alport|Fabry", "Maladies rénales rares / génétiques"),
         (r"maladie rénale chronique|MRC|protéinurie|albuminurie|hyperkali|hyperparathyro|calcitriol|alfacalcidol|cinacalcet", "MRC / néphroprotection / cardio-rénal"),
         (r"lithiase|pyélonéphrite|infection urinaire", "Lithiase / infections urinaires")]
added = 0
for r, p in zip(rows, phrc):
    if r["resultat"] != "introuvable" or int(p["annee"] or 0) < 2021: continue
    c = sorted(cities(p["etab"]))
    v = CITYNAME.get(c[0], c[0].title()) if c else ""
    la, lo = pt(v)
    th = [t for pat, t in FR_TH if re.search(pat, p["titre"], re.I)] or ["Autre néphrologie"]
    data.append({"id": p["num"], "nct": "", "eu": [], "ac": p["acro"].strip(), "t": p["titre"], "st": "À venir",
                 "cat": "Interventionnel" if re.search(r"randomis|essai|efficacit|versus|\bvs\b", p["titre"], re.I) else "Observationnel / cohorte",
                 "fund": "PHRC / DGOS", "phrc": f'{p["type"]} {p["annee"]}', "th": th, "pa": [], "ph": "", "sp": p["etab"], "ped": bool(re.search(r"pédiatr|enfant", p["titre"], re.I)),
                 "n": None, "start": "", "sum": "", "fr": f'Lauréat {p["type"]} {p["annee"]} (projet {p["num"]}), pas encore enregistré dans un registre public. Porteur : {p["porteur"]}, {p["etab"]}.',
                 "cc": [], "ce": [{"f": p["etab"].title(), "v": v, "p": "FR", "z": "", "s": "À venir", "la": la, "lo": lo,
                                   "k": [{"n": p["porteur"], "r": "STUDY_CHAIR"}]}] if v else [], "src": "Liste DGOS des lauréats"})
    r["resultat"] = "ajouté à l'outil (À venir)"; added += 1
print("lauréats récents ajoutés comme « À venir » :", added)
json.dump(data, open(sys.argv[3], "w"), ensure_ascii=False, separators=(",", ":"))
with open(sys.argv[4], "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=";"); w.writeheader(); w.writerows(rows)

import collections
print(f"{len(phrc)} PHRC néphro : {matched} retrouvés dans l'outil")
print(collections.Counter(r["resultat"] for r in rows))
print("études étiquetées PHRC dans l'outil :", sum(1 for d in data if d["fund"] == "PHRC / DGOS"))

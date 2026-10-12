"""Ajoute les sources locales (pages « recherche » des services, listes transmises par les centres) : data/local/*.json
- étude déjà connue (même NCT) : le centre local est ajouté ou passé « Ouvert », la présentation en français et le financement sont repris ;
- étude inconnue : ajoutée à partir de la fiche locale (et de ClinicalTrials.gov si un NCT est donné), sauf si le registre la dit terminée.
Sans NCT, l'étude est reconnue par son acronyme s'il est sans ambiguïté (une seule étude, même promoteur).
Format d'une source : {"source", "source_url", "centre": {f, v, p, z, k, match?}, "projects": [{ac, long?, pres?, pop?, obj?, fin?, sp, nct, url, th, pa, obs, k?}]}
  centre.match : motif identifiant le centre parmi les sites de la même ville (indispensable dans une ville à plusieurs hôpitaux) ;
  k d'un projet : contacts propres à l'étude (investigateur, coordinateur), sinon ceux du centre.
Usage : python3 local_merge.py app/data.json data/local app/data.json
"""
import glob, json, os, re, sys, unicodedata, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from rules import theme, PATHO, PHRC

data = json.load(open(sys.argv[1]))
by_nct = {}
for d in data:
    n = d["id"] if d["id"].startswith("NCT") else d.get("nct", "")
    if n: by_nct[n] = d

def norm(s): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower())
by_ac = {}
for d in data:
    if len(norm(d.get("ac"))) >= 4: by_ac.setdefault(norm(d["ac"]), []).append(d)

def by_acronym(r, city):
    """acronyme identique (ou contenu dans l'acronyme du registre, ex. PACIFIC -> BaxDuo-Pacific) ;
    une seule étude, du même promoteur ou ayant déjà un site dans la même ville."""
    a = norm(r.get("ac"))
    if len(a) < 4: return None
    w = [x[:6] for x in re.findall(r"[a-z]{4,}", norm_words(r.get("sp", ""))) if x[:6] not in ("univer", "hospit", "medica", "center", "centre", "pharma", "therap")]
    ok = lambda d: (w and any(x in norm_words(d.get("sp", "")) for x in w)) or any(c["v"] == city for c in d["ce"])
    exact = [d for d in by_ac.get(a, []) if ok(d)]
    if len(exact) == 1: return exact[0]
    if exact: return None
    part = [d for d in data if re.search(r"(^|[^a-z0-9])" + re.escape(r["ac"].lower()) + r"($|[^a-z0-9])", (d.get("ac") or "").lower())
            and w and any(x in norm_words(d.get("sp", "")) for x in w)]
    return part[0] if len(part) == 1 else None

def norm_words(s): return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()

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
skipped = []
for f in sorted(glob.glob(os.path.join(sys.argv[2], "*.json"))):
    src = json.load(open(f))
    la, lo = coords(src["centre"]["v"])
    match = src["centre"].get("match")
    centre = {k: v for k, v in src["centre"].items() if k != "match"}
    centre.update(s="Ouvert", la=la, lo=lo)
    label = src["source"].split(" — ")[0]
    for r in src["projects"]:
        cen = dict(centre, k=r.get("k") or centre["k"])
        fund = funding(r.get("fin"), r.get("sp"))
        fr = " ".join(x for x in [r.get("pres", ""), ("Population : " + r["pop"]) if r.get("pop") else "",
                                  ("Objectif : " + r["obj"]) if r.get("obj") else ""] if x)
        d = by_nct.get(r.get("nct")) or (None if r.get("nct") else by_acronym(r, centre["v"]))
        if d:
            updated += 1
            here = [c for c in d["ce"] if c["v"] == centre["v"] and (not match or re.search(match, c.get("f", "") + " " + c.get("e", ""), re.I))]
            if here:
                for c in here:
                    if c["s"] in ("À venir", "Non précisé", "À confirmer"): c["s"] = "Ouvert"
                    c["k"] = c["k"] + [k for k in cen["k"] if norm(k.get("n")) not in [norm(x.get("n")) for x in c["k"]]]
            else:
                d["ce"].append(dict(cen))
            if fund and d["fund"] != "Industriel": d["fund"] = fund
            if d["st"] == "À confirmer": d["st"], d["upd"] = "Ouvert", ""  # la page du service confirme l'étude
            if d["st"] in ("À venir", "Fermé") and not here: pass  # on ne contredit pas le registre au niveau de l'étude
            d.setdefault("loc", []).append({"src": label, "url": r["url"]})
            d["fr"] = d.get("fr") or fr
            if not d["ac"]: d["ac"] = r["ac"]
            continue
        # étude absente : fiche locale, complétée par ClinicalTrials.gov si possible
        s = ctgov(r["nct"]) if r.get("nct") else None
        if s and s["statusModule"]["overallStatus"] in ("COMPLETED", "TERMINATED", "WITHDRAWN"):
            skipped.append(f"{r['ac']} ({r['nct']})"); continue
        title = r.get("long") or r.get("pres") or r["ac"]
        cat = "Observationnel / cohorte" if r["obs"] else "Interventionnel"
        sp = r.get("sp", "")
        ph, ped, n, st = "", False, None, "Ouvert"
        th, pa = r["th"], r["pa"]
        if s:
            title = title if (r.get("long") or r.get("pres")) else s["identificationModule"].get("briefTitle", title)
            r["ac"] = s["identificationModule"].get("acronym") or r["ac"]  # acronyme du registre plutôt que le n° de protocole
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
        # promoteur académique : hôpital, université, institut, fondation… ; tout autre promoteur nommé est industriel
        academic = re.search(r"univ|hosp|h[ôo]pita|\bchu\b|\bchr\b|clinique|\buz\b|\baz\b|medical cent|center|centre|institut|inserm|ap-?hp|\bhcl\b|"
                             r"hospices|fondation|foundation|vzw|asbl|aisbl|kce|commission|société|society|groupe|group|erasme|calydial|\bcub\b|plan national|minist|projet", sp, re.I)
        industry = bool(sp.strip()) and not academic
        data.append({"id": r.get("nct") or r["url"], "nct": r.get("nct", ""), "eu": [], "ac": r["ac"], "t": title,
                     "st": st, "cat": cat, "fund": "Industriel" if industry else (fund or "Académique (autre)"),
                     "th": th, "pa": pa, "ph": ph, "sp": sp, "ped": ped, "n": n, "start": "", "sum": "", "fr": fr,
                     "cc": [], "ce": [dict(cen, s=st)], "src": label, "loc": [{"src": label, "url": r["url"]}]})
        added += 1
        if r.get("nct"): by_nct[r["nct"]] = data[-1]
        if len(norm(r["ac"])) >= 4: by_ac.setdefault(norm(r["ac"]), []).append(data[-1])
json.dump(data, open(sys.argv[3], "w"), ensure_ascii=False, separators=(",", ":"))
print(f"sources locales : {updated} études complétées, {added} ajoutées -> {len(data)} études"
      + (f" ; terminées selon ClinicalTrials.gov, non ajoutées : {', '.join(skipped)}" if skipped else ""))

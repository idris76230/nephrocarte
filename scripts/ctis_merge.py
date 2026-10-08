"""Fusionne les essais CTIS (registre européen) avec les études ClinicalTrials.gov déjà enrichies.
- doublons (même NCT ou même numéro EU CT) : la fiche ClinicalTrials.gov est gardée et reçoit le numéro EU CT ;
  ses centres sont remplacés par ceux de CTIS si CTIS donne plus de contacts.
- essais présents seulement dans CTIS : ajoutés.
Usage : python3 ctis_merge.py app/data.json data/raw/ctis_search.json data/raw/ctis_details.json app/data.json
"""
import json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(__file__))
from rules import theme, PATHO, PHRC, onco_study
from norm import city

data = json.load(open(sys.argv[1]))
search = json.load(open(sys.argv[2]))
details = json.load(open(sys.argv[3]))

def k(s): return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().strip()

# coordonnées tirées des centres ClinicalTrials.gov : par ville, puis par département / zone postale
city_pts, zip_pts = {}, {}
for d in data:
    for c in d["ce"]:
        if c.get("la") is None: continue
        city_pts.setdefault(k(c["v"]), []).append((c["la"], c["lo"]))
        if c.get("z"): zip_pts.setdefault(c["p"] + str(c["z"])[:2], []).append((c["la"], c["lo"]))
mean = lambda pts: (round(sum(p[0] for p in pts) / len(pts), 4), round(sum(p[1] for p in pts) / len(pts), 4))
def geo(v, p, z):
    pts = city_pts.get(k(v)) or zip_pts.get(p + str(z or "")[:2])
    return mean(pts) if pts else (None, None)

def country_status(ev):
    types = {e["notificationType"] for e in ev}
    if types & {"END_OF_TRIAL", "END_OF_RECRUITMENT", "EARLY_TERMINATION"}: return "Fermé"
    if "START_OF_RECRUITMENT" in types: return "Ouvert"
    return "À venir"
ORDER = ["Ouvert", "À venir", "Sur invitation", "Fermé"]

def ctis_record(ct, det, srch):
    a = det["authorizedApplication"]; p1 = a["authorizedPartI"]
    ids = p1["trialDetails"]["clinicalTrialIdentifiers"]
    full = (ids.get("publicTitle") or ids.get("fullTitle") or srch.get("ctTitle") or "").strip()
    fr = next((t["attributeTranslation"] for t in ids.get("publicTitleTranslations", []) if "French" in t.get("languageDescription", "")), "")
    m = re.search(r"\(([A-Z0-9][A-Za-z0-9\-]{2,20})\)\s*$", full)
    m2 = re.match(r"^([A-Z][A-Za-z0-9\-]{2,24})\s*[-–:,]\s", full)
    short = (srch.get("shortTitle") or ids.get("shortTitle") or "").strip()
    # un code de protocole (D740FC00001, CSET 2025/3840, APHP240937) n'est pas un acronyme : on veut surtout des lettres
    looks_acro = re.fullmatch(r"[A-Z][A-Za-z\-']{2,24}(-?\d{1,2})?", short) is not None
    if m2 and sum(ch.isupper() for ch in m2.group(1)) < 3: m2 = None  # « Randomized, … » n'est pas un acronyme
    acro = m.group(1) if m else m2.group(1) if m2 else short if looks_acro else ""
    title = fr or full
    if acro: title = re.sub(r"^" + re.escape(acro) + r"\s*[-–:]\s*|\s*\(" + re.escape(acro) + r"\)\s*$", "", title)
    status_by_country = {t["mscName"]: country_status(t["events"]) for t in det.get("events", {}).get("trialEvents", [])}
    sites = []
    for part in a.get("authorizedPartsII", []):
        cn = part["mscInfo"].get("countryName")
        if cn not in ("France", "Belgium"): continue
        pc = "FR" if cn == "France" else "BE"
        for s in part.get("trialSites", []):
            oa = s.get("organisationAddressInfo", {}); org = oa.get("organisation", {}); ad = oa.get("address", {})
            pi = s.get("personInfo", {})
            v = city(ad.get("city", "") or "")
            la, lo = geo(v, pc, ad.get("postcode"))
            name = org.get("name", "") + (f" — {s['departmentName']}" if s.get("departmentName") else "")
            ct_ = {"n": " ".join(x for x in (pi.get("firstName"), pi.get("lastName")) if x), "r": "PRINCIPAL_INVESTIGATOR",
                   "e": pi.get("email") or oa.get("email", ""), "t": pi.get("telephone") or oa.get("phone", "")}
            sites.append({"f": name, "v": v, "p": pc, "z": ad.get("postcode", ""), "s": status_by_country.get(cn, "À venir"),
                          "la": la, "lo": lo, "k": [{kk: vv for kk, vv in ct_.items() if vv}]})
    st = min((status_by_country.get(c, "À venir") for c in ("France", "Belgium") if any(s["p"] == ("FR" if c == "France" else "BE") for s in sites)),
             key=ORDER.index, default="À venir")
    sponsor = p1["sponsors"][0]["organisation"] if p1.get("sponsors") else {}
    cond = srch.get("conditions") or ""
    th = theme(" | ".join([cond, full]))
    pa = sorted({n for t, n, pat in PATHO if t in th and re.search(pat, cond + " | " + full, re.I)})
    text = json.dumps(det)
    nct = re.findall(r"NCT\d{8}", text)
    fund = "Industriel" if sponsor.get("commercial") else ("PHRC / DGOS" if PHRC.search(text) else "Académique (autre)")
    ped = bool(re.search(r"0-17|adolescent|child|infant|newborn|preterm|in utero", srch.get("ageGroup", ""), re.I))
    ph = srch.get("trialPhase", "")
    ph = ", ".join(sorted(set(re.findall(r"Phase [IV]+", ph)))) or ph
    pep = re.sub(r"\s+", " ", srch.get("primaryEndPoint") or "").strip()
    return {"id": ct, "nct": nct[0] if nct else "", "eu": [ct], "ac": acro, "t": title, "st": st, "cat": "Interventionnel",
            "fund": fund, "th": th, "pa": pa, "ph": ph, "sp": sponsor.get("name", srch.get("sponsor", "")), "ped": ped,
            "n": int(srch["totalNumberEnrolled"]) if str(srch.get("totalNumberEnrolled", "")).isdigit() else None,
            "start": "", "sum": ("Critère principal : " + pep[:380] + ("…" if len(pep) > 380 else "")) if pep else "",
            "cc": [], "ce": sites, "src": "CTIS"}

by_nct = {d["id"]: d for d in data}
by_eu = {e: d for d in data for e in d.get("eu", [])}
for d in data: d["src"] = "CT.gov"
added = merged = 0
for ct, det in details.items():
    rec = ctis_record(ct, det, search.get(ct, {}))
    if not rec["ce"] or onco_study(rec["t"], search.get(ct, {}).get("ctTitle", ""), search.get(ct, {}).get("conditions", "")): continue
    twin = by_eu.get(ct) or by_nct.get(rec["nct"])
    if twin:
        merged += 1
        twin["src"] = "CT.gov + CTIS"
        twin["eu"] = [ct]
        has = lambda sites: sum(1 for s in sites if any(x.get("e") or x.get("t") for x in s["k"]))
        if has(rec["ce"]) > has(twin["ce"]):
            twin["ce"] = rec["ce"]
        if not twin["ac"] and rec["ac"]: twin["ac"] = rec["ac"]
        if twin["st"] == "À confirmer" and rec["st"] != "À confirmer":  # CTIS, tenu à jour, tranche
            twin["st"], twin["upd"] = rec["st"], ""
    else:
        added += 1
        data.append(rec)
json.dump(data, open(sys.argv[4], "w"), ensure_ascii=False, separators=(",", ":"))
print(f"CTIS : {len(details)} fiches, {merged} déjà présentes (fusionnées), {added} ajoutées -> {len(data)} études")
import collections
new = [d for d in data if d["src"] == "CTIS"]
print("nouvelles par statut", collections.Counter(d["st"] for d in new), "par financement", collections.Counter(d["fund"] for d in new))
for d in new[:8]: print(" ", d["id"], d["st"], d["ac"], "|", d["t"][:80], "|", d["th"])

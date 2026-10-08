import json, os, re, sys, collections
d = json.load(open(sys.argv[1]))
# fiches ClinicalTrials.gov des PHRC néphro retrouvés par acronyme (phrc_ctgov.py), si présentes
_extra = os.path.join(os.path.dirname(sys.argv[1]), "ctgov_phrc.json")
if os.path.exists(_extra):
    for _k, _v in json.load(open(_extra)).items(): d.setdefault(_k, _v)
sys.path.insert(0, __import__("os").path.dirname(__file__))
from rules import ONCO, NEPH, THEMES, theme, PHRC, KCE, txt, stale_ok
STAT_FR = {"RECRUITING":"Recrutement ouvert","NOT_YET_RECRUITING":"Pas encore ouvert","ENROLLING_BY_INVITATION":"Sur invitation","ACTIVE_NOT_RECRUITING":"Actif, recrutement clos","UNKNOWN":"À confirmer"}
rows = []; dropped = []
for nct, s in d.items():
    p = s["protocolSection"]
    idm = p["identificationModule"]; sm = p["statusModule"]; dm = p["designModule"]
    if sm["overallStatus"] == "UNKNOWN" and not stale_ok(sm): continue
    cm = p.get("conditionsModule", {}); spm = p["sponsorCollaboratorsModule"]
    conds = cm.get("conditions", []); kws = cm.get("keywords", [])
    title = idm.get("briefTitle", ""); otitle = idm.get("officialTitle", "")
    ctext = txt(*conds, *kws)
    # relevance: nephro term in conditions/keywords/title after removing oncology phrases
    clean = ONCO.sub(" ", txt(ctext, title))
    onco_only = bool(ONCO.search(ctext)) and not NEPH.search(ONCO.sub(" ", ctext))
    if not NEPH.search(clean) or onco_only:
        dropped.append((nct, title, conds[:3])); continue
    if re.search(r"liver transplant|heart transplant|lung transplant", ctext, re.I) and not re.search(r"kidney|renal", txt(ctext,title), re.I):
        dropped.append((nct, title, conds[:3])); continue
    lead = spm["leadSponsor"]; collabs = [c["name"] for c in spm.get("collaborators", [])]
    ids = [p["identificationModule"].get("orgStudyIdInfo", {}).get("id", "")]
    for x in idm.get("secondaryIdInfos", []): ids += [x.get("id",""), x.get("domain",""), x.get("type","")]
    fund_text = txt(*ids, *collabs, lead.get("name"))
    locs = p.get("contactsLocationsModule", {}).get("locations", [])
    fr = [l for l in locs if l.get("country") in ("France", "Belgium")]
    centres = [{"f": l.get("facility",""), "c": l.get("city",""), "p": "FR" if l.get("country")=="France" else "BE", "s": l.get("status","")} for l in fr]
    countries = sorted({c["p"] for c in centres})
    if lead.get("class") == "INDUSTRY": fund = "Industriel"
    elif PHRC.search(fund_text): fund = "PHRC / DGOS"
    elif KCE.search(fund_text): fund = "KCE (Belgique)"
    else: fund = "Académique (autre)"
    styp = dm.get("studyType")
    bio = dm.get("bioSpec", {})
    if styp == "INTERVENTIONAL": cat = "Interventionnel"
    elif bio.get("retention") in ("SAMPLES_WITH_DNA","SAMPLES_WITHOUT_DNA") or re.search(r"biobank|biocollection|biobanque|biological collection", txt(title, otitle, *kws), re.I): cat = "Cohorte avec biobanque"
    else: cat = "Observationnel / cohorte"
    phases = dm.get("phases", [])
    ages = p.get("eligibilityModule", {})
    stdages = ages.get("stdAges", [])
    rows.append({
        "id": nct, "t": title, "ac": idm.get("acronym",""), "st": STAT_FR.get(sm["overallStatus"], sm["overallStatus"]),
        "cat": cat, "fund": fund, "th": theme(txt(ctext, title, otitle)),
        "ph": ", ".join(x.replace("PHASE","Phase ").replace("EARLY_","Précoce ") for x in phases if x != "NA"),
        "sp": lead.get("name",""), "cond": conds[:6], "ped": "CHILD" in stdages,
        "n": dm.get("enrollmentInfo", {}).get("count"), "start": sm.get("startDateStruct", {}).get("date",""),
        "pc": countries, "ce": centres,
        "upd": sm.get("lastUpdatePostDateStruct", {}).get("date",""),
    })
rows.sort(key=lambda r: (r["st"] != "Recrutement ouvert", r["t"]))
json.dump(rows, open(sys.argv[2], "w"), ensure_ascii=False, separators=(",",":"))
C = collections.Counter
print("kept", len(rows), "dropped", len(dropped))
for k in ("st","cat","fund"): print(k, C(r[k] for r in rows).most_common())
print("th", C(t for r in rows for t in r["th"]).most_common())
print("pays", C("+".join(r["pc"]) for r in rows).most_common(), "ped", sum(r["ped"] for r in rows))
import random; random.seed(1)
print("--- dropped"); [print(x) for x in dropped if not ONCO.search(" ".join(x[2])+x[1])]
print("--- PHRC"); [print(r["id"], r["sp"], r["t"][:80]) for r in rows if r["fund"]=="PHRC / DGOS"][:5]

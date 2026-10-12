"""Pages « essais cliniques » publiées par les centres -> sources locales (data/local/<site>.json, format décrit dans local_merge.py).
Sites : Cliniques universitaires Saint-Luc (Bruxelles), UZ Leuven (néphrologie), CHU de Saint-Étienne.
Le NCT est repris de la page quand il y figure, sinon cherché sur ClinicalTrials.gov (n° de protocole, puis acronyme) ;
les correspondances trouvées sont gardées en cache (data/raw/sites_nct.json).
Usage : python3 sites.py data/local [saintluc uzleuven stetienne]
Un site indisponible est signalé et son dernier fichier conservé.
"""
import html, json, os, re, sys, unicodedata, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from rules import theme, PATHO

OUT = sys.argv[1]
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"}
CACHE_F = os.path.join("data", "raw", "sites_nct.json")
cache = json.load(open(CACHE_F)) if os.path.exists(CACHE_F) else {}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8", "ignore")

def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

def text(page):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S)
    s = re.sub(r"<br\s*/?>|</(p|li|h\d|tr|div|td)>", "\n", s)
    return re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t]+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))))

def person(raw):
    """« DEMOULIN Nathalie » / « MAILLARD, Nicolas » -> « Nathalie Demoulin »"""
    raw = clean(raw).strip(" ,")
    if "," in raw:
        last, first = [x.strip() for x in raw.split(",", 1)]
    else:
        w = raw.split()
        up = [x for x in w if x.isupper() and len(x) > 1]
        last, first = " ".join(up), " ".join(x for x in w if x not in up)
    cap = lambda x: "-".join(p.capitalize() for p in x.split("-"))
    return " ".join(x for x in [first, " ".join(cap(p) for p in last.split())] if x).strip()

def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())

def ctgov(params):
    q = urllib.parse.urlencode(dict(params, fields="NCTId,Acronym,BriefTitle,OrgStudyId,SecondaryId,LeadSponsorName,CollaboratorName,OverallStatus", pageSize=10))
    try:
        return json.load(urllib.request.urlopen(f"https://clinicaltrials.gov/api/v2/studies?{q}", timeout=60)).get("studies", [])
    except Exception:
        return None

ACTIVE = "RECRUITING,NOT_YET_RECRUITING,ENROLLING_BY_INVITATION,ACTIVE_NOT_RECRUITING,UNKNOWN"
def ascii(s): return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
def same_sponsor(sp, s):
    w = [x[:6] for x in re.findall(r"[a-z]{4,}", ascii(sp)) if x not in ("univer", "medica", "center", "centre", "hospit", "pharma", "therap", "limite", "catholique"[:6])]
    m = s["protocolSection"].get("sponsorCollaboratorsModule", {})
    names = ascii(" ".join([m.get("leadSponsor", {}).get("name", "")] + [c.get("name", "") for c in m.get("collaborators", [])]))
    return not w or any(x in names for x in w)

def find_nct(protocol, acronym, country, city, sponsor=""):
    """NCT d'après le n° de protocole du promoteur (avec puis sans filtre de pays), puis l'acronyme parmi les études actives
    du même promoteur (une seule étude correspondante exigée)."""
    key = f"{protocol}|{acronym}|{country}|{sponsor}"
    if key in cache: return cache[key]
    nct, failed = "", False
    if protocol and len(protocol) >= 5:
        # sans filtre de pays seulement pour un vrai code de protocole (avec chiffres), pas pour un acronyme
        for params in ({"query.id": protocol, "query.locn": country},) + (({"query.id": protocol},) if re.search(r"\d", protocol) else ()):
            r = ctgov(params)
            if r is None: failed = True; break
            hits = [s["protocolSection"]["identificationModule"] for s in r]
            hits = [h for h in hits if norm(protocol) in [norm(h.get("orgStudyIdInfo", {}).get("id", ""))] +
                    [norm(x.get("id", "")) for x in h.get("secondaryIdInfos", [])]]
            if len({h["nctId"] for h in hits}) == 1: nct = hits[0]["nctId"]; break
    if not nct and acronym and len(norm(acronym)) >= 4:
        for loc in (city, country):
            r = ctgov({"query.titles": acronym, "query.locn": loc, "filter.overallStatus": ACTIVE})
            if r is None: failed = True; break
            hits = [s["protocolSection"]["identificationModule"] for s in r
                    if norm(s["protocolSection"]["identificationModule"].get("acronym", "")) == norm(acronym) and same_sponsor(sponsor, s)]
            if len({h["nctId"] for h in hits}) == 1: nct = hits[0]["nctId"]; break
    if not failed: cache[key] = nct
    return nct

FR = [(r"lupi", "Glomérulopathies / néphropathies immunes", "Néphropathie lupique"),
      (r"\bIgA", "Glomérulopathies / néphropathies immunes", "Néphropathie à IgA"),
      (r"dépôts de C3|\bC3G\b|glomérulopathie à C3", "Glomérulopathies / néphropathies immunes", "Glomérulopathie à C3"),
      (r"extra-?membraneuse|membraneuse|membranous", "Glomérulopathies / néphropathies immunes", "Glomérulonéphrite extramembraneuse"),
      (r"segmentaire et focale|\bHSF\b|néphrotique", "Glomérulopathies / néphropathies immunes", "HSF / syndrome néphrotique"),
      (r"\bANCA\b|vascularite", "Glomérulopathies / néphropathies immunes", "Vascularites à ANCA"),
      (r"hémolytique et urémique|\bSHU\b|microangiopathie", "Glomérulopathies / néphropathies immunes", "MAT / SHU"),
      (r"glomérul|néphrite", "Glomérulopathies / néphropathies immunes", None),
      (r"polykystose|polykysti|kystiques? du rein", "Maladies rénales rares / génétiques", "Polykystose (PKD)"),
      (r"alport|collag[eè]ne IV", "Maladies rénales rares / génétiques", "Syndrome d'Alport"),
      (r"APOL1", "Maladies rénales rares / génétiques", None),
      (r"greffe|transplant|receveur", "Transplantation", None),
      (r"cytomégalovirus|\bCMV\b|\bBK\b", "Transplantation", "Infections post-greffe"),
      (r"tacrolimus|immunosuppress", "Transplantation", "Immunosuppression / tolérance"),
      (r"dialys", "Dialyse / suppléance", None),
      (r"hémodialyse", "Dialyse / suppléance", "Hémodialyse / HDF"),
      (r"dialyse péritonéale", "Dialyse / suppléance", "Dialyse péritonéale"),
      (r"maladie rénale chronique|\bIRC\b|\bMRC\b|insuffisance rénale chronique", "MRC / néphroprotection / cardio-rénal", "Progression de la MRC"),
      (r"hypertension|cardiovasculaire", "MRC / néphroprotection / cardio-rénal", "HTA / cardio-rénal"),
      (r"diabét", "MRC / néphroprotection / cardio-rénal", "Maladie rénale diabétique"),
      (r"insuffisance rénale aiguë|agression rénale aiguë", "Insuffisance rénale aiguë", None),
      (r"lithiase|calcul", "Lithiase / infections urinaires", "Lithiase")]

def classify(txt, extra=None):
    th, pa = set(extra[0:1]) if extra else set(), {extra[1]} if extra and extra[1] else set()
    for pat, t, p in FR:
        if re.search(pat, txt, re.I):
            th.add(t)
            if p: pa.add(p)
    t2 = theme(txt)
    if t2 != ["Autre néphrologie"]: th |= set(t2)
    pa |= {p for t, p, pat in PATHO if t in th and re.search(pat, txt, re.I)}
    return sorted(th) or ["Autre néphrologie"], sorted(pa)

# un service de néphrologie participe parfois à des études sans lien avec le rein (ex. cardiovasculaire) : écartées
RENAL = re.compile(r"\brein|rénal|renal|kidney|néphr|nephr|dialys|glomérul|\bIgA|greff|transplant|polykyst|ADPKD|APOL1|C3G|lupi|protéinur|albuminur|"
                   r"hypertension|\bHTA\b|cytomégalovirus|urémi|collag", re.I)

def obs(txt):
    return bool(re.search(r"cohort|registr|registre|observation|non[- ]interventionnel|biobanque|biobank|banque de|prédicteurs|microbiote|"
                          r"prevalen|prévalence|systems serology|n/a\b|genotype|phenotype|génotyp|phénotyp", txt, re.I))

# ---------------- Cliniques universitaires Saint-Luc ----------------
def saintluc():
    base = "https://saintluc.be/fr/clinical-study"
    projects = []
    for sv, label in [("8303", "Néphrologie"), ("8344", "Transplantation abdominale")]:
        for page in range(10):
            url = f"{base}?field_cs_service={sv}&page={page}"
            t = re.sub(r"\s*\n\s*", "\n", text(get(url)))
            blocks = t.split("N° protocole\n")[1:]
            if not blocks: break
            for b in blocks:
                b = b.split("N° comité d’éthique")[0]
                lines = [l.strip() for l in b.split("\n") if l.strip()]
                prot = lines[0]
                rest = [l for l in lines[1:] if l not in ("CTR", "MDR", "(", ")")]
                f = {}
                for key in ["Phase", "Investigateur", "Service", "Coordinateur de recherche", "Pathologie", "Promoteur"]:
                    if key in rest:
                        i = rest.index(key); v = rest[i + 1] if i + 1 < len(rest) else ""
                        f[key] = "" if v in ("Phase", "Investigateur", "Service", "Coordinateur de recherche", "Pathologie", "Promoteur") else v
                head = rest[:rest.index("Phase")] if "Phase" in rest else rest[:1]
                m = re.search(r"\(\s*\n?([^()]{2,40})\n?\s*\)", b)
                ac = clean(m.group(1)) if m else ""
                title = " ".join(x for x in head if x != ac)
                if not RENAL.search(title + " " + f.get("Pathologie", "") + " " + ac): continue
                if not ac or ac in ("C3G", "ADPKD", "IgAN", "CKD"): ac = prot if not re.match(r"^(\d{1,2}|VERSION \d+)$", prot) else (ac or title[:40])
                k = [{"n": person(f["Investigateur"]), "r": "Investigateur principal"}] if f.get("Investigateur") else []
                if f.get("Coordinateur de recherche"): k.append({"n": person(f["Coordinateur de recherche"]), "r": "Coordinateur de recherche"})
                txt = " ".join([title, f.get("Pathologie", "")])
                th, pa = classify(txt)
                sp = f.get("Promoteur", "").title() if f.get("Promoteur", "").isupper() else f.get("Promoteur", "")
                projects.append({"ac": ac, "long": title, "sp": sp,
                                 "proto": prot, "nct": find_nct(prot if not re.match(r"^(\d{1,2}|VERSION \d+)$", prot) else "", ac, "Belgium", "Brussels", sp),
                                 "url": f"{base}?field_cs_service={sv}", "th": th, "pa": pa, "k": k,
                                 "obs": f.get("Phase", "") in ("n/a", "") and obs(txt + " " + title)})
    return {"source": "Cliniques universitaires Saint-Luc — études cliniques en cours", "source_url": base + "?field_cs_service=8303",
            "centre": {"f": "Cliniques universitaires Saint-Luc — Néphrologie", "v": "Bruxelles", "p": "BE", "z": "1200",
                       "match": r"saint[- ]?luc|st[- ]?luc|\bucl\b|uclouvain", "k": []},
            "projects": projects}

# ---------------- UZ Leuven, néphrologie ----------------
def uzleuven():
    base = "https://www.uzleuven.be/nl/nefrologie/klinische-studies"
    cats = {"adpkd": ("Maladies rénales rares / génétiques", "Polykystose (PKD)"), "chronische-nierziekten": ("MRC / néphroprotection / cardio-rénal", None),
            "iga": ("Glomérulopathies / néphropathies immunes", "Néphropathie à IgA"), "nierdialyse": ("Dialyse / suppléance", None),
            "niertransplantatie": ("Transplantation", None), "andere-pathologie": (None, None)}
    seen = {}
    for cat, extra in cats.items():
        page = get(f"{base}/{cat}")
        content = page[page.find('class="l-content'):]
        for m in re.finditer(r"<h2[^>]*?(?:id=\"([^\"]*)\")?[^>]*>(.*?)</h2>(.*?)(?=<h2|$)", content, re.S):
            anchor, head, body = m.group(1) or "", clean(m.group(2)), m.group(3)
            if not re.search(r"\bstudie\b", head, re.I): continue
            parts = re.split(r"\s+[–-]\s+", head, maxsplit=1)
            ac = re.sub(r"\s*\bstudie\b\s*", " ", parts[0], flags=re.I).strip()
            sp = parts[1].strip() if len(parts) > 1 else ""
            paras = [clean(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S)]
            paras = [p for p in paras if p]
            long = paras[0] if paras else ""
            if ac in seen:
                r = seen[ac]
                if extra[0] and extra[0] not in r["th"]: r["th"] = sorted(set(r["th"]) | {extra[0]})
                continue
            th, pa = classify(" ".join([ac, long] + paras[:3]), extra if extra[0] else None)
            nct = (re.findall(r"NCT\d{8}", body) or [""])[0] or find_nct("", ac, "Belgium", "Leuven", sp)
            seen[ac] = {"ac": ac, "long": long, "sp": sp, "nct": nct, "url": f"{base}/{cat}" + (f"#{anchor}" if anchor else ""),
                        "th": th, "pa": pa, "obs": obs(long)}
    return {"source": "UZ Leuven — klinische studies nefrologie", "source_url": base,
            "centre": {"f": "UZ Leuven — Nefrologie", "v": "Louvain", "p": "BE", "z": "3000", "match": r"leuven|louvain|gasthuisberg",
                       "k": [{"n": "Studiecoördinatoren nefrologie", "r": "CONTACT", "e": "RDNefro@uzleuven.be", "t": "+32 16 34 56 75"}]},
            "projects": list(seen.values())}

# ---------------- CHU de Saint-Étienne ----------------
def stetienne():
    url = "https://www.chu-st-etienne.fr/rechercheclinique/essaisCliniques/accueil"
    page = get(url)
    projects = []
    for m in re.finditer(r"<div id=DivEssai\d+.*?(?=<div id=DivEssai\d+|\Z)", page, re.S):
        b = m.group(0)
        g = lambda pat: clean((re.search(pat, b, re.S) or [None, ""])[1])
        dom, onco = g(r"Famille / Domaine : <b>(.*?)</b>"), g(r"Cancérologie :\s*<span><b>(.*?)</b>")
        title = g(r"fa-clipboard[^>]*></i>(.*?)</div>")
        inv_m = re.search(r"Investigateur : <b>(.*?)</b>\s*-?\s*([^<]*)", b)
        service = clean(inv_m.group(2)) if inv_m else ""
        organe = g(r"Organe / Pathologie : <b>(.*?)</b>")
        if not (dom == "Néphrologie" or "Néphrologie" in service) or not RENAL.search(title + " " + organe): continue
        ac = g(r"Essai : <b>(.*?)</b>")
        k = []
        if inv_m and person(inv_m.group(1)): k.append({"n": person(inv_m.group(1)), "r": "Investigateur principal"})
        cm = re.search(r"Contact de l'étude : (?:<a href='mailto:([^']*)'[^>]*>)?(.*?)<", b)
        if cm and clean(cm.group(2)) and person(cm.group(2)) not in [x["n"] for x in k]: k.append({k2: v for k2, v in {"n": person(cm.group(2)), "r": "Contact de l'étude", "e": (cm.group(1) or "").strip()}.items() if v})
        typ = g(r"Type d'essai : <b>(.*?)</b>")
        txt = " ".join([title, organe])
        th, pa = classify(txt)
        sp = g(r"Organisme Promoteur : <b>(.*?)</b>")
        nct = (re.findall(r"NCT\d{8}", b) or [""])[0] or find_nct(ac.split()[-1] if " " in ac else ac, ac.split()[0], "France", "Saint-Etienne", sp)
        projects.append({"ac": ac, "long": title, "sp": sp, "nct": nct,
                         "url": url, "th": th, "pa": pa, "k": k, "type": typ,
                         "obs": bool(re.search(r"observ|cohorte|registre|RIPH ?3|non interventionnel", typ + " " + title, re.I))})
    return {"source": "CHU de Saint-Étienne — essais cliniques", "source_url": url,
            "centre": {"f": "CHU de Saint-Étienne — Néphrologie", "v": "Saint-Étienne", "p": "FR", "z": "42055",
                       "match": r"[eé]tienne|bellevue|chuse|priest", "k": []},
            "projects": projects}

SITES = {"saintluc": saintluc, "uzleuven": uzleuven, "stetienne": stetienne}
known = {}
for name in (sys.argv[2:] or SITES):
    try:
        src = SITES[name]()
        if not src["projects"]: raise ValueError("aucune étude lue (page modifiée ?)")
    except Exception as e:
        print(f"::warning::{name} : {e} — dernière version conservée"); continue
    for p in src["projects"]:
        if p["nct"]: known.setdefault(norm(p["ac"]), p["nct"])
        elif len(norm(p["ac"])) >= 4 and norm(p["ac"]) in known: p["nct"] = known[norm(p["ac"])]
    json.dump(src, open(os.path.join(OUT, f"{name}.json"), "w"), ensure_ascii=False, indent=1)
    n = len(src["projects"]); w = sum(1 for p in src["projects"] if p["nct"])
    print(f"{name} : {n} études, {w} avec NCT")
os.makedirs(os.path.dirname(CACHE_F), exist_ok=True)
json.dump(cache, open(CACHE_F, "w"), ensure_ascii=False, indent=0)

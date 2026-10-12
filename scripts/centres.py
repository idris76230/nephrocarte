"""Regroupe les libellés de centres (un même hôpital apparaît sous des dizaines de noms) en établissements canoniques,
nettoie les villes (« Toulouse Cedex 9 » -> Toulouse) et range les PHRC dans le financement académique.
Ajoute à chaque centre : e (établissement canonique). Usage : python3 centres.py app/data.json app/data.json
"""
import json, re, sys, unicodedata, collections

data = json.load(open(sys.argv[1]))
def k(s): return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()

# hôpitaux nommés (sites d'un même CHU qu'il est utile de distinguer pour adresser un patient)
NAMED = [
    ("Paris & IDF", [("necker", "Hôpital Necker-Enfants malades (AP-HP)"), ("pitie|salpetriere", "Hôpital Pitié-Salpêtrière (AP-HP)"),
                     ("tenon", "Hôpital Tenon (AP-HP)"), ("saint[- ]louis", "Hôpital Saint-Louis (AP-HP)"), ("bichat", "Hôpital Bichat (AP-HP)"),
                     ("pompidou|hegp", "Hôpital européen Georges-Pompidou (AP-HP)"), ("cochin", "Hôpital Cochin (AP-HP)"),
                     ("lariboisiere", "Hôpital Lariboisière (AP-HP)"), ("saint[- ]antoine", "Hôpital Saint-Antoine (AP-HP)"),
                     ("robert[- ]debre", "Hôpital Robert-Debré (AP-HP)"), ("trousseau", "Hôpital Trousseau (AP-HP)"),
                     ("bicetre|kremlin", "Hôpital Bicêtre (AP-HP)"), ("mondor", "Hôpital Henri-Mondor (AP-HP)"),
                     ("avicenne", "Hôpital Avicenne (AP-HP)"), ("ambroise", "Hôpital Ambroise-Paré (AP-HP)"),
                     ("poincare", "Hôpital Raymond-Poincaré (AP-HP)"), ("beaujon", "Hôpital Beaujon (AP-HP)"),
                     ("louis[- ]mourier", "Hôpital Louis-Mourier (AP-HP)"), ("jean[- ]verdier", "Hôpital Jean-Verdier (AP-HP)"),
                     ("hotel[- ]dieu", "Hôtel-Dieu (AP-HP)"), ("foch", "Hôpital Foch (Suresnes)"), ("saint[- ]joseph", "Groupe hospitalier Paris Saint-Joseph"),
                     ("diaconesses", "Hôpital des Diaconesses"), ("begin", "Hôpital d'instruction des armées Bégin"),
                     ("curie", "Institut Curie"), ("gustave roussy", "Gustave-Roussy"), ("aura", "AURA Paris (dialyse)"),
                     ("versailles|mignot|le chesnay", "CH de Versailles (Le Chesnay)"), ("sud[- ]francilien|corbeil", "CH Sud-Francilien"),
                     ("delafontaine|saint[- ]denis", "CH Delafontaine (Saint-Denis)"), ("pontoise|dubos", "CH René-Dubos (Pontoise)"),
                     ("argenteuil", "CH d'Argenteuil"), ("poissy", "CH de Poissy"), ("montreuil|andre gregoire", "CH André-Grégoire (Montreuil)")]),
    ("Lyon", [("herriot", "Hôpital Édouard-Herriot (HCL)"), ("lyon[- ]sud|pierre[- ]benite", "Centre hospitalier Lyon-Sud (HCL)"),
              ("femme mere enfant|hfme|bron", "Hôpital Femme-Mère-Enfant / GH Est (HCL)"), ("croix[- ]rousse", "Hôpital de la Croix-Rousse (HCL)"),
              ("louis pradel|cardio", "Hôpital Louis-Pradel (HCL)")]),
    ("Marseille", [("conception", "Hôpital de la Conception (AP-HM)"), ("timone", "Hôpital de la Timone (AP-HM)"), ("nord", "Hôpital Nord (AP-HM)")]),
    ("Bordeaux", [("pellegrin", "Hôpital Pellegrin (CHU de Bordeaux)"), ("haut[- ]leveque", "Hôpital Haut-Lévêque (CHU de Bordeaux)")]),
    ("Toulouse", [("rangueil", "Hôpital Rangueil (CHU de Toulouse)"), ("purpan", "Hôpital Purpan (CHU de Toulouse)")]),
    ("Bruxelles", [("erasme|hub", "Hôpital Erasme / HUB (Bruxelles)"), ("saint[- ]luc|st[- ]luc|ucl", "Cliniques universitaires Saint-Luc (Bruxelles)"),
                   ("brugmann", "CHU Brugmann (Bruxelles)"), ("uz brussel|vub", "UZ Brussel"), ("delta|chirec", "CHIREC (Bruxelles)")]),
]
UNIV = r"\bchu\b|\bchru\b|\bchr\b|universit|hospices civils|\bhcl\b|ap[- ]?h[pm]\b|assistance publique|\buz\b|universitair|academisch|\bhus\b|hopitaux universitaires"
BE_UNIV = {"Louvain": "UZ Leuven", "Gand": "UZ Gent", "Anvers": "UZ Antwerpen", "Liège": "CHU de Liège", "Yvoir (CHU UCL Namur)": "CHU UCL Namur (Yvoir)"}

def clean_city(v):
    v = re.sub(r"\s+cedex(\s*\d+)?$", "", v.strip(), flags=re.I)
    v = re.sub(r"\s+\d+$", "", v)
    return v

# libellés anonymes des promoteurs industriels (« Research Site », « Novartis Investigative Site »...) : un site par ville
GENERIC = re.compile(r"^(\w+ )?(investigat\w*|research|clinical( trial| research)?|study|trial)( clinical)? (site|facility|center|centre)\b|"
                     r"^site\s*(be|fr)?\s*#?\s*\d+$|^investigational site number", re.I)

def canon(c):
    v = clean_city(c["v"])
    if v == "Paris & IDF" and str(c.get("z", "")).startswith("974"): v = "Saint-Denis (La Réunion)"  # Saint-Denis de La Réunion
    n = k(c["f"])
    if GENERIC.search(c["f"].strip()):
        return v, f"Site non nommé par le promoteur ({v}{', ' + c['z'] if c.get('z') else ''})"
    for city, items in NAMED:
        if city == v:
            for pat, name in items:
                if re.search(pat, n): return v, name
    if c["p"] == "BE" and v in BE_UNIV and re.search(UNIV + r"|gasthuisberg|sart tilman|hospital|hopital|ziekenhuis", n):
        return v, BE_UNIV[v]
    if re.search(UNIV, n):
        if v == "Paris & IDF": return v, "AP-HP (site non précisé)"
        if v == "Lyon": return v, "Hospices civils de Lyon (site non précisé)"
        if v == "Marseille": return v, "AP-HM (site non précisé)"
        return v, ("Hôpital universitaire de " if c["p"] == "BE" else "CHU de ") + v
    # autre établissement : partie avant le service, sans numéro de site
    base = re.split(r"\s+—\s+|\s+-\s+site\b|,", c["f"])[0].strip() or c["f"]
    base = re.sub(r"\s*(site\s*#?\s*\w+|#\s*\d+)$", "", base, flags=re.I).strip()
    return v, base[:1].upper() + base[1:] if base else f"Centre non nommé ({v})"

before = len({(c["f"], c["v"]) for d in data for c in d["ce"]})
for d in data:
    if d["fund"] == "PHRC / DGOS":
        d["fund"] = "Académique"
        d["phrc"] = d.get("phrc") or "PHRC"
    elif d["fund"] in ("Académique (autre)", "KCE (Belgique)"):
        d["fund"] = "Académique"
    for c in d["ce"]:
        c["v"], c["e"] = canon(c)

# « AP-HP (site non précisé) » (registre européen : « Assistance Publique Hôpitaux de Paris — service ») : l'hôpital est retrouvé
# d'après les études où il est nommé — nom de l'investigateur, puis préfixe téléphonique, puis code postal du site.
GEN = "AP-HP (site non précisé)"
def person(n): return " ".join(sorted(re.findall(r"[a-z]{2,}", k(re.sub(r"\b(dr|pr|prof|md|phd|mme|mr|m)\b\.?", " ", n or "", flags=re.I)))))
def prefix(t):
    t = re.sub(r"\D", "", t or "")
    t = re.sub(r"^(00)?33(0)?", "0", t)
    if len(t) == 9 and t[0] in "1234567": t = "0" + t
    return t[:6] if len(t) == 10 and t.startswith("01") else ""
learn = {"n": collections.defaultdict(collections.Counter), "t": collections.defaultdict(collections.Counter), "z": collections.defaultdict(collections.Counter)}
for d in data:
    for c in d["ce"]:
        if c["e"].endswith("(AP-HP)"):
            for x in c["k"]:
                if person(x.get("n")): learn["n"][person(x.get("n"))][c["e"]] += 1
                if prefix(x.get("t")): learn["t"][prefix(x.get("t"))][c["e"]] += 1
            if c.get("z"): learn["z"][str(c["z"])][c["e"]] += 1
def vote(kind, key, nmin):
    cnt = learn[kind].get(key)
    if not cnt: return None
    h, n = cnt.most_common(1)[0]
    return h if n >= nmin and n / sum(cnt.values()) >= 0.8 else None
import os
ann = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data", "aphp_annuaire.json")))
ANN_N = {person(n): h for n, h in ann.get("personnes", {}).items()}
ANN_T = ann.get("telephones", {})
def where(x):
    return ANN_N.get(person(x.get("n"))) or vote("n", person(x.get("n")), 1) or ANN_T.get(prefix(x.get("t"))) or vote("t", prefix(x.get("t")), 2)
resolved = 0
for d in data:
    out = []
    for c in d["ce"]:
        if c["e"] != GEN: out.append(c); continue
        groups = collections.defaultdict(list)
        for x in c["k"]: groups[where(x)].append(x)
        hosp = [h for h in groups if h]
        if not hosp:
            h = vote("z", str(c.get("z", "")), 3)
            if h: hosp, groups = [h], {h: c["k"]}
        if not hosp: out.append(c); continue
        if len(hosp) == 1 and groups.get(None): groups[hosp[0]] += groups.pop(None)  # contacts non reconnus : même site
        for h in hosp:
            out.append(dict(c, e=h, k=groups[h], devine=1)); resolved += 1
        if groups.get(None): out.append(dict(c, k=groups[None]))
    d["ce"] = out
print(f"AP-HP sans site précisé : {resolved} sites rattachés à un hôpital", end=" ; ")

for d in data:
    seen = {}
    for c in d["ce"]:
        # un établissement apparaît une seule fois par étude (plusieurs services -> on garde le meilleur statut / contacts)
        prev = seen.get(c["e"])
        if prev is None: seen[c["e"]] = c
        else:
            order = ["Ouvert", "Sur invitation", "À venir", "À confirmer", "Non précisé", "Fermé", "Suspendu"]
            rank = lambda x: order.index(x) if x in order else len(order)
            if rank(c["s"]) < rank(prev["s"]): prev["s"] = c["s"]
            prev["k"] += [x for x in c["k"] if x not in prev["k"]]
            if c["f"] not in prev["f"]: prev.setdefault("svc", []).append(c["f"])
    d["ce"] = list(seen.values())
after = len({c["e"] for d in data for c in d["ce"]})
json.dump(data, open(sys.argv[2], "w"), ensure_ascii=False, separators=(",", ":"))
print(f"libellés de centres : {before} -> établissements : {after}")
print(collections.Counter(c["e"] for d in data for c in d["ce"]).most_common(12))
print(collections.Counter(d["fund"] for d in data), sum(1 for d in data if d.get("phrc")), "PHRC")

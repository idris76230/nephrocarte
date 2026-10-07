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

def canon(c):
    v = clean_city(c["v"])
    n = k(c["f"])
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
    seen = {}
    for c in d["ce"]:
        c["v"], c["e"] = canon(c)
        # un établissement apparaît une seule fois par étude (plusieurs services -> on garde le meilleur statut / contacts)
        prev = seen.get(c["e"])
        if prev is None: seen[c["e"]] = c
        else:
            order = ["Ouvert", "Sur invitation", "À venir", "Non précisé", "Fermé", "Suspendu"]
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

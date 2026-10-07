"""Transforme les fiches projet du CRMR / URC néphrologie de Brest en « source locale » (data/local/brest.json).
Format commun aux sources locales : voir local_merge.py.
"""
import json, re, sys

pages = json.load(open(sys.argv[1]))
BASE = "https://nephrogenetique.chu-brest.fr"
FIELDS = {"Promoteur": "sp", "Présentation": "pres", "Population concernée": "pop", "Objectif principal": "obj",
          "Appel à projet / financement": "fin", "Avis comité d’éthique": "eth", "Enregistrement ClinicalTrial": "reg",
          "Pour plus d’informations": "reg"}
# thématique / pathologie d'après la rubrique du site, puis d'après le texte (en français)
SECTION = {"polykystose": ("Maladies rénales rares / génétiques", "Polykystose (PKD)"),
           "syndrome-dalport": ("Maladies rénales rares / génétiques", "Syndrome d'Alport"),
           "vascularites-a-anca": ("Glomérulopathies / néphropathies immunes", "Vascularites à ANCA"),
           "greffe-renale": ("Transplantation", None),
           "hors-maladies-rares": ("MRC / néphroprotection / cardio-rénal", None)}
FR_PATHO = [(r"lupi", "Glomérulopathies / néphropathies immunes", "Néphropathie lupique"),
            (r"\bIgA", "Glomérulopathies / néphropathies immunes", "Néphropathie à IgA"),
            (r"dépôts de C3|GC3|C3G", "Glomérulopathies / néphropathies immunes", "Glomérulopathie à C3"),
            (r"extra-?membraneuse|GEM\b", "Glomérulopathies / néphropathies immunes", "Glomérulonéphrite extramembraneuse"),
            (r"segmentaire et focale|GSF|HSF", "Glomérulopathies / néphropathies immunes", "HSF / syndrome néphrotique"),
            (r"hémolytique et urémique|SHU", "Glomérulopathies / néphropathies immunes", "MAT / SHU"),
            (r"hyperoxalurie", "Maladies rénales rares / génétiques", "Hyperoxalurie"),
            (r"polykystose", "Maladies rénales rares / génétiques", "Polykystose (PKD)"),
            (r"sclérose tubéreuse|angiomyolipome", "Maladies rénales rares / génétiques", None),
            (r"maladies? rénales? rares?", "Maladies rénales rares / génétiques", None),
            (r"rejet|\bDSA\b|greffe rénale|transplantation rénale|transplantés rénaux", "Transplantation", None),
            (r"hypertension|cardiovasculaire", "MRC / néphroprotection / cardio-rénal", "HTA / cardio-rénal"),
            (r"maladie rénale chronique|MRC|néphropathies? d.origine indéterminée", "MRC / néphroprotection / cardio-rénal", "Progression de la MRC")]
out = []
for path, v in pages.items():
    if v["children"]: continue
    lines = [l.strip() for l in v["text"].split("\n") if l.strip()]
    # le texte suit le motif « Libellé : valeur » ; le titre de la fiche est la première ligne
    head = lines[0]
    m = re.match(r"^(.*?)\s*\(([A-Z][A-Z0-9\-]{2,15})\)\s*$", head) or None
    if m: rec = {"ac": m.group(2), "long": m.group(1)}
    elif " : " in head: rec = {"ac": head.split(" : ")[0], "long": head.split(" : ", 1)[1]}
    else: rec = {"ac": head}
    body = " \n".join(lines[1:])
    keys = "|".join(re.escape(k) for k in FIELDS)
    for m in re.finditer(r"(" + keys + r")\s*:\s*(.*?)(?=\s*(?:" + keys + r")\s*:|\Z)", body, re.S):
        rec[FIELDS[m.group(1)]] = re.sub(r"\s+", " ", m.group(2)).strip(" /")
    ncts = re.findall(r"NCT\d{8}", " ".join([body] + v["links"]))
    rec["nct"] = ncts[0] if ncts else ""
    rec["url"] = BASE + path
    text = " ".join([rec.get("pres", ""), rec.get("pop", ""), rec.get("obj", "")])
    th, pa = set(), set()
    for key, (t, p) in SECTION.items():
        if key in path:
            th.add(t); pa.add(p) if p else None
    for pat, t, p in FR_PATHO:
        if re.search(pat, text):
            th.add(t); pa.add(p) if p else None
    rec["th"] = sorted(th) or ["Autre néphrologie"]
    rec["pa"] = sorted(x for x in pa if x)
    rec["obs"] = bool(re.search(r"registre|cohorte|observationnelle|non interventionnelle|rétro|base .*données|repérage", text + " " + rec["ac"], re.I))
    rec["intra"] = "promotion-interne" in path
    out.append(rec)
local = {"source": "CHU de Brest — URC de néphrologie / CRMR maladies rénales rares",
         "source_url": BASE + "/unite-de-recherche-clinique-de-nephrologie/les-projets-de-recherche-en-cours",
         "centre": {"f": "CHU de Brest — Néphrologie (URC de néphrologie)", "v": "Brest", "p": "FR", "z": "29200",
                    "k": [{"n": "Secrétariat de néphrologie", "r": "CONTACT", "t": "02 98 34 70 58"}]},
         "projects": out}
json.dump(local, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
print(len(out), "projets ;", sum(1 for r in out if r["nct"]), "avec NCT")
for r in out: print(f"  {r['ac'][:28]:28} {r['nct']:12} {r.get('fin','')[:30]:30} {r['th']} {r['pa']}")

"""Lit les fichiers Excel de résultats DGOS (PHRC-N, PHRC-I) et produit une table unifiée + le sous-ensemble néphro.
Usage : python phrc_parse.py data/phrc_lists data/phrc_all.json data/phrc_nephro.json   (nécessite openpyxl)
"""
import glob, json, os, re, sys, unicodedata
import openpyxl

def k(s): return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
COLS = {  # rôle -> motifs d'en-tête
    "num": r"n.? ?du projet|numero (du )?projet|numero de projet|reference lettre|phrcn-22",
    "etab": r"etablissement|nom de l.etablissement",
    "acro": r"acronyme",
    "titre": r"^titre",
    "nom": r"nom (du porteur|coordonnateur)|porteur de projet",
    "prenom": r"prenom",
    "girci": r"girci",
}
rows = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.xlsx"))):
    base = os.path.basename(f)
    if "mie" in base: continue  # appel « Recherche MIE », pas un PHRC
    typ = "PHRC-I" if re.search(r"phrc[-_]?i", base, re.I) else "PHRC-N"
    year = re.search(r"(20)?(1[6-9]|2[0-6])(?!\d)", re.sub(r"_\d{8}", "", base.replace("phrc-i2", "phrc-i_2")))
    wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    header = next(it)
    hk = [k(h).replace("\n", " ").strip() for h in header]
    idx = {}
    for role, pat in COLS.items():
        for i, h in enumerate(hk):
            if role in idx or not h: continue
            if role == "nom" and ("prenom" in h): continue
            if re.search(pat, h): idx[role] = i
    # 2 colonnes « Porteur de projet » (nom puis prénom) dans beaucoup de fichiers
    porteurs = [i for i, h in enumerate(hk) if h.startswith("porteur de projet")]
    if "prenom" not in idx and len(porteurs) >= 2: idx["nom"], idx["prenom"] = porteurs[0], porteurs[1]
    empty = 0
    for r in it:
        if not any(r):
            empty += 1
            if empty > 50: break
            continue
        empty = 0
        g = lambda role: str(r[idx[role]]).strip() if role in idx and idx[role] < len(r) and r[idx[role]] is not None else ""
        num = g("num")
        y = re.search(r"-(?:20)?(\d{2})-", num)
        rows.append({"type": typ, "annee": "20" + y.group(1) if y else ("20" + year.group(2) if year else ""),
                     "num": num, "etab": g("etab"), "porteur": " ".join(x for x in (g("prenom"), g("nom")) if x),
                     "acro": g("acro"), "titre": re.sub(r"\s+", " ", g("titre")), "fichier": base})
rows = [r for r in rows if r["titre"] or r["acro"]]
json.dump(rows, open(sys.argv[2], "w"), ensure_ascii=False, indent=0)

NEPHRO = re.compile(r"\brein|(?<!ad)r[ée]na(l|ux)|néphr|nephr|glomérul|glomerul|dialys|hémodiaf|hemodiaf|uremi|urémi|"
                    r"greffe rénale|transplant[ée]s? r[ée]na|transplantation r[ée]nale|greffon r[ée]nal|"
                    r"\bIgA\b|lupique|vascularites? (associées? )?aux ANCA|\bANCA\b|hémolytique et urémique|\bSHU\b|"
                    r"microangiopathie thrombotique|hyperkali|insuffisance rénale|maladie rénale|\bMRC\b|\bIRA\b|\bIRC\b|"
                    r"lithiase|polykystose|protéinurie|albuminurie|\bDFG\b|cystinose|hyperoxalurie|syndrome néphrotique|"
                    r"fistule artério|abord vasculaire", re.I)
NOT = re.compile(r"cancer|carcinome r[ée]nal|tumeurs? (du )?rein|néphrectomie partielle|surrénal", re.I)
neph = [r for r in rows if NEPHRO.search(r["titre"] + " " + r["acro"]) and not NOT.search(r["titre"])]
json.dump(neph, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
import collections
print(len(rows), "projets lus ;", len(neph), "néphro")
print(collections.Counter((r["type"], r["annee"]) for r in rows))
print(collections.Counter((r["type"], r["annee"]) for r in neph))

"""Corrections validées du formulaire du site (onglet « Publiées » du Google Sheet, publié en CSV) -> même format que data/corrections.json.
Usage : python3 sheet_corrections.py <url_csv> data/corrections_formulaire.json
Seules les lignes marquées « oui » dans la colonne « Validé » du Sheet sont publiées dans l'onglet (aucun nom ni e-mail de déclarant).
"""
import csv, io, json, re, sys, urllib.request

url, out = sys.argv[1], sys.argv[2]
raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "NephroCarte"}), timeout=60).read().decode("utf-8-sig")
rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(io.StringIO(raw))]
if rows and "Étude concernée" not in rows[0]: sys.exit("colonnes inattendues dans le Sheet : " + ", ".join(rows[0]))

STATUTS = {"ouvert": "Ouvert", "à venir": "À venir", "a venir": "À venir", "sur invitation": "Sur invitation", "fermé": "Fermé", "ferme": "Fermé"}
corr = []
for r in rows:
    if not r.get("Étude concernée") or not r.get("Établissement concerné"): continue
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", r.get("Horodateur", ""))
    contact = {k: r.get(c, "") for k, c in [("nom", "Contact – nom"), ("role", "Contact – fonction"), ("email", "Contact – e-mail"), ("tel", "Contact – téléphone")]}
    centre = {"etablissement": r["Établissement concerné"], "ville": r.get("Ville", "")}
    if STATUTS.get(r.get("Statut du centre", "").lower()): centre["statut"] = STATUTS[r["Statut du centre"].lower()]
    if any(contact.values()): centre["contacts"] = [{k: v for k, v in contact.items() if v}]
    # « HYPERSHU — NCT05726916 » (bouton d'une fiche) : on garde l'identifiant
    ref = r["Étude concernée"]; ids = re.findall(r"NCT\d{8}|\d{4}-\d{6}-\d{2}-\d{2}", ref)
    corr.append({"etude": ids[0] if ids else ref.split(" — ")[0].strip(), "date": f"{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}" if m else "",
                 "source": "Formulaire NéphroCarte", "centre": centre})
json.dump({"_aide": ["Généré automatiquement depuis le Google Sheet des signalements validés (scripts/sheet_corrections.py) : ne pas modifier à la main."],
           "corrections": corr}, open(out, "w"), ensure_ascii=False, indent=1)
print(f"formulaire : {len(corr)} correction(s) validée(s)")

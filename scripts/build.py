"""Assemble app/template.html + données + logo -> app/nephro-essais.html et site/index.html (page publiée)."""
import datetime, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = lambda f: open(os.path.join(root, "app", f), encoding="utf-8").read()
today = datetime.date.today()
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
html = (a("template.html").replace("__DATA__", a("data.json").replace("</", "<\\/"))
        .replace("__PMAP__", a("pmap.json")).replace("__LOGO__", a("logo.b64").strip())
        .replace("__DATE__", f"{today.day} {MOIS[today.month - 1]} {today.year}"))
# claude.ai ajoute lui-même l'enveloppe du document ; pour GitHub Pages on l'écrit (sinon mode « quirks » et [hidden] inopérant)
SHELL = ('<!doctype html><html lang="fr"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
         '<meta name="description" content="Les études cliniques en néphrologie, dialyse et transplantation en France et en Belgique.">'
         '<style>:root{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>'
         '</head><body>')
os.makedirs(os.path.join(root, "site"), exist_ok=True)
open(os.path.join(root, "app", "nephro-essais.html"), "w", encoding="utf-8").write(html)
open(os.path.join(root, "site", "index.html"), "w", encoding="utf-8").write(SHELL + html + "</body></html>")
open(os.path.join(root, "site", ".nojekyll"), "w").close()
print("ok", len(html))

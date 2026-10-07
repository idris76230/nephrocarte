# NéphroCarte

Les études cliniques en néphrologie, dialyse et transplantation ouvertes en France et en Belgique : essais académiques
(dont PHRC), essais industriels, cohortes et biobanques, avec les centres participants et le contact de l'investigateur.

Prototype préparé pour la commission clinique de la SFNDT.

## Sources

| Source | Contenu | Mise à jour |
|---|---|---|
| ClinicalTrials.gov (API v2) | études néphro avec un centre en France ou en Belgique | automatique |
| Registre européen CTIS (euclinicaltrials.eu) | essais médicamenteux, investigateurs et contacts par centre | automatique |
| Pages « recherche » des services (CHU de Brest) | projets en cours, présentation en français | automatique |
| Listes des lauréats DGOS (PHRC-N, PHRC-I) | étiquetage PHRC, lauréats pas encore enregistrés | **manuelle, une fois par an** |

## Mise à jour

- **Automatique** : chaque lundi (GitHub Actions, `.github/workflows/mise-a-jour.yml`). On peut aussi la lancer à la
  demande : onglet *Actions* → *Mise à jour et publication* → *Run workflow*.
- **Listes PHRC** : déposer les nouveaux fichiers Excel de la DGOS dans `data/phrc_lists/` (le site du ministère bloque les
  téléchargements automatiques). Un projet qui a changé d'acronyme se déclare dans `data/phrc_alias.json`.
- **Autre service à ajouter** : sur le modèle de `scripts/brest_crawl.py` + `scripts/brest_parse.py`, produire un fichier
  `data/local/<centre>.json` ; `scripts/local_merge.py` l'intègre.

En local :

```bash
pip3 install -r requirements.txt
./run_all.sh     # collectes + construction (5 à 10 min)
./rebuild.sh     # construction seule, à partir des données déjà téléchargées
open site/index.html
```

## Organisation

```
scripts/
  harvest.py        collecte ClinicalTrials.gov
  process.py        filtre néphro (exclusion oncologie), thématiques, type d'étude, financement
  rules.py          règles partagées : mots-clés néphro / oncologie, thématiques, pathologies
  norm.py           noms de villes
  enrich.py         pathologies, centres actifs, contacts, coordonnées GPS
  ctis_*.py         registre européen : recherche, fiches détaillées, fusion avec ClinicalTrials.gov
  brest_*.py        pages recherche du CHU de Brest
  local_merge.py    intégration des sources locales (data/local/*.json)
  phrc_*.py         listes DGOS : lecture, recherche sur ClinicalTrials.gov, rapprochement
  centres.py        regroupement des libellés de centres par établissement
  build.py          construction de la page (app/template.html -> site/index.html)
app/template.html   interface (HTML/CSS/JS, sans dépendance)
site/index.html     page publiée (GitHub Pages)
```

## Limites

Statuts, centres et contacts tels que déclarés par les promoteurs ; thématiques et pathologies attribuées par mots-clés ;
regroupement des établissements automatique. Aucune donnée patient n'est collectée.

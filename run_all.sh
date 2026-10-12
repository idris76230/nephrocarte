#!/usr/bin/env bash
# Mise à jour complète de NéphroCarte : collectes puis traitement et construction de la page.
# Une source indisponible (site en panne, API lente) n'arrête pas la mise à jour : la dernière version connue est réutilisée.
set -euo pipefail
cd "$(dirname "$0")"
PY_XLSX=${PY_XLSX:-python3}
mkdir -p data/raw data/local site
warn() { echo "::warning::$1 — dernière version conservée"; }

# 1. collectes
python3 -I scripts/harvest.py data/raw/ctgov_frbe.json
$PY_XLSX -I scripts/phrc_parse.py data/phrc_lists data/phrc_all.json data/phrc_nephro.json | head -1
python3 -I scripts/phrc_ctgov.py data/phrc_nephro.json data/raw/ctgov_phrc.json | cut -c1-80 || warn "PHRC sur ClinicalTrials.gov"
{ python3 -I scripts/ctis_harvest.py data/raw/ctis_search.json > /dev/null &&
  python3 -I scripts/ctis_details.py data/raw/ctis_search.json data/raw/ctis_details.json; } || warn "registre européen CTIS"
{ python3 -I scripts/brest_crawl.py data/raw/brest_pages.json &&
  python3 -I scripts/brest_parse.py data/raw/brest_pages.json data/local/brest.json | head -1; } || warn "pages recherche CHU de Brest"

# corrections validées dans le Google Sheet des signalements du site
SHEET_CSV="https://docs.google.com/spreadsheets/d/e/2PACX-1vTPesbkiRJZhe8qTk_n57fSsjNItRtGuG-QjF8YMSY2dUGTpfdfN4jEisn2xVE_w3HiHHzYNcsrLCAu/pub?gid=227078854&single=true&output=csv"
python3 -I scripts/sheet_corrections.py "$SHEET_CSV" data/corrections_formulaire.json || warn "Google Sheet des signalements"

# 2. traitement (chaque étape repart de la sortie de la précédente : toujours tout relancer)
./rebuild.sh

#!/usr/bin/env bash
# Retraitement sans nouvelle collecte (après modification des règles, des sources locales ou de l'interface).
set -euo pipefail
cd "$(dirname "$0")"
python3 -I scripts/process.py data/raw/ctgov_frbe.json data/trials.json | head -1
python3 -I scripts/norm.py data/trials.json data/trials_n.json
python3 -I scripts/enrich.py data/raw/ctgov_frbe.json data/trials_n.json app/data.json | head -1
if [ -f data/raw/ctis_details.json ]; then
  python3 -I scripts/ctis_merge.py app/data.json data/raw/ctis_search.json data/raw/ctis_details.json app/data.json | head -1
fi
python3 -I scripts/local_merge.py app/data.json data/local app/data.json
python3 -I scripts/phrc_match.py app/data.json data/phrc_nephro.json app/data.json data/phrc_rapport.csv | head -2
python3 -I scripts/centres.py app/data.json app/data.json | head -1
if [ -f data/corrections.json ]; then
  python3 -I scripts/corrections.py app/data.json data/corrections.json app/data.json
fi
python3 -I scripts/build.py

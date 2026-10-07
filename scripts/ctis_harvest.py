"""Récupère dans CTIS (euclinicaltrials.eu) les essais néphro ayant un site en France ou en Belgique."""
import json, sys, urllib.request, time
URL = "https://euclinicaltrials.eu/ctis-public-api/search"
TERMS = ["kidney", "renal", "nephropathy", "nephritis", "glomerulonephritis", "glomerulopathy", "nephrotic", "dialysis",
         "haemodialysis", "hemodialysis", "nephrology", "IgA nephropathy", "lupus nephritis", "ANCA", "haemolytic uraemic",
         "hemolytic uremic", "C3 glomerulopathy", "polycystic kidney", "Alport", "Fabry", "cystinosis", "hyperoxaluria",
         "membranous nephropathy", "FSGS", "hyperkalaemia", "hyperkalemia", "kidney transplantation", "nephrolithiasis", "vasculitis"]
def post(body):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))
out = {}
for t in TERMS:
    page = 1
    while True:
        d = post({"pagination": {"page": page, "size": 100}, "sort": {"property": "decisionDate", "direction": "DESC"},
                  "searchCriteria": {"containAll": t}})
        for x in d["data"]:
            if any(c.split(":")[0] in ("France", "Belgium") for c in x.get("trialCountries", [])):
                out[x["ctNumber"]] = x
        if not d["pagination"]["nextPage"]: break
        page += 1; time.sleep(0.2)
    print(t, d["pagination"]["totalRecords"], "-> FR/BE cumul", len(out), flush=True)
json.dump(out, open(sys.argv[1], "w"))

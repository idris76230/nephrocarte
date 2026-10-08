"""Applique les corrections manuelles (data/corrections.json) après la collecte et le regroupement des centres.
Usage : python3 corrections.py app/data.json data/corrections.json app/data.json
"""
import json, sys, unicodedata

data = json.load(open(sys.argv[1])); corr = json.load(open(sys.argv[2]))["corrections"]
def k(s): return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower().strip()

def find(ref):
    r = k(ref)
    return [d for d in data if r in (k(d["id"]), k(d.get("nct")), k(d.get("ac"))) or r in map(k, d.get("eu", []))]

def coords(v):
    pts = [(c["la"], c["lo"]) for d in data for c in d["ce"] if c["v"] == v and c.get("la") is not None]
    return (round(sum(a for a, _ in pts) / len(pts), 4), round(sum(b for _, b in pts) / len(pts), 4)) if pts else (None, None)

done, missing = 0, []
for x in corr:
    ds = find(x["etude"])
    if not ds: missing.append(x["etude"]); continue
    for d in ds:
        if x.get("statut_etude"): d["st"] = x["statut_etude"]
        if x.get("note"): d["fr"] = (d.get("fr", "") + " " + x["note"]).strip()
        if x.get("retirer_centre"): d["ce"] = [c for c in d["ce"] if k(c["e"]) != k(x["retirer_centre"])]
        cx = x.get("centre")
        if cx:
            ks = [{kk: v for kk, v in {"n": p.get("nom", ""), "r": p.get("role", ""), "e": p.get("email", ""), "t": p.get("tel", "")}.items() if v}
                  for p in cx.get("contacts", [])]
            same = [c for c in d["ce"] if k(c["e"]) == k(cx["etablissement"])] or \
                   [c for c in d["ce"] if c["v"] == cx["ville"] and c["e"].startswith("Site non nommé")][:1]
            if same:
                c = same[0]
                c["e"] = cx["etablissement"]
                if cx.get("statut"): c["s"] = cx["statut"]
                c["k"] = ks + [y for y in c["k"] if y not in ks]
            else:
                la, lo = coords(cx["ville"])
                d["ce"].append({"f": cx["etablissement"], "e": cx["etablissement"], "v": cx["ville"], "p": cx.get("pays", "FR"), "z": "",
                                "s": cx.get("statut", "Ouvert"), "la": la, "lo": lo, "k": ks})
        d["corr"] = max(d.get("corr", ""), x.get("date", ""))
    done += 1
json.dump(data, open(sys.argv[3], "w"), ensure_ascii=False, separators=(",", ":"))
print(f"corrections manuelles : {done} appliquées" + (f" ; études introuvables : {', '.join(missing)}" if missing else ""))

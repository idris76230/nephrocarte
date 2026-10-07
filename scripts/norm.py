import json, sys, unicodedata
def k(s): return unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower().strip()
M = {"bron":"Lyon","pierre-benite":"Lyon","lyon":"Lyon","vandoeuvre-les-nancy":"Nancy","vandœuvre-lès-nancy":"Nancy","nancy":"Nancy",
 "brussels":"Bruxelles","bruxelles":"Bruxelles","brussel":"Bruxelles","jette":"Bruxelles","anderlecht":"Bruxelles","woluwe-saint-lambert":"Bruxelles","ixelles":"Bruxelles",
 "ghent":"Gand","gent":"Gand","antwerp":"Anvers","antwerpen":"Anvers","edegem":"Anvers","leuven":"Louvain","louvain":"Louvain","liege":"Liège","yvoir":"Yvoir (CHU UCL Namur)",
 "pessac":"Bordeaux","saint-herblain":"Nantes","saint-priest-en-jarez":"Saint-Étienne","saint-etienne":"Saint-Étienne","la tronche":"Grenoble","chambray-les-tours":"Tours",
 "le kremlin-bicetre":"Paris & IDF","creteil":"Paris & IDF","boulogne-billancourt":"Paris & IDF","clichy":"Paris & IDF","suresnes":"Paris & IDF","garches":"Paris & IDF","bobigny":"Paris & IDF","villejuif":"Paris & IDF","colombes":"Paris & IDF","le chesnay":"Paris & IDF","saint-denis":"Paris & IDF","paris":"Paris & IDF","neuilly-sur-seine":"Paris & IDF","bondy":"Paris & IDF","levallois-perret":"Paris & IDF","montreuil":"Paris & IDF","massy":"Paris & IDF","evry":"Paris & IDF","corbeil-essonnes":"Paris & IDF","argenteuil":"Paris & IDF","pontoise":"Paris & IDF","le plessis-robinson":"Paris & IDF","poissy":"Paris & IDF","versailles":"Paris & IDF",
 "vandoeuvre les nancy":"Nancy","lille":"Lille","loos":"Lille","montpellier":"Montpellier","toulouse":"Toulouse","marseille":"Marseille","nice":"Nice"}
def city(raw):
    return "Nancy" if "nancy" in k(raw) else M.get(k(raw), raw.strip().title() if raw.isupper() or raw.islower() else raw.strip())

if __name__ == "__main__":
    r = json.load(open(sys.argv[1]))
    for t in r:
        for c in t["ce"]:
            c["v"] = city(c["c"])
    json.dump(r, open(sys.argv[2],"w"), ensure_ascii=False, separators=(",",":"))

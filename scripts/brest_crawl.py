"""Parcourt les pages « projets de recherche » du CRMR / URC néphrologie de Brest et en extrait le texte."""
import html, json, re, sys, time, urllib.request
BASE = "https://nephrogenetique.chu-brest.fr"
def get(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
def text(h):
    m = re.search(r"(?s)<main.*?</main>", h); h = m.group(0) if m else h
    h = re.sub(r"(?s)<(script|style|nav)[^>]*>.*?</\1>", "", h)
    t = re.sub(r"<(br|/p|/li|/h\d|/tr|/td|/div)[^>]*>", "\n", h); t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t); t = re.sub(r"[ \t\xa0]+", " ", t); return re.sub(r"\n\s*\n+", "\n", t).strip()
seen, todo, pages = set(), ["/nos-activites/promotion-interne", "/nos-activites/promotion-externe",
                           "/nos-activites/hors-maladies-rares", "/nos-activites/greffe-renale"], {}
while todo:
    p = todo.pop(0)
    if p in seen: continue
    seen.add(p); h = get(p); time.sleep(0.3)
    kids = sorted(set(re.findall(r'href="(' + re.escape(p) + r'/[^"#?]+)"', h)))
    pages[p] = {"text": text(h), "children": kids, "links": sorted(set(re.findall(r'href="(https?://[^"]+)"', h)))}
    todo += [k for k in kids if k not in seen]
json.dump(pages, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
print(len(pages), "pages ;", sum(1 for v in pages.values() if not v["children"]), "fiches projet")

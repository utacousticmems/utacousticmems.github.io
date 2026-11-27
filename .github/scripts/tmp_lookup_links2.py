#!/usr/bin/env python3
"""TEMPORARY helper, second pass (removed again before the pull request is opened).
Checks the few entries the first pass could not settle, patent family details,
Prof. Hall's patents and papers in other indexes, and prints every OpenAlex work."""
import html, json, os, re, sys, time, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
import tmp_lookup_links as base  # noqa: E402
import yaml  # noqa: E402

out, get, sim, norm = base.out, base.get, base.sim, base.norm
pubs = yaml.safe_load(open("_data/publications.yml", encoding="utf-8"))
titles = [(p["title"], p["year"]) for p in pubs]


def best_site(t):
    s, y, tt = max(((sim(x, t), yy, x) for x, yy in titles), default=(0, None, ""))
    return round(s, 2), y, tt[:50]


# 1. Thévenin acoustics: two JASA DOIs
for doi in ("10.1121/1.4971284", "10.1121/1.4970288"):
    out("CRDOI", base.crossref_doi(doi))

# 2. OSTI records and title searches
for oid in ("1163476",):
    d = get(f"https://www.osti.gov/api/v1/records/{oid}")
    out("OSTI_ID", d if isinstance(d, list) else [d])
for t in ("Interferometric Sensor Platform", "MEMS integrated with optics and nanostructures for sensor applications",
          "Micro-Seismometers via Advanced Mesoscale Fabrication", "Ultrasensitive Directional Microphone Arrays"):
    d = get("https://www.osti.gov/api/v1/records", {"title": t, "rows": 8})
    rows = []
    for r in d or []:
        rows.append({k: r.get(k) for k in ("osti_id", "title", "authors", "publication_date", "doi", "report_number",
                                           "product_type", "conference_info", "research_orgs", "entry_date")})
    out("OSTI_SEARCH", {"q": t, "results": rows})

# 3. OpenAlex title search (theses and reports)
key = os.environ.get("OPENALEX_API_KEY", "").strip()
hdr = {"Authorization": f"Bearer {key}"} if key else {}
for t in ("Micromachined broadband acoustic transducers with integrated optical displacement detection",
          "Interferometric Sensor Platform", "MEMS integrated with optics and nanostructures for sensor applications"):
    d = get("https://api.openalex.org/works", {"search": t, "per-page": 5,
            "select": "id,doi,display_name,publication_year,type,authorships,locations"}, hdr)
    res = []
    for w in (d or {}).get("results", []):
        res.append({"title": w.get("display_name"), "year": w.get("publication_year"), "type": w.get("type"), "doi": w.get("doi"),
                    "authors": [((a.get("author") or {}).get("display_name")) for a in (w.get("authorships") or [])][:6],
                    "landing": [l.get("landing_page_url") for l in (w.get("locations") or [])][:4]})
    out("OA_SEARCH", {"q": t, "results": res})

# 4. Georgia Tech repository (DSpace 7)
d = get("https://repository.gatech.edu/server/api/discover/search/objects",
        {"query": "Micromachined broadband acoustic transducers with integrated optical displacement detection", "dsoType": "ITEM", "size": 5})
res = []
try:
    for o in d["_embedded"]["searchResult"]["_embedded"]["objects"]:
        it = o["_embedded"]["indexableObject"]
        md = it.get("metadata") or {}
        res.append({"name": it.get("name"), "handle": it.get("handle"),
                    "date": [x.get("value") for x in md.get("dc.date.issued", [])],
                    "author": [x.get("value") for x in md.get("dc.contributor.author", [])],
                    "uri": [x.get("value") for x in md.get("dc.identifier.uri", [])]})
except (KeyError, TypeError):
    res = ["no result", str(d)[:300]]
out("GATECH", res)


# 5. Google Patents pages
def gp_page(num):
    st, final, body = get(f"https://patents.google.com/patent/{num}/en", headers={"Accept": "text/html"}, raw=True)
    if st != 200:
        return {"num": num, "status": st}
    def meta(name):
        m = re.search(rf'<meta name="{name}" content="([^"]*)"', body)
        return html.unescape(m.group(1)).strip() if m else None
    app = re.search(r'itemprop="applicationNumber"[^>]*>([^<]+)<', body)
    fam = sorted(set(re.findall(r'\b(US\d{7,11}[AB]\d)\b', body)))
    events = re.findall(r'<time itemprop="date" datetime="([\d-]+)">[^<]*</time>\s*<span itemprop="title">([^<]+)</span>', body)
    return {"num": num, "title": meta("DC.title"), "date": meta("DC.date"), "app": app.group(1).strip() if app else None,
            "us_family": fam[:20], "events": events[:12]}


for num in ("US8989411B2", "US20120250897A1", "WO2015156859A2", "US20220128517A1", "US20220132240A1"):
    out("GP_PAGE", gp_page(num))
    time.sleep(1)


# 6. Prof. Hall's patents on Google Patents
seen = {}
for q in ("inventor=Neal+A+Hall&num=100", "inventor=Neal+Allen+Hall&num=100", "inventor=Neal+Hall&assignee=University+of+Texas&num=100",
          "inventor=Neal+Hall&assignee=Silicon+Audio&num=100", "inventor=Neal+Hall&assignee=Georgia+Tech&num=100",
          "inventor=Neal+Hall&assignee=Sandia&num=100"):
    st, final, body = get("https://patents.google.com/xhr/query?url=" + urllib.parse.quote(q, safe="") + "&exp=", raw=True)
    n = 0
    if st == 200 and body:
        try:
            dd = json.loads(body)
        except ValueError:
            dd = {}
        for c in (dd.get("results") or {}).get("cluster") or []:
            for rr in c.get("result") or []:
                p = rr.get("patent") or {}
                pn = p.get("publication_number")
                if pn and pn not in seen:
                    seen[pn] = {"pub": pn, "title": html.unescape(re.sub("<[^>]+>", "", p.get("title") or "")).strip()[:110],
                                "inv": re.sub("<[^>]+>", "", p.get("inventor") or "")[:80],
                                "asg": re.sub("<[^>]+>", "", p.get("assignee") or "")[:50],
                                "prio": p.get("priority_date"), "pubdate": p.get("publication_date"), "grant": p.get("grant_date")}
                    n += 1
    out("GP_QUERY", {"q": q, "status": st, "new": n})
    time.sleep(1.5)
for r in sorted(seen.values(), key=lambda r: r.get("prio") or ""):
    r["site"] = best_site(r["title"])
    out("GP_HALL", r)

# 7. Semantic Scholar
d = get("https://api.semanticscholar.org/graph/v1/author/search", {"query": "Neal A. Hall", "fields": "name,paperCount,affiliations", "limit": 10})
cands = (d or {}).get("data") or []
out("S2_AUTHORS", cands)
for a in cands[:4]:
    time.sleep(3)
    dd = get(f"https://api.semanticscholar.org/graph/v1/author/{a['authorId']}/papers",
             {"fields": "title,year,venue,externalIds,publicationTypes", "limit": 500})
    papers = (dd or {}).get("data") or []
    hits = sum(1 for p in papers if best_site(p.get("title"))[0] >= 0.85)
    out("S2_AUTHOR_PAPERS", {"id": a["authorId"], "name": a.get("name"), "papers": len(papers), "on_page": hits})
    if hits >= 5:
        for p in papers:
            s = best_site(p.get("title"))
            if s[0] < 0.85:
                out("S2_MISSING", {"year": p.get("year"), "title": p.get("title"), "venue": p.get("venue"),
                                   "doi": (p.get("externalIds") or {}).get("DOI"), "types": p.get("publicationTypes")})

# 8. Every OpenAlex work, with the closest entry on the page
for w in base.openalex_works():
    r = base.oa_row(w)
    out("OA_ALL", {"y": r["year"], "doi": r["doi"], "type": r["type"], "t": (r["title"] or "")[:70], "site": best_site(r["title"])})

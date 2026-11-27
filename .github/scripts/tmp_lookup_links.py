#!/usr/bin/env python3
"""TEMPORARY helper, removed again before the pull request is opened.

1. Finds DOIs for entries in _data/publications.yml that have no doi: or url:
   (OpenAlex works by Prof. Hall, his ORCID record, and a Crossref title search).
2. Lists works by Prof. Hall in OpenAlex, ORCID and Crossref that the page doesn't have.
3. Checks Google Patents addresses for the patents.
Prints one line per finding, prefixed with a tag, for reading in the job log.
"""
import json, os, re, time, unicodedata, urllib.error, urllib.parse, urllib.request
from difflib import SequenceMatcher

import yaml

UA = "publications-lookup/1.0 (+https://github.com/utacousticmems/utacousticmems.github.io)"
ORCID = "0000-0001-5237-8927"
OA_IDS = ["A5085364400", "A5112463774"]


def out(tag, obj):
    print(tag, json.dumps(obj, ensure_ascii=False), flush=True)


def get(url, params=None, headers=None, raw=False):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params, safe=":,|/()\"")
    h = {"User-Agent": UA, "Accept": "application/json"}
    h.update(headers or {})
    delay = 2
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=45) as r:
                body = r.read().decode("utf-8", "replace")
                return (r.status, r.geturl(), body) if raw else json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(delay); delay *= 2; continue
            if e.code != 404:
                print(f"ERR HTTP {e.code} {url[:160]}", flush=True)
            return (e.code, url, "") if raw else None
        except Exception as e:  # noqa: BLE001
            if attempt < 4:
                time.sleep(delay); delay *= 2; continue
            print(f"ERR {type(e).__name__}: {e} {url[:160]}", flush=True)
            return (0, url, "") if raw else None


def norm(t):
    t = unicodedata.normalize("NFKD", str(t or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"<[^>]+>", " ", t).lower().replace("&amp;", " and ").replace("&", " and ")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())


def sim(site_title, cand):
    a, b = norm(site_title), norm(cand)
    if not a or not b:
        return 0.0
    if str(site_title).rstrip().endswith(("…", "...")):
        a = norm(str(site_title).rstrip(" .…"))
        b = b[: len(a)]
    return round(SequenceMatcher(None, a, b).ratio(), 3)


def to_int(y):
    try:
        return int(str(y)[:4])
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ sources

def openalex_works():
    key = os.environ.get("OPENALEX_API_KEY", "").strip()
    hdr = {"Authorization": f"Bearer {key}"} if key else {}
    works = {}
    for flt in [f"author.orcid:{ORCID}"] + [f"author.id:{a}" for a in OA_IDS]:
        for page in range(1, 8):
            d = get("https://api.openalex.org/works", {
                "filter": flt, "per-page": 200, "page": page,
                "select": "id,doi,display_name,publication_year,type,primary_location,authorships,biblio",
            }, hdr)
            res = (d or {}).get("results") or []
            for w in res:
                w["_via"] = flt
                works.setdefault(w["id"], w)
            if len(res) < 200:
                break
    out("INFO", {"openalex_works": len(works)})
    return list(works.values())


def oa_row(w):
    src = ((w.get("primary_location") or {}).get("source") or {})
    b = w.get("biblio") or {}
    return {
        "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
        "year": w.get("publication_year"), "type": w.get("type"),
        "title": w.get("display_name"), "venue": src.get("display_name"),
        "vol": b.get("volume"), "iss": b.get("issue"), "pages": "-".join(x for x in [b.get("first_page"), b.get("last_page")] if x),
        "authors": [((a.get("author") or {}).get("display_name")) for a in (w.get("authorships") or [])][:14],
        "via": w.get("_via"), "oa": w.get("id", "").rsplit("/", 1)[-1],
    }


def orcid_works():
    d = get(f"https://pub.orcid.org/v3.0/{ORCID}/works")
    rows = []
    for g in (d or {}).get("group", []):
        for s in (g.get("work-summary") or [])[:1]:
            title = (((s.get("title") or {}).get("title")) or {}).get("value")
            year = ((((s.get("publication-date") or {}).get("year")) or {}) or {}).get("value")
            doi = ""
            for x in (((s.get("external-ids") or {}).get("external-id")) or []):
                if (x.get("external-id-type") or "").lower() == "doi":
                    doi = x.get("external-id-value") or ""
                    break
            jt = s.get("journal-title") or {}
            rows.append({"title": title, "year": year, "doi": doi, "venue": jt.get("value") if isinstance(jt, dict) else "", "type": s.get("type")})
    out("INFO", {"orcid_works": len(rows)})
    return rows


CR_SELECT = "DOI,title,author,issued,container-title,type,volume,issue,page,article-number"


def cr_row(it):
    yr = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
    return {
        "doi": it.get("DOI"), "year": yr, "type": it.get("type"),
        "title": " ".join(it.get("title") or []), "venue": " ".join(it.get("container-title") or []),
        "vol": it.get("volume"), "iss": it.get("issue"), "pages": it.get("page") or it.get("article-number"),
        "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in (it.get("author") or [])][:14],
        "hall": any((a.get("family") or "").lower() == "hall" for a in (it.get("author") or [])),
    }


def crossref_search(entry):
    first = re.split(r"\s+", entry["authors"].split(",")[0].strip())[-1]
    d = get("https://api.crossref.org/works", {
        "query.bibliographic": f'{entry["title"]} {entry.get("venue", "")} {entry["year"]}',
        "query.author": f"{first} Hall", "rows": 6, "select": CR_SELECT,
    })
    time.sleep(0.15)
    return [cr_row(it) for it in ((d or {}).get("message") or {}).get("items", [])]


def crossref_doi(doi):
    d = get("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/:;()"))
    time.sleep(0.1)
    return cr_row((d or {}).get("message") or {}) if d else None


def datacite_search(title):
    d = get("https://api.datacite.org/dois", {"query": f'titles.title:"{title}"', "page[size]": 5})
    rows = []
    for it in (d or {}).get("data", []):
        a = it.get("attributes") or {}
        rows.append({"doi": a.get("doi"), "year": a.get("publicationYear"),
                     "title": " ".join(t.get("title", "") for t in (a.get("titles") or [])[:1]),
                     "venue": a.get("publisher"), "type": (a.get("types") or {}).get("resourceTypeGeneral"),
                     "authors": [c.get("name") for c in (a.get("creators") or [])][:8]})
    return rows


def best(entry, rows):
    scored = [(sim(entry["title"], r.get("title")), r) for r in rows if r.get("title")]
    scored.sort(key=lambda x: -x[0])
    return scored[0] if scored else (0.0, None)


# ------------------------------------------------------------------ main

def main():
    pubs = yaml.safe_load(open("_data/publications.yml", encoding="utf-8"))
    people = yaml.safe_load(open("_data/people.yml", encoding="utf-8"))
    oa = [oa_row(w) for w in openalex_works()]
    orc = orcid_works()

    # 1. links for entries without one
    for i, e in enumerate(pubs):
        if e.get("doi") or e.get("url") or e.get("type") == "patent":
            continue
        y = to_int(e.get("year"))
        row = {"i": i, "year": y, "type": e.get("type"), "title": e["title"][:100], "venue": (e.get("venue") or "")[:60]}
        s_oa, r_oa = best(e, [r for r in oa if r["doi"]])
        s_or, r_or = best(e, [r for r in orc if r["doi"]])
        crs = crossref_search(e)
        s_cr, r_cr = best(e, crs)
        row["oa"] = [r_oa["doi"], s_oa, r_oa["year"], (r_oa["venue"] or "")[:50]] if r_oa else None
        row["orcid"] = [r_or["doi"], s_or, r_or["year"]] if r_or else None
        row["cr"] = [r_cr["doi"], s_cr, r_cr["year"], (r_cr["venue"] or "")[:50], r_cr["hall"], r_cr["type"]] if r_cr else None
        if r_cr and s_cr < 0.93:
            row["cr_title"] = (r_cr["title"] or "")[:100]
        if max(s_oa, s_or, s_cr) < 0.9 and e.get("type") in ("other", "conference", "journal"):
            s_dc, r_dc = best(e, datacite_search(e["title"].rstrip(" .…")))
            row["dc"] = [r_dc["doi"], s_dc, r_dc["year"], (r_dc["venue"] or "")[:50], (r_dc["title"] or "")[:80]] if r_dc else None
        # Crossref record of the most likely DOI, for checking details
        cand = None
        for s, r in ((s_cr, r_cr), (s_oa, r_oa), (s_or, r_or)):
            if r and r.get("doi") and s >= 0.9:
                cand = r["doi"]
                break
        if cand:
            rec = crossref_doi(cand)
            if rec:
                row["rec"] = {k: rec[k] for k in ("doi", "year", "venue", "vol", "iss", "pages", "type", "hall")}
                row["rec"]["title"] = (rec["title"] or "")[:160]
                row["rec"]["authors"] = rec["authors"][:10]
        out("LINK", row)

    # 2. works not on the page
    titles = [p["title"] for p in pubs]
    def on_page(t):
        return max((sim(x, t) for x in titles), default=0) >= 0.85
    for r in oa:
        if r["title"] and not on_page(r["title"]):
            out("MISSING_OA", r)
    for r in orc:
        if r["title"] and not on_page(r["title"]):
            out("MISSING_ORCID", r)
    group = set()
    for p in pubs:
        for a in (p.get("authors") or "").split(","):
            if a.strip():
                group.add(norm(a.strip().split()[-1]))
    for sec in ("phd", "postdocs", "undergrads", "alumni"):
        for m in people.get(sec) or []:
            group.add(norm(m["name"].split()[-1]))
    group.discard("hall")
    seen = set()
    for yr in range(2010, 2027):
        d = get("https://api.crossref.org/works", {
            "query.author": "Neal A. Hall", "filter": f"from-pub-date:{yr}-01-01,until-pub-date:{yr}-12-31",
            "rows": 300, "select": CR_SELECT + ",published-print,published-online",
        })
        items = ((d or {}).get("message") or {}).get("items", [])
        n = 0
        for it in items:
            auth = it.get("author") or []
            neal = any((a.get("family") or "").lower() == "hall" and (a.get("given") or "").lower().startswith("n") for a in auth)
            co = sorted({norm(a.get("family") or "") for a in auth} & group)
            if not neal or not co:
                continue
            r = cr_row(it)
            if r["doi"] in seen or on_page(r["title"]):
                continue
            seen.add(r["doi"])
            r["coauthors_known"] = co[:6]
            out("MISSING_CR", r)
            n += 1
        out("INFO", {"crossref_year": yr, "items": len(items), "new": n})
        time.sleep(0.3)

    # 3. patents
    for e in pubs:
        if e.get("type") != "patent" or e.get("url"):
            continue
        v = e.get("venue") or ""
        m = re.search(r"US Patent ([\d,]+)$", v)
        if m:
            num = m.group(1).replace(",", "")
            hit = None
            for kind in ("B2", "B1"):
                st, final, body = get(f"https://patents.google.com/patent/US{num}{kind}/en", headers={"Accept": "text/html"}, raw=True)
                if st == 200 and body:
                    t = re.search(r'<meta name="DC.title" content="([^"]*)"', body)
                    hit = {"kind": kind, "url": f"https://patents.google.com/patent/US{num}{kind}", "title": t.group(1).strip() if t else None}
                    break
            out("PATENT", {"venue": v, "site_title": e["title"][:90], "hit": hit})
        else:
            q = e["title"].rstrip(" .…")
            qs = urllib.parse.quote(f'q=("{q}")&inventor=Neal+Hall', safe="")
            st, final, body = get(f"https://patents.google.com/xhr/query?url={qs}&exp=", raw=True)
            res = []
            if st == 200 and body:
                try:
                    dd = json.loads(body)
                    for c in (dd.get("results") or {}).get("cluster") or []:
                        for rr in (c.get("result") or [])[:6]:
                            p = rr.get("patent") or {}
                            res.append({"pub": p.get("publication_number"), "title": re.sub("<[^>]+>", "", p.get("title") or "")[:90],
                                        "inv": (p.get("inventor") or "")[:60], "date": p.get("publication_date"),
                                        "grant": p.get("grant_date"), "prio": p.get("priority_date")})
                except ValueError:
                    res = ["not json"]
            out("PATENT_APP", {"venue": v, "site_title": e["title"][:90], "status": st, "results": res})
            time.sleep(1)


if __name__ == "__main__":
    main()

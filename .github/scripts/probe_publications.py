#!/usr/bin/env python3
"""Temporary probe: how well do OpenAlex and Crossref cover the group's papers?

Reads _data/publications.yml, looks up the DOIs already on the page, finds
Prof. Hall's author IDs from those lookups, then lists what each source returns
for him since START. Prints a report. Read-only; changes nothing.
"""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from difflib import SequenceMatcher

import yaml

START = "2024-01-01"
UA = "publications-probe/0.1 (GitHub Actions)"
OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read()[:300].decode("utf-8", "replace")
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(3 * (attempt + 1))
                continue
            return e.code, body
        except Exception as e:  # network hiccup
            if attempt < 3:
                time.sleep(3)
                continue
            return -1, str(e)
    return -1, "gave up"


def norm_title(t):
    t = unicodedata.normalize("NFKD", t or "")
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"[^a-z0-9]+", "", t.lower())


def is_hall(name):
    name = (name or "").strip()
    return bool(re.search(r"\bHall\b", name)) and name[:1].upper() == "N"


def main():
    pubs = yaml.safe_load(open("_data/publications.yml", encoding="utf-8"))
    say(f"Entries on the page: {len(pubs)}")
    page_dois = {}
    page_arxiv = {}
    page_titles = {}
    for p in pubs:
        if p.get("doi"):
            page_dois[str(p["doi"]).lower().replace("https://doi.org/", "")] = p
        m = re.search(r"arxiv\.org/abs/([0-9.]+)", str(p.get("url", "")))
        if m:
            page_arxiv[m.group(1)] = p
        page_titles[norm_title(str(p.get("title", "")))] = p
    say(f"Entries with a DOI: {len(page_dois)}; arXiv links: {len(page_arxiv)}")

    # 1) Look up every DOI on the page (and the arXiv ones) in OpenAlex and Crossref
    oa_ids, oa_orcids, cr_orcids = Counter(), Counter(), Counter()
    say("\n## DOIs already on the page")
    say("| year | type | DOI | OpenAlex | Hall's OpenAlex ID | Crossref | Hall ORCID in Crossref |")
    say("|---|---|---|---|---|---|---|")
    lookups = [(d, p) for d, p in page_dois.items()]
    lookups += [(f"10.48550/arxiv.{a}", p) for a, p in page_arxiv.items()]
    first_status = None
    for doi, p in sorted(lookups, key=lambda x: -int(x[1].get("year", 0))):
        st, oa = get_json("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="/:."))
        if first_status is None:
            first_status = st
            say(f"(first OpenAlex call returned HTTP {st}{'' if st == 200 else ': ' + str(oa)[:200]})")
        hall_oa = "-"
        if st == 200 and isinstance(oa, dict):
            for a in oa.get("authorships", []):
                names = [a.get("raw_author_name") or "", (a.get("author") or {}).get("display_name") or ""]
                if any(is_hall(n) for n in names):
                    aid = ((a.get("author") or {}).get("id") or "").rsplit("/", 1)[-1]
                    orc = ((a.get("author") or {}).get("orcid") or "").rsplit("/", 1)[-1]
                    hall_oa = aid + (f" (ORCID {orc})" if orc else "")
                    if aid:
                        oa_ids[aid] += 1
                    if orc:
                        oa_orcids[orc] += 1
        time.sleep(0.15)
        cr_txt, hall_cr = "-", "-"
        if not doi.startswith("10.48550"):
            st2, cr = get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/:."))
            if st2 == 200 and isinstance(cr, dict):
                m = cr["message"]
                cr_txt = m.get("type", "?")
                for a in m.get("author", []):
                    full = f"{a.get('given', '')} {a.get('family', '')}"
                    if is_hall(full):
                        orc = (a.get("ORCID") or "").rsplit("/", 1)[-1]
                        hall_cr = orc or "no ORCID"
                        if orc:
                            cr_orcids[orc] += 1
            else:
                cr_txt = f"HTTP {st2}"
            time.sleep(0.15)
        say(f"| {p.get('year')} | {p.get('type')} | {doi} | {'yes' if st == 200 else 'HTTP ' + str(st)} | {hall_oa} | {cr_txt} | {hall_cr} |")

    say(f"\nHall's OpenAlex IDs seen: {dict(oa_ids)}")
    say(f"Hall's ORCIDs seen in OpenAlex: {dict(oa_orcids)}")
    say(f"Hall's ORCIDs seen in Crossref: {dict(cr_orcids)}")

    def on_page(doi, title, arxiv_id):
        if doi and doi.lower() in page_dois:
            return "same DOI"
        if arxiv_id and arxiv_id in page_arxiv:
            return "same arXiv"
        nt = norm_title(title)
        if nt in page_titles:
            q = page_titles[nt]
            return f"same title (page entry: {q.get('type')}, doi={q.get('doi', '-')})"
        for k, q in page_titles.items():
            if nt and k and SequenceMatcher(None, nt, k).ratio() > 0.9:
                return f"similar title (page entry: {q.get('type')}, doi={q.get('doi', '-')})"
        return ""

    # 2) Author profiles
    for aid in oa_ids:
        st, au = get_json(f"https://api.openalex.org/authors/{aid}")
        if st == 200:
            inst = ", ".join(i.get("display_name", "") for i in au.get("last_known_institutions") or [])
            say(f"\nOpenAlex author {aid}: {au.get('display_name')} | works: {au.get('works_count')} | ORCID: {au.get('orcid')} | last known: {inst}")
        time.sleep(0.15)

    # 3) OpenAlex works for Hall since START
    def oa_list(filt):
        out, cursor = [], "*"
        while cursor:
            url = ("https://api.openalex.org/works?per-page=200&sort=publication_date:desc&cursor="
                   + urllib.parse.quote(cursor) + "&filter=" + urllib.parse.quote(filt, safe=":,|"))
            st, js = get_json(url)
            if st != 200:
                say(f"OpenAlex list failed for {filt}: HTTP {st} {str(js)[:200]}")
                break
            out += js.get("results", [])
            cursor = js.get("meta", {}).get("next_cursor")
            if not js.get("results"):
                break
            time.sleep(0.2)
        return out

    seen = {}
    if oa_ids:
        filt = "author.id:" + "|".join(oa_ids) + f",from_publication_date:{START}"
        works = oa_list(filt)
        say(f"\n## OpenAlex: works by Hall's author ID(s) since {START}: {len(works)}")
        say("| date | OA type | venue | DOI | title | on page? |")
        say("|---|---|---|---|---|---|")
        for w in works:
            doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
            arx = None
            m = re.search(r"10\.48550/arxiv\.([0-9.]+)", doi)
            if m:
                arx = m.group(1)
            for loc in w.get("locations") or []:
                m = re.search(r"arxiv\.org/abs/([0-9.]+)", (loc.get("landing_page_url") or ""))
                if m:
                    arx = arx or m.group(1)
            src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "")
            status = on_page(doi, w.get("display_name"), arx)
            seen[doi or w.get("id")] = status
            say(f"| {w.get('publication_date')} | {w.get('type')} | {src} | {doi or '-'} | {(w.get('display_name') or '')[:90]} | {status or '**NOT ON PAGE**'} |")

    for orc in oa_orcids or cr_orcids:
        works = oa_list(f"author.orcid:{orc},from_publication_date:{START}")
        say(f"\nOpenAlex works by ORCID {orc} since {START}: {len(works)}")
        extra = [w for w in works if ((w.get('doi') or '').replace('https://doi.org/', '').lower() or w.get('id')) not in seen]
        for w in extra:
            say(f"  extra via ORCID: {w.get('publication_date')} {w.get('doi')} {(w.get('display_name') or '')[:90]}")

    # 4) Crossref by ORCID
    for orc in set(cr_orcids) | set(oa_orcids):
        st, js = get_json(f"https://api.crossref.org/works?rows=200&filter=orcid:{orc},from-pub-date:{START}")
        if st == 200:
            items = js["message"]["items"]
            say(f"\n## Crossref: works with ORCID {orc} since {START}: {len(items)}")
            for it in items:
                doi = it.get("DOI", "").lower()
                t = (it.get("title") or [""])[0]
                status = on_page(doi, t, None)
                say(f"  {it.get('type')} | {doi} | {t[:90]} | {status or 'NOT ON PAGE'} | also in OpenAlex list: {'yes' if doi in seen else 'no'}")
        else:
            say(f"Crossref ORCID query failed: HTTP {st}")

    # 5) Page DOIs since 2024 that the OpenAlex author query did not return
    missing = [d for d, p in page_dois.items() if int(p.get("year", 0)) >= 2024 and d not in seen]
    say(f"\nPage DOIs (2024+) NOT returned by the OpenAlex author query: {missing}")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())

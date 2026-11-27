#!/usr/bin/env python3
"""TEMPORARY helper, third pass (removed again before the pull request is opened):
inventors and dates of Prof. Hall's patents, and details of the papers to suggest."""
import html, os, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import tmp_lookup_links as base  # noqa: E402

out, get = base.out, base.get

for doi in ("10.1121/10.0018445", "10.1121/10.0016205", "10.1121/1.5137376", "10.1121/1.3654726", "10.2172/1591797"):
    out("CRDOI", base.crossref_doi(doi))
d = get("https://www.osti.gov/api/v1/records/1591797")
for r in (d if isinstance(d, list) else [d]):
    if r:
        out("OSTI", {k: r.get(k) for k in ("osti_id", "title", "authors", "publication_date", "doi", "report_number",
                                         "product_type", "research_orgs", "sponsor_orgs", "contributing_org")})

for num in ("US8391517B2", "US9702992B2", "US9832573B2", "US10309845B2", "US11073433B2", "US20250345636A1",
            "US20260022009A1", "US20260292408A1", "US20160337761A1", "US8989411B2", "US9479875B2", "US9503820B2",
            "US9372111B2", "US7485847B2", "US7518737B2", "US7440117B2", "US7116430B2", "US20220128517A1",
            "US20220132240A1", "US20260061226A1"):
    st, final, body = get(f"https://patents.google.com/patent/{num}/en", headers={"Accept": "text/html"}, raw=True)
    if st != 200:
        out("GP", {"num": num, "status": st})
        continue
    inv = [html.unescape(x) for x in re.findall(r'<meta name="DC.contributor" content="([^"]*)" scheme="inventor"', body)]
    asg = [html.unescape(x) for x in re.findall(r'<meta name="DC.contributor" content="([^"]*)" scheme="assignee"', body)]
    t = re.search(r'<meta name="DC.title" content="([^"]*)"', body)
    app = re.search(r'itemprop="applicationNumber"[^>]*>([^<]+)<', body)
    ev = re.findall(r'<time itemprop="date" datetime="([\d-]+)">[^<]*</time>\s*<span itemprop="title">([^<]+)</span>', body)
    ev = [e for e in ev if re.search(r"Publication of|granted|Application filed|Priority to US", e[1])]
    out("GP", {"num": num, "title": html.unescape(t.group(1)).strip() if t else None, "inventors": inv, "assignees": asg,
               "app": app.group(1).strip() if app else None, "events": ev[:10]})
    time.sleep(1)

#!/usr/bin/env python3
"""Weekly publications check for the group website.

What it does
  1. Asks OpenAlex (a free index of scholarly papers that picks up every new
     DOI) for recent papers by the people in settings.yml, using their ORCID iDs.
  2. Skips papers that are already on the Publications page, were suggested
     before, or are listed under `skip:` in settings.yml.
  3. Writes the rest in the same format as _data/publications.yml (details come
     from Crossref, the DOI registry) and opens one pull request for a person
     to review. Nothing goes live until someone merges it.

Runs every Monday from .github/workflows/publications-bot.yml.
  python .github/publications-bot/update_publications.py            # normal run (GitHub Actions)
  python .github/publications-bot/update_publications.py --dry-run  # show what it would do, change nothing
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

import yaml

BOT_DIR = Path(__file__).resolve().parent
ROOT = BOT_DIR.parent.parent
PUBS_PATH = "_data/publications.yml"
SUGGESTED_PATH = ".github/publications-bot/already-suggested.txt"
SETTINGS_PATH = ".github/publications-bot/settings.yml"
WORKFLOW_FILE = "publications-bot.yml"
BRANCH_PREFIX = "publications-bot/"
LABEL = "publications-bot"
MARKER = "publications-bot-dois"          # hidden list of the DOIs a pull request suggests
SUPERSEDED = "publications-bot-superseded"  # a pull request the bot replaced with a fresh one
ISSUE_TITLE = "New publications found: please review"  # used when GitHub won't let the check open a pull request
REVIEW_BRANCH = BRANCH_PREFIX + "review"  # fixed branch for that issue's link, so links in older emails keep working
DONE = "publications-bot-done"            # marks an issue the check closed itself; a person closing one means "skip"
REPO = os.environ.get("GITHUB_REPOSITORY", "")
USER_AGENT = "publications-bot/1.0" + (f" (+https://github.com/{REPO})" if REPO else "")

ARXIV_RE = re.compile(r"(?:arxiv\.org/abs/|10\.48550/arxiv\.|arxiv:\s*)(\d{4}\.\d{4,5})", re.I)
YEAR_HEADER_RE = re.compile(r"^# -+ (\d{4}) -+\s*$")
SKIP_TYPES = {"paratext", "erratum", "retraction", "editorial", "peer-review", "dataset",
              "supplementary-materials", "libguides", "grant", "standard"}
SKIP_TITLE_RE = re.compile(r"^(erratum|errata|correction|corrections to|author correction|"
                           r"retraction|retracted|publisher correction|front cover|back cover|"
                           r"table of contents)\b", re.I)
PARTICLES = {"van", "von", "der", "den", "de", "da", "del", "della", "di", "du", "la", "le", "dos", "das"}
TYPE_WORDS = {"journal": "a journal paper", "conference": "a conference paper", "abstract": "an abstract",
              "preprint": "a preprint", "patent": "a patent", "other": "an entry"}

# Words that stay capitalized when a Title Case title is changed to sentence case.
# More can be added under keep_capitalized: in settings.yml.
KEEP_CAPS = {
    # people and effects
    "Doppler", "Mach", "Zehnder", "Fabry", "Perot", "Pérot", "Helmholtz", "Rayleigh", "Lamb", "Love",
    "Brillouin", "Kerr", "Bragg", "Fourier", "Gaussian", "Lorentz", "Lorentzian", "Young", "Poisson",
    "Raman", "Michelson", "Sagnac", "Thévenin", "Thevenin", "Norton", "Kalman", "Bayesian", "Euler",
    "Bernoulli", "Timoshenko", "Kirchhoff", "Navier", "Stokes", "Faraday", "Coulomb", "Maxwell",
    "Schottky", "Wheatstone", "Pirani", "Butterworth", "Chebyshev", "Nyquist", "Bode", "Laplace",
    "Boltzmann", "Planck", "Johnson", "Brownian", "Langevin", "Duffing", "Mathieu", "Floquet",
    "Hilbert", "Green", "Mindlin", "Kelvin", "Westervelt", "Burgers", "Ormia", "Terfenol",
    # places and organizations
    "Texas", "Austin", "America", "American", "Acoustical", "IEEE",
    # units and elements that look like ordinary words
    "Hz", "Pa", "Si", "Al", "Au", "Pt", "Ti", "Cr", "Ni", "Cu", "Ag", "Zn", "Mo", "Sc", "Ge", "Ga",
    "Li", "Ta", "Nb", "Hf", "Zr", "Pb", "Fe", "Mg", "Sn",
    "I",
}

OUT: list[str] = []  # report lines, also written to the GitHub job summary


def log(msg: str = "") -> None:
    print(msg, flush=True)
    OUT.append(msg)


# ----------------------------------------------------------------------------- HTTP

def http_json(url: str, params: dict | None = None, headers: dict | None = None):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params, safe=":,|/")
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    hdrs.update(headers or {})
    req = urllib.request.Request(url, headers=hdrs)
    delay = 2.0
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None
            if err.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(delay)
                delay *= 2
                continue
            body = err.read()[:300].decode("utf-8", "replace")
            raise RuntimeError(f"HTTP {err.code} from {url.split('?')[0]}: {body}") from err
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt < 4:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    return None


def openalex(path: str, params: dict) -> dict:
    headers = {}
    key = os.environ.get("OPENALEX_API_KEY", "").strip()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return http_json("https://api.openalex.org/" + path, params, headers) or {}


def crossref_work(doi: str, contact: str):
    params = {"mailto": contact} if contact else None
    data = http_json("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/:;()"), params)
    return (data or {}).get("message")


# ----------------------------------------------------------------------------- text helpers

SUB = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")
SUP = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")
HYPHENS = dict.fromkeys(map(ord, "‐‑‒−"), "-")


def clean_text(value) -> str:
    """Plain, single-line text that is safe to show on the page (no HTML tags)."""
    s = html.unescape(str(value or ""))
    s = re.sub(r"<sub>\s*([0-9+\-=()]+)\s*</sub>", lambda m: m.group(1).translate(SUB), s, flags=re.I)
    s = re.sub(r"<sup>\s*([0-9+\-=()]+)\s*</sup>", lambda m: m.group(1).translate(SUP), s, flags=re.I)
    s = re.sub(r"<[^<>]*>", "", s)  # italics, MathML and other markup
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"[\x00-\x1f\x7f]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def fold(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def norm_title(t) -> str:
    return re.sub(r"[^a-z0-9]+", "", fold(clean_text(t)))


def norm_doi(d) -> str:
    d = str(d or "").strip().lower()
    d = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", d)
    return d


def arxiv_id(*values) -> str:
    for v in values:
        m = ARXIV_RE.search(str(v or ""))
        if m:
            return m.group(1)
    return ""


def key_of(value: str) -> str:
    """Normalized DOI, or arXiv number, used to remember and skip papers."""
    a = arxiv_id(value)
    return f"arxiv:{a}" if a else norm_doi(value)


def initials(given: str) -> str:
    given = clean_text(given).translate(HYPHENS)
    out = []
    for tok in re.split(r"[\s.]+", given):
        parts = [p for p in tok.split("-") if p]
        if parts:
            out.append("-".join(p[0].upper() + "." for p in parts))
    return " ".join(out)


def split_name(full: str) -> tuple[str, str]:
    full = clean_text(full).translate(HYPHENS)
    if "," in full:
        family, given = [x.strip() for x in full.split(",", 1)]
        return given, family
    parts = full.split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return "", parts[0]
    i = len(parts) - 1
    while i > 1 and parts[i - 1].lower() in PARTICLES:
        i -= 1
    return " ".join(parts[:i]), " ".join(parts[i:])


def short_name(given: str, family: str) -> str:
    family = clean_text(family).translate(HYPHENS)
    if family.isupper() and len(family) > 2:
        family = family.title()
    return f"{initials(given)} {family}".strip()


def name_key(given: str, family: str) -> str:
    g = fold(clean_text(given)).strip()
    f = re.sub(r"[^a-z]+", "", fold(clean_text(family)))
    return f"{g[:1]}|{f}"


def to_sentence_case(title: str, keep: set[str]) -> str:
    """Change a Title Case title to sentence case, the style used on the page.

    Leaves the title alone when it already looks like sentence case. Keeps
    acronyms (MEMS, LDV), mixed-case words (AlN, LiNbO3, kHz), words with digits
    and the names in `keep` (Doppler, Mach–Zehnder ...).
    """
    words = title.split(" ")

    def core_of(w: str) -> str:
        c = re.sub(r"^[^\w]+|[^\w]+$", "", w)
        return re.sub(r"['’]s$", "", c)

    content = []
    for w in words[1:]:
        c = core_of(w)
        if re.fullmatch(r"[A-Za-z][a-z]{3,}", c) and c not in keep:
            content.append(c)
    if len(content) < 3 or sum(c[0].isupper() for c in content) / len(content) < 0.5:
        return title

    def convert(part: str, in_compound: bool) -> str:
        c = core_of(part)
        if not c:
            return part
        if c in keep or (c.endswith("s") and c[:-1] in keep):
            return part
        if sum(ch.isupper() for ch in c) >= 2 or any(ch.isupper() for ch in c[1:]):
            return part  # acronym or mixed case: MEMS, AlN, LiNbO3, kHz
        if any(ch.isdigit() for ch in c):
            return part
        if len(c) == 1 and c.isupper() and (in_compound or c != "A"):
            return part  # X-cut, Q factor
        return part.lower()

    out = []
    for i, w in enumerate(words):
        pieces = re.split(r"([-–/])", w)
        conv = []
        for j, p in enumerate(pieces):
            if p in ("-", "–", "/") or (i == 0 and j == 0):
                conv.append(p)
            else:
                conv.append(convert(p, in_compound=len(pieces) > 1))
        out.append("".join(conv))
    return " ".join(out)


# ----------------------------------------------------------------------------- the page

def load_yaml_text(text: str):
    data = yaml.safe_load(text)
    return data if isinstance(data, list) else []


class Page:
    """What is already on the Publications page."""

    def __init__(self, entries: list[dict]):
        self.keys: set[str] = set()
        self.titles: list[tuple[str, dict]] = []
        self.author_keys: set[str] = set()
        for e in entries:
            if not isinstance(e, dict):
                continue
            if e.get("doi"):
                self.keys.add(key_of(e["doi"]))
            a = arxiv_id(e.get("url"), e.get("doi"))
            if a:
                self.keys.add(f"arxiv:{a}")
            self.titles.append((norm_title(e.get("title")), e))
            if e.get("era") != "pre-ut":
                for name in str(e.get("authors") or "").split(","):
                    name = name.strip()
                    if name and "et al" not in name:
                        self.author_keys.add(name_key(*split_name(name)))

    def match(self, key: str, title: str, typ: str):
        """('same', entry) if the paper is on the page, ('version', entry) if another
        version of it is (say the preprint of a journal paper), else (None, None)."""
        if key in self.keys:
            return "same", None
        nt = norm_title(title)
        same, other = [], []
        for t, e in self.titles:
            if not t or not nt:
                continue
            if t == nt or (abs(len(t) - len(nt)) <= 12 and SequenceMatcher(None, t, nt).ratio() >= 0.92):
                (same if e.get("type") == typ else other).append(e)
        if same:
            return "same", same[0]
        if other:
            return "version", other[0]
        return None, None


def entry_yaml(entry: dict) -> str:
    def scalar(v) -> str:
        s = str(v)
        try:
            if yaml.safe_load(f"k: {s}") == {"k": s} and not s.startswith(("'", '"')):
                return s
        except yaml.YAMLError:
            pass
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

    lines = []
    for k in ("year", "type", "authors", "title", "venue", "details", "doi", "url"):
        if entry.get(k) in (None, ""):
            continue
        v = entry[k] if k == "year" else scalar(entry[k])
        lines.append(("- " if not lines else "  ") + f"{k}: {v}")
    return "\n".join(lines) + "\n"


def insert_entries(text: str, entries: list[dict]) -> str:
    """Add entries at the top of their year in publications.yml, newest first."""
    for e in sorted(entries, key=lambda e: e["_date"]):  # oldest first, so the newest ends up on top
        lines = text.splitlines(keepends=True)
        year = int(e["year"])
        block = entry_yaml(e)
        headers = [(i, int(m.group(1))) for i, l in enumerate(lines) if (m := YEAR_HEADER_RE.match(l))]
        same = [i for i, y in headers if y == year]
        older = [i for i, y in headers if y < year]
        if same:
            lines.insert(same[0] + 1, block)
        elif older:
            lines.insert(older[0], f"# ---------------- {year} ----------------\n{block}\n")
        else:  # older than every dated section: add a section at the end
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append(f"\n# ---------------- {year} ----------------\n{block}")
        text = "".join(lines)
    return text


# ----------------------------------------------------------------------------- finding papers

WORK_FIELDS = ("id,doi,display_name,publication_year,publication_date,type,"
               "primary_location,authorships,biblio")


def find_works(person: dict, start: str) -> list[tuple[dict, str]]:
    """(work, how_found) pairs; how_found is 'orcid' or 'extra'."""
    queries = []
    if person.get("orcid"):
        queries.append(("orcid", f"author.orcid:{person['orcid']}"))
    extra = [str(x).strip() for x in person.get("extra_openalex_ids") or [] if str(x).strip()]
    if extra:
        queries.append(("extra", "author.id:" + "|".join(extra)))
    found: dict[str, tuple[dict, str]] = {}
    for how, filt in queries:
        for page in range(1, 6):
            data = openalex("works", {
                "filter": f"{filt},from_publication_date:{start}",
                "per-page": 200, "page": page, "sort": "publication_date:desc", "select": WORK_FIELDS,
            })
            results = data.get("results") or []
            for w in results:
                wid = w.get("id")
                if wid and (wid not in found or how == "orcid"):
                    found[wid] = (w, how)
            if len(results) < 200:
                break
            time.sleep(0.3)
    return list(found.values())


def person_key(person: dict) -> str:
    return name_key(*split_name(person.get("name", "")))


def is_person(person: dict, given: str, family: str, orcid: str = "", oa_id: str = "") -> bool:
    if orcid and person.get("orcid") and orcid.rsplit("/", 1)[-1] == person["orcid"]:
        return True
    if oa_id and oa_id.rsplit("/", 1)[-1] in {str(x) for x in person.get("extra_openalex_ids") or []}:
        return True
    return name_key(given, family) == person_key(person)


def classify(work: dict, cr: dict | None, venue: str) -> str:
    oa_type = (work.get("type") or "").lower()
    cr_type = (cr or {}).get("type", "")
    doi = norm_doi(work.get("doi"))
    page = str((cr or {}).get("page") or (work.get("biblio") or {}).get("first_page") or "")
    v = venue.lower()
    if doi.startswith("10.48550/") or oa_type == "preprint" or cr_type == "posted-content":
        return "preprint"
    if "proceedings of meetings on acoustics" in v:
        return "conference"
    if "acoustical society of america" in v and (page[:1].upper() == "A" or oa_type == "conference-abstract"):
        return "abstract"  # ASA meeting abstracts have pages like A176
    if oa_type == "conference-abstract":
        return "abstract"
    if cr_type == "proceedings-article" or oa_type in ("conference-paper", "proceedings-article"):
        return "conference"
    if cr_type == "journal-article" or oa_type in ("article", "review", "letter"):
        return "journal"
    return "other"


def venue_of(work: dict, cr: dict | None) -> str:
    doi = norm_doi(work.get("doi"))
    if doi.startswith("10.48550/"):
        return "arXiv"
    if doi.startswith("10.21203/"):
        return "Research Square (preprint)"
    if cr:
        ct = cr.get("container-title") or []
        if ct:
            return clean_text(ct[0])
        if cr.get("type") == "posted-content":
            inst = ((cr.get("institution") or [{}])[0] or {}).get("name") or cr.get("publisher") or "Preprint"
            return f"{clean_text(inst)} (preprint)"
    src = ((work.get("primary_location") or {}).get("source") or {}).get("display_name")
    return clean_text(src)


def details_of(work: dict, cr: dict | None, typ: str) -> str:
    if typ == "preprint":
        return ""
    if cr:
        vol, issue = str(cr.get("volume") or ""), str(cr.get("issue") or "")
        pages = str(cr.get("article-number") or cr.get("page") or "")
    else:
        b = work.get("biblio") or {}
        vol, issue = str(b.get("volume") or ""), str(b.get("issue") or "")
        fp, lp = str(b.get("first_page") or ""), str(b.get("last_page") or "")
        pages = fp + (f"-{lp}" if lp and lp != fp else "")
    if not vol:
        return ""  # early access: volume and pages are not final yet
    issue = re.sub(r"[_ ]?supplement", " Suppl.", issue, flags=re.I).strip()
    first, _, last = pages.partition("-")
    if first and first == last:
        pages = first
    pages = pages.replace("-", "–")
    s = vol + (f"({issue})" if issue else "")
    if pages:
        s += f", {pages}"
    return clean_text(s)


def authors_of(work: dict, cr: dict | None, person: dict) -> tuple[list[str], list[str]]:
    """(formatted names, name keys). The tracked person is written as `show_as`."""
    people = []  # (given, family, orcid, openalex_id)
    if cr and cr.get("author"):
        for a in cr["author"]:
            if a.get("family"):
                people.append((a.get("given", ""), a["family"], a.get("ORCID", ""), ""))
            elif a.get("name"):
                people.append(("", a["name"], "", ""))
    else:
        for a in work.get("authorships") or []:
            raw = a.get("raw_author_name") or (a.get("author") or {}).get("display_name") or ""
            given, family = split_name(raw)
            au = a.get("author") or {}
            people.append((given, family, au.get("orcid") or "", au.get("id") or ""))
    names, keys = [], []
    # OpenAlex tells us which authorship is the tracked person; Crossref may only have the name.
    oa_hits = {name_key(*split_name(a.get("raw_author_name") or "")) for a in work.get("authorships") or []
               if is_person(person, "", "", (a.get("author") or {}).get("orcid") or "",
                            (a.get("author") or {}).get("id") or "")}
    for given, family, orcid, oa_id in people:
        k = name_key(given, family)
        if is_person(person, given, family, orcid, oa_id) or k in oa_hits:
            names.append(person.get("show_as") or short_name(given, family))
            keys.append(person_key(person))
        else:
            names.append(short_name(given, family))
            keys.append(k)
    if len(names) > 30:
        names = names[:29] + ["et al."]
    return names, keys


# ----------------------------------------------------------------------------- git and GitHub

def run(cmd: list[str], check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, input=input_text)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:4])} ... failed: {(r.stderr or r.stdout).strip()[:800]}")
    return r


def gh_json(args: list[str]):
    r = run(["gh", *args], check=False)
    if r.returncode != 0:
        log(f"(GitHub CLI: {' '.join(args[:3])} failed: {(r.stderr or '').strip()[:300]})")
        return None
    try:
        return json.loads(r.stdout or "null")
    except json.JSONDecodeError:
        return None


def marker_keys(body: str, marker: str = MARKER) -> set[str]:
    m = re.search(rf"<!--\s*{marker}:?([^>]*)-->", body or "")
    return {key_of(x) for x in m.group(1).split()} if m else set()


def bot_prs(state: str) -> list[dict]:
    """Pull requests from this check's branches (found by branch name, so a missing label doesn't matter)."""
    prs = gh_json(["pr", "list", "--state", state, "--limit", "200",
                   "--json", "number,url,body,headRefName,mergedAt,mergeable,title"]) or []
    return [p for p in prs if str(p.get("headRefName", "")).startswith(BRANCH_PREFIX)]


def file_at(ref: str, path: str) -> str:
    r = run(["git", "show", f"{ref}:{path}"], check=False)
    return r.stdout if r.returncode == 0 else ""


def read_suggested(text: str) -> set[str]:
    return {key_of(l.split("#")[0].strip()) for l in text.splitlines() if l.split("#")[0].strip()}


# ----------------------------------------------------------------------------- pull request text

def esc(s: str) -> str:
    """Text for the pull request description: no accidental @mentions or markup."""
    return str(s).replace("@", "@​").replace("<", "&lt;").replace("|", "\\|")


def pr_body(items: list[dict], skipped: list[str], all_keys: set[str], wiki_url: str) -> str:
    n = len(items)
    lines = [
        f"**{n} new publication{'s' if n != 1 else ''} found for the Publications page.** "
        "Please check them, then click **Merge pull request** at the bottom of this page. "
        "The website updates about a minute after merging.",
        "",
    ]
    for i, it in enumerate(items, 1):
        venue = f"*{esc(it['venue'])}*" + (f" {esc(it['details'])}" if it.get("details") else "")
        link = it.get("link", "")
        lines.append(f"{i}. **{esc(it['title'])}**  ")
        lines.append(f"   {esc(it['authors'])}  ")
        lines.append(f"   {venue} ({it['year']}), {it['type']}" + (f" · [{esc(it['link_text'])}]({link})" if link else "") + "  ")
        lines.append(f"   Found because: {esc(it['reason'])}" + ("  " if it.get("notes") else ""))
        for note in it.get("notes", []):
            lines.append(f"   ⚠️ {esc(note)}" + ("  " if note is not it["notes"][-1] else ""))
        lines.append("")
    lines += [
        "**If something is wrong**",
        "- **A paper doesn't belong** (for example, it's by someone else with the same name): open the "
        "**Files changed** tab, click **⋯** next to `_data/publications.yml`, then **Edit file**. Delete that "
        "paper's lines, from its `- year:` line down to the line before the next `- year:`, and click "
        "**Commit changes**. Then merge. A paper removed this way is not suggested again.",
        "- **None of them belong:** click **Close pull request**. They won't be suggested again.",
        "- **A typo, or the wrong type** (journal, conference, abstract, preprint): fix it the same way before "
        "merging. Titles were changed to sentence case automatically, so check names of people and materials.",
        "",
    ]
    if skipped:
        lines += ["<details><summary>Also seen, but not added</summary>", ""]
        lines += [f"- {esc(s)}" for s in skipped]
        lines += ["", "To add one of these, copy it into `_data/publications.yml` by hand.", "</details>", ""]
    lines += [
        f"Opened by the weekly publications check. How it works: [{wiki_url}]({wiki_url}). "
        f"Settings: `{SETTINGS_PATH}`.",
        "",
        f"<!-- {MARKER}: {' '.join(sorted(all_keys))} -->",
    ]
    return "\n".join(lines)


def describe_entry(e: dict) -> dict:
    link = f"https://doi.org/{e['doi']}" if e.get("doi") else e.get("url", "")
    return {
        "title": e.get("title", ""), "authors": e.get("authors", ""), "venue": e.get("venue", ""),
        "details": e.get("details", ""), "year": e.get("year", ""), "type": e.get("type", ""),
        "link": link, "link_text": e.get("doi") or e.get("url", ""),
        "reason": e.get("_reason", "earlier run of this check"), "notes": e.get("_notes", []),
    }


# ----------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="show what would change; push and open nothing")
    args = ap.parse_args()
    dry = args.dry_run

    settings = yaml.safe_load((ROOT / SETTINGS_PATH).read_text(encoding="utf-8")) or {}
    people = settings.get("people") or []
    start = str(settings.get("start_date") or (dt.date.today() - dt.timedelta(days=365)))
    contact = str(settings.get("contact_email") or "").strip()
    keep = KEEP_CAPS | {str(w) for w in settings.get("keep_capitalized") or []}
    skip = {key_of(str(x)) for x in settings.get("skip") or []}
    reviewers = [str(r).strip().lstrip("@") for r in settings.get("reviewers") or [] if str(r).strip()]
    site_url = str(settings.get("site_url") or "https://utacousticmems.github.io").rstrip("/")
    wiki_url = f"{site_url}/wiki/publication-updates/"
    for p in people:
        p["orcid"] = str(p.get("orcid") or "").strip().rsplit("/", 1)[-1]
        if p["orcid"] and not re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", p["orcid"]):
            log(f"Warning: '{p['orcid']}' does not look like an ORCID iD (0000-0000-0000-0000).")

    main_sha = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    main_text = file_at(main_sha, PUBS_PATH)
    main_entries = load_yaml_text(main_text)
    suggested = read_suggested(file_at(main_sha, SUGGESTED_PATH))

    # Pull requests from earlier runs
    open_prs = bot_prs("open")
    rejected: set[str] = set()
    for pr in bot_prs("closed"):
        if pr.get("mergedAt"):
            continue
        if SUPERSEDED in (pr.get("body") or ""):
            rejected |= marker_keys(pr.get("body"), SUPERSEDED)
        else:
            rejected |= marker_keys(pr.get("body"))
    for issue in bot_issues("closed"):
        if DONE not in (issue.get("body") or ""):
            rejected |= marker_keys(issue.get("body"))  # closed by a person: skip these papers

    mode, pr, branch_ref, newly_rejected = "new", None, main_sha, set()
    page_entries = list(main_entries)
    if open_prs:
        pr = open_prs[0]
        run(["git", "fetch", "--depth=1", "origin", f"+refs/heads/{pr['headRefName']}:refs/remotes/origin/{pr['headRefName']}"])
        branch_ref = f"origin/{pr['headRefName']}"
        branch_entries = load_yaml_text(file_at(branch_ref, PUBS_PATH))
        on_branch = Page(branch_entries).keys
        pr_keys = marker_keys(pr.get("body"))
        newly_rejected = {k for k in pr_keys if k not in on_branch}  # removed by a reviewer
        main_page = Page(main_entries)
        mergeable = pr.get("mergeable")
        for _ in range(3):
            if mergeable != "UNKNOWN":
                break
            time.sleep(5)
            mergeable = (gh_json(["pr", "view", str(pr["number"]), "--json", "mergeable"]) or {}).get("mergeable")
        stale = [k for k in pr_keys - newly_rejected if k in main_page.keys]
        if mergeable == "CONFLICTING" or stale:
            mode = "refresh"
            log(f"Pull request #{pr['number']} {'has a conflict' if mergeable == 'CONFLICTING' else 'repeats papers now on the page'}; replacing it with a fresh one.")
        else:
            mode = "append"
            page_entries += branch_entries
            suggested |= read_suggested(file_at(branch_ref, SUGGESTED_PATH))
            log(f"Pull request #{pr['number']} is still open; new papers, if any, will be added to it.")
    page = Page(page_entries)
    exclude = suggested | skip | rejected | newly_rejected

    # Find and format new papers
    items, skipped, missing_doi_links = [], [], []
    for person in people:
        pname = person.get("name", "?")
        works = find_works(person, start)
        log(f"OpenAlex: {len(works)} works for {pname} since {start}.")
        for work, how in sorted(works, key=lambda x: x[0].get("publication_date") or "", reverse=True):
            title0 = clean_text(work.get("display_name"))
            doi = norm_doi(work.get("doi"))
            if not doi:
                continue  # only papers with a DOI are handled automatically
            k = key_of(doi)
            label = f"{title0[:110]} ({doi})"
            if (work.get("type") or "").lower() in SKIP_TYPES or SKIP_TITLE_RE.match(title0):
                continue
            if k in page.keys or k in exclude:
                continue
            cr = None
            if not doi.startswith("10.48550/"):
                try:
                    cr = crossref_work(doi, contact)
                except Exception as err:  # Crossref down: fall back to OpenAlex details
                    log(f"Crossref lookup failed for {doi}: {err}")
                time.sleep(0.2)
            venue = venue_of(work, cr)
            typ = classify(work, cr, venue)
            raw_title = clean_text((cr.get("title") or [None])[0] if cr and cr.get("title") else title0)
            title = to_sentence_case(raw_title, keep)
            status, other = page.match(k, title, typ)
            if status == "same":
                if other is not None and not other.get("doi") and not other.get("url"):
                    missing_doi_links.append(
                        f"{other.get('title')} | page: {other.get('venue')} {other.get('details') or ''} "
                        f"({other.get('year')}) | DOI {doi}: {venue} {details_of(work, cr, typ)} "
                        f"({work.get('publication_year')})")
                continue
            names, keys = authors_of(work, cr, person)
            me = person_key(person)
            coauthors = [n for n, kk in zip(names, keys) if kk != me and kk in page.author_keys]
            if how == "extra" and not coauthors:
                skipped.append(f"{label}: no co-authors from the page, so probably another person named {pname}")
                continue
            notes = []
            if how == "orcid" and not coauthors:
                notes.append(f"None of the other authors appear on the page yet. Please check that this is {pname}'s paper.")
            if status == "version" and other is not None:
                notes.append(f"Already on the page as {TYPE_WORDS.get(other.get('type'), 'an entry')}: "
                             f"“{other.get('title')}”. If this is the newer version, you may want to remove the old entry.")
            if how == "orcid":
                reason = f"listed under {pname}'s ORCID iD in OpenAlex"
            else:
                reason = f"{pname}'s name, with co-authors already on the page ({', '.join(coauthors[:3])})"
            a = arxiv_id(doi)
            entry = {
                "year": int(work.get("publication_year") or start[:4]),
                "type": typ,
                "authors": ", ".join(names),
                "title": title,
                "venue": venue,
                "details": details_of(work, cr, typ),
                "doi": "" if a else doi,
                "url": f"https://arxiv.org/abs/{a}" if a else "",
                "_date": work.get("publication_date") or "",
                "_key": k,
                "_reason": reason,
                "_notes": notes,
            }
            items.append(entry)
            page.keys.add(k)  # do not add the same paper twice in one run

    log(f"New papers to suggest: {len(items)}")
    for e in items:
        log("\n" + entry_yaml(e).rstrip())
        for n in e["_notes"]:
            log(f"  note: {n}")
    if skipped:
        log("\nSeen but not added:")
        for s in skipped:
            log(f"- {s}")
    if missing_doi_links:
        log("\nOn the page without a DOI link (DOI found):")
        for s in missing_doi_links:
            log(f"- {s}")

    if not dry:
        keepalive()
    if dry:
        if items:
            log("\n--- Pull request text (dry run) ---\n")
            log(pr_body([describe_entry(e) for e in items], skipped, {e['_key'] for e in items}, wiki_url))
        log("\nDry run: nothing was pushed or opened.")
        return finish()

    if mode == "refresh":
        body = (pr.get("body") or "") + f"\n<!-- {SUPERSEDED}: {' '.join(sorted(newly_rejected))} -->"
        run(["gh", "pr", "edit", str(pr["number"]), "--body-file", "-"], check=False, input_text=body)
        run(["gh", "pr", "close", str(pr["number"]), "--comment",
             "The publications list changed since this was opened, so the weekly check is replacing it with "
             "a fresh pull request. Papers removed from this one stay skipped."], check=False)
        pr = None
    if mode == "append":
        close_bot_issues(f"The pull request with these papers is open now: {pr['url']}")
    if not items:
        log("Nothing new this week.")
        if not pr:
            close_bot_issues("Nothing is waiting for review any more: the papers are on the page or were skipped.")
        cleanup_branches(keep_branch=pr["headRefName"] if pr else None)
        return finish()

    # Write the changes on a branch
    run(["git", "config", "user.name", "github-actions[bot]"])
    run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"])
    if mode == "append":
        branch = pr["headRefName"]
        run(["git", "checkout", "-B", branch, branch_ref])
    else:
        branch = new_branch_name()
        run(["git", "checkout", "-B", branch, main_sha])
    pubs_file = ROOT / PUBS_PATH
    old_text = pubs_file.read_text(encoding="utf-8")
    new_text = insert_entries(old_text, items)
    check = load_yaml_text(new_text)
    if len(check) != len(load_yaml_text(old_text)) + len(items):
        raise RuntimeError("The edited publications.yml did not parse as expected; nothing was pushed.")
    pubs_file.write_text(new_text, encoding="utf-8")
    sug_file = ROOT / SUGGESTED_PATH
    sug_text = sug_file.read_text(encoding="utf-8") if sug_file.exists() else ""
    if sug_text and not sug_text.endswith("\n"):
        sug_text += "\n"
    for e in items:
        sug_text += f"{e['_key']}  # {e['_date']} {e['title'][:70]}\n"
    for k in sorted(newly_rejected - read_suggested(sug_text)):
        sug_text += f"{k}  # removed during review\n"
    for k in sorted(rejected - read_suggested(sug_text)):
        sug_text += f"{k}  # skipped: its pull request or issue was closed without merging\n"
    sug_file.write_text(sug_text, encoding="utf-8")
    run(["git", "add", PUBS_PATH, SUGGESTED_PATH])
    n = len(items)
    run(["git", "commit", "-m", f"Add {n} new publication{'s' if n != 1 else ''} found online"])
    run(["git", "push", "origin", f"HEAD:refs/heads/{branch}"])

    # The pull request lists every paper the branch adds, including earlier runs' papers
    final_entries = load_yaml_text(new_text)
    pr_keys = (marker_keys(pr.get("body")) if pr else set()) | {e["_key"] for e in items}
    shown = []
    by_key = {e["_key"]: e for e in items}
    for e in final_entries:
        ks = {key_of(e.get("doi"))} if e.get("doi") else set()
        if arxiv_id(e.get("url")):
            ks.add(f"arxiv:{arxiv_id(e.get('url'))}")
        hit = next((k for k in ks if k in pr_keys), None)
        if hit:
            shown.append(describe_entry(by_key.get(hit, e)))
    body = pr_body(shown, skipped, pr_keys, wiki_url)
    title = f"Add {len(shown)} new publication{'s' if len(shown) != 1 else ''} found online"
    if mode == "append":
        run(["gh", "pr", "edit", str(pr["number"]), "--title", title, "--body-file", "-"], check=False, input_text=body)
        log(f"Updated pull request #{pr['number']}: {pr['url']}")
    else:
        branch = open_pull_request(branch, title, body, reviewers)
    cleanup_branches(keep_branch=branch)
    return finish()


def new_branch_name() -> str:
    base = BRANCH_PREFIX + dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d-%H%M")
    name, n = base, 2
    while run(["git", "ls-remote", "--heads", "origin", f"refs/heads/{name}"], check=False).stdout.strip():
        name, n = f"{base}-{n}", n + 1
    return name


def open_pull_request(branch: str, title: str, body: str, reviewers: list[str]) -> str:
    """Opens the pull request, or an issue with a one-click link if GitHub won't allow that.
    Returns the branch that now holds the papers."""
    run(["gh", "label", "create", LABEL, "--color", "1D76DB", "--force",
         "--description", "Opened by the weekly publications check"], check=False)
    default = (gh_json(["repo", "view", "--json", "defaultBranchRef"]) or {}).get("defaultBranchRef", {}).get("name") or "main"
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(body)
        body_file = f.name
    r = run(["gh", "pr", "create", "--base", default, "--head", branch, "--title", title,
             "--body-file", body_file, "--label", LABEL], check=False)
    if r.returncode != 0 and "label" in (r.stderr or "").lower():
        r = run(["gh", "pr", "create", "--base", default, "--head", branch, "--title", title,
                 "--body-file", body_file], check=False)
    if r.returncode == 0:
        url = r.stdout.strip().splitlines()[-1]
        log(f"Opened pull request: {url}")
        close_bot_issues(f"The pull request with these papers is open now: {url}")
        for who in reviewers:
            rr = run(["gh", "pr", "edit", url, "--add-reviewer", who], check=False)
            if rr.returncode != 0:
                log(f"(Could not ask {who} to review: {rr.stderr.strip()[:200]})")
        return branch
    err = (r.stderr or "").strip()
    log(f"Could not open the pull request: {err[:400]}")
    # Usually means "Allow GitHub Actions to create and approve pull requests" is off (often locked by the
    # organization). The branch is pushed, so a person can open the pull request with one click instead.
    # The papers move to one fixed branch, so the link in an older email still works and shows the latest list.
    if branch != REVIEW_BRANCH and run(["git", "push", "--force", "origin", f"HEAD:refs/heads/{REVIEW_BRANCH}"],
                                       check=False).returncode == 0:
        run(["git", "push", "origin", "--delete", branch], check=False)
        branch = REVIEW_BRANCH
    pr_text = body
    if len(urllib.parse.quote(pr_text)) > 6000:  # keep the link short enough for browsers
        pr_text = ("Papers found by the weekly publications check. They are listed in the issue "
                   f"“{ISSUE_TITLE}” and under **Files changed**.\n\n" + body[body.index(f"<!-- {MARKER}"):])
    compare = (f"https://github.com/{REPO}/compare/{default}...{urllib.parse.quote(branch, safe='/')}"
               f"?expand=1&labels={LABEL}&title={urllib.parse.quote(title)}&body={urllib.parse.quote(pr_text)}")
    org = REPO.split("/")[0] or "the"
    issue_body = (
        "The weekly publications check found new papers for the Publications page.\n\n"
        "**To add them (about 2 minutes):**\n"
        f"1. [Open the pull request page]({compare}).\n"
        "2. Click the green **Create pull request** button.\n"
        "3. Check the papers (listed below, and under **Files changed**), then click **Merge pull request**.\n\n"
        "To leave a paper out, delete it under **Files changed** before merging; it won't be suggested again. "
        "To skip them all, close this issue. The weekly check closes it by itself once the papers are merged.\n\n"
        "**Why the extra step:** GitHub doesn't let the check open the pull request itself. To change that, an owner "
        f"of the {org} organization opens the organization's **Settings → Actions → General**, ticks **Allow GitHub "
        "Actions to create and approve pull requests** under **Workflow permissions**, and clicks **Save**. Then a "
        "repository admin ticks the same box in this repository's **Settings → Actions → General**.\n\n"
        f"<details><summary>The papers</summary>\n\n{body}\n</details>\n"
    )
    issues = bot_issues()
    if issues:
        num = str(issues[0]["number"])
        old_keys = marker_keys(issues[0].get("body") or "")
        run(["gh", "issue", "edit", num, "--body-file", "-"], check=False, input_text=issue_body)
        if marker_keys(body) - old_keys:
            run(["gh", "issue", "comment", num, "--body",
                 "More papers were found this week. The list and the link above are updated."], check=False)
        log(f"Updated issue #{num} with the papers and a fresh link.")
        return branch
    rr = run(["gh", "issue", "create", "--title", ISSUE_TITLE, "--label", LABEL, "--body-file", "-"],
             check=False, input_text=issue_body)
    if rr.returncode != 0:
        rr = run(["gh", "issue", "create", "--title", ISSUE_TITLE, "--body-file", "-"], check=False, input_text=issue_body)
    url = (rr.stdout or "").strip().splitlines()[-1] if rr.returncode == 0 and rr.stdout.strip() else ""
    log(f"Opened issue {url}" if url else f"Could not open an issue either: {(rr.stderr or '').strip()[:300]}")
    for who in reviewers if url else []:
        run(["gh", "issue", "edit", url, "--add-assignee", who], check=False)
    return branch


def bot_issues(state: str = "open") -> list[dict]:
    """Issues this check opened because it could not open a pull request."""
    issues = gh_json(["issue", "list", "--state", state, "--limit", "100", "--json", "number,title,body"]) or []
    return [i for i in issues if i.get("title") == ISSUE_TITLE]


def close_bot_issues(comment: str) -> None:
    for i in bot_issues():
        num = str(i["number"])
        run(["gh", "issue", "edit", num, "--body-file", "-"], check=False,
            input_text=(i.get("body") or "") + f"\n<!-- {DONE} -->\n")
        run(["gh", "issue", "close", num, "--comment", comment], check=False)
        log(f"Closed issue #{num}.")


def cleanup_branches(keep_branch: str | None) -> None:
    """Delete branches of this check whose pull requests are closed or merged."""
    r = run(["git", "ls-remote", "--heads", "origin", f"refs/heads/{BRANCH_PREFIX}*"], check=False)
    open_heads = {p.get("headRefName") for p in bot_prs("open")}
    for line in (r.stdout or "").splitlines():
        ref = line.split("\t")[-1].removeprefix("refs/heads/")
        if ref and ref != keep_branch and ref not in open_heads:
            run(["git", "push", "origin", "--delete", ref], check=False)


def keepalive() -> None:
    """GitHub pauses scheduled workflows after 60 days without commits. Re-enabling resets that."""
    if REPO:
        run(["gh", "api", "-X", "PUT", f"repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/enable"], check=False)


def finish() -> int:
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("```\n" + "\n".join(OUT) + "\n```\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as err:
        log(f"\nThe publications check stopped: {err}")
        log("Nothing was changed on the website. If OpenAlex says an API key is needed, add a free key as the "
            "repository secret OPENALEX_API_KEY (see the wiki page 'Automatic publication updates').")
        finish()
        raise

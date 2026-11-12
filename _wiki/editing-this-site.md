---
title: Editing this site
category: Getting started
order: 2
summary: How to add a paper, a person, a news item or a wiki page. No coding needed.
authors: [Hall Group]
updated: Nov 2026
---

Everything on this site lives in a GitHub repository. You can edit any of it in the browser: open the file on GitHub, click the **pencil** icon, make your change, and click **Commit changes**. The site rebuilds itself in about a minute.

## Where things live

| To change… | Edit this file |
|---|---|
| A paper | `_data/publications.yml` |
| A person, or move someone to alumni | `_data/people.yml` |
| A news item | `_data/news.yml` |
| A research area | `_data/research.yml` |
| A wiki page | `_wiki/<page-name>.md` |
| Home, Join, Visit pages | `index.html`, `join.html`, `visit.html` |
| Images | `assets/img/` (people photos in `assets/people/`, wiki images in `assets/wiki/`) |

## Add a paper
Copy an existing entry in `_data/publications.yml`, paste it at the top of the right year, and change the fields:

```yaml
- year: 2027
  type: journal          # journal | conference | abstract | preprint | patent
  authors: A. Student, B. Student, N. A. Hall
  title: Title in sentence case
  venue: Journal name
  details: 12(3), 456    # volume(issue), pages or article number
  doi: 10.xxxx/xxxxx     # or url: https://...
  cover: Cover article, March 2027   # optional
  highlight: true        # optional: show under its research area
```

YAML is picky about indentation (two spaces) and about colons inside text. If a title contains a colon, wrap the whole title in double quotes.

## Add yourself
In `_data/people.yml`, add an entry under `phd:` (or `postdocs:` / `undergrads:`). For a photo, upload a square JPG (at least 400 × 400 px) to `assets/people/` and set `photo: yourname.jpg`.

When you graduate, move your entry to `alumni:` and fill in `year:` and `now:`.

## Add a news item
Add an entry at the **top** of `_data/news.yml`:

```yaml
- date: 2027-01-15
  title: Short headline
  text: One or two sentences.
  link: https://doi.org/...   # optional
  tag: Paper                  # Paper, Cover, Award, Talks, Recruiting…
```

## Write a wiki page
1. Copy `_templates/wiki-page.md` into `_wiki/` and rename it, e.g. `_wiki/ldv-setup.md` (lowercase, hyphens). That name becomes the URL: `/wiki/ldv-setup/`.
2. Fill in the header: `title`, `category` (must match one in `_data/wiki_categories.yml`), `order`, `summary`, `authors`, `updated`.
3. Write in Markdown. Put images in `assets/wiki/` and reference them as {% raw %}`![caption]({{ '/assets/wiki/your-image.jpg' | relative_url }})`{% endraw %}.

**Keep it public-safe.** No account numbers, P-card details, vendor contacts, door codes, export-controlled or NDA material, or unpublished results. Those go on the internal wiki.

## Preview locally (optional)
```bash
bundle install
bundle exec jekyll serve
# open http://localhost:4000
```

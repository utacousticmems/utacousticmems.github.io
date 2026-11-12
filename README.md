# UT Acoustic MEMS Group (Hall Lab) website

Public website and group wiki for the UT Acoustic MEMS Group, also known as the Hall Lab (Prof. Neal A. Hall, UT Austin ECE).
Built with [Jekyll](https://jekyllrb.com/) and hosted free on GitHub Pages.

## Put it online (one-time, about 10 minutes)

1. **Create a GitHub organization** for the group, e.g. `utacousticmems` (github.com → your avatar → *Your organizations* → *New organization* → Free). Add Dr. Hall and current students as owners or members, so the site outlives any one student.
2. **Create a public repository** in that organization named exactly `utacousticmems.github.io`. That name gives the site the address `https://utacousticmems.github.io` with no extra setup.
   - If you use another name (e.g. `hall-group`), the address becomes `https://<org>.github.io/hall-group/`, and you must set `baseurl: /hall-group` in `_config.yml`.
3. **Upload these files.** Easiest: on the new repo page click *uploading an existing file* and drag in everything in this folder (including the hidden-looking `_data`, `_layouts`, `_wiki` folders). Or with git:
   ```bash
   git init && git add . && git commit -m "Group website"
   git branch -M main
   git remote add origin https://github.com/utacousticmems/utacousticmems.github.io.git
   git push -u origin main
   ```
4. **Turn on Pages:** repo → *Settings* → *Pages* → *Build and deployment* → Source: *Deploy from a branch* → Branch: `main` / `(root)` → *Save*. The site is live in 1–2 minutes.
5. **Set `repo_url`** in `_config.yml` to the repo's URL so the "Edit on GitHub" links appear.
6. **Point the old site here.** In the old Google Site, replace the home page with a short note and link to the new address (Google Sites cannot do a true redirect).
7. Optional: a custom domain (e.g. a UT subdomain) can be added later under *Settings → Pages → Custom domain*.

## Everyday editing (no coding)

Open a file on GitHub, click the pencil icon, edit, *Commit changes*. The site rebuilds in about a minute.

| To change… | Edit |
|---|---|
| Papers | `_data/publications.yml` |
| People, alumni, "where our PhDs go" | `_data/people.yml` |
| News | `_data/news.yml` (newest at top) |
| Research areas | `_data/research.yml` |
| Wiki pages | `_wiki/*.md` (start from `_templates/wiki-page.md`) |
| Wiki sections | `_data/wiki_categories.yml` |
| Home / Join / Visit text | `index.html`, `join.html`, `visit.html` |
| Images | `assets/img/`, people photos `assets/people/`, wiki images `assets/wiki/` |

Full how-to with examples: the wiki page *Editing this site* (`_wiki/editing-this-site.md`).

**Keep it public-safe.** This repo and site are public. No P-card or account details, vendor contacts, door codes, NDA or export-controlled material, proposal text, or unpublished results. Those go in the internal wiki.

## Preview on your computer (optional)

```bash
bundle install          # first time only; needs Ruby
bundle exec jekyll serve
# open http://localhost:4000
```

## What's where

```
_config.yml              site settings (title, baseurl, repo_url)
_data/                   people, publications, news, research areas, wiki sections
_wiki/                   one Markdown file per wiki page
_layouts/, _includes/    page templates (rarely need changes)
assets/css/site.css      all styling (colors and fonts at the top; SF Pro on Apple devices, Inter elsewhere)
assets/img/              research photos and journal covers
assets/video/            recruiting film (compressed, 12 MB) and poster frame
```

## To do

- [ ] Add photos for people (`assets/people/`, square JPG, at least 400 px).
- [ ] Fill in alumni graduation years and current positions in `_data/people.yml`.
- [ ] Add 2020–2022 publications.
- [ ] Re-upload the photos and screenshots from the old wiki pages (DSE, FIJI ALD, mask design, RIE) to `assets/wiki/`.
- [ ] Confirm the FIJI ALD thickness numbers (the old page's numbers disagree with each other).

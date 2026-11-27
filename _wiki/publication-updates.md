---
title: Automatic publication updates
category: Getting started
order: 3
description: How new papers reach the Publications page by themselves, and how to review them.
authors: [UT Acoustic MEMS Group]
updated: Nov 2026
---

Nobody has to watch for new papers. Every Monday morning a small program in this site's GitHub repository looks for new papers by Prof. Hall and suggests them as a **pull request**. A person checks the list and clicks **Merge**. Nothing goes live before that.

## How it finds papers
It asks [OpenAlex](https://openalex.org), a free index that picks up every new DOI from publishers, plus arXiv and Research Square preprints. It finds Prof. Hall's papers through his [ORCID iD](https://orcid.org/0000-0001-5237-8927), so papers by other people named Neal Hall are left out. Prof. Hall is an author on every group paper, so he is the only person it needs to track.

For each new paper it:

1. skips it if it is already on the [Publications page]({{ '/publications/' | relative_url }}) (same DOI, arXiv number or title), was suggested before, or is on the skip list;
2. writes an entry in the same format as the others in `_data/publications.yml`: authors as initials and last name, the title in sentence case, and the journal, volume, issue and pages from Crossref, the DOI registry;
3. puts all new entries at the top of their year in one pull request called **Add N new publications found online**, and asks the reviewers listed in the settings to look at it. GitHub emails them.

If last week's pull request is still open, new papers are added to it instead of starting another one.

## Review a pull request (about 2 minutes)
1. Open the pull request from the email, or from the repository's **Pull requests** tab.
2. Read the list. Each paper says why it was picked up, and ⚠️ marks one that needs a closer look, such as a paper with no co-authors from the group, or the journal version of a preprint that is already on the page.
3. **All good:** click **Merge pull request**, then **Confirm merge**. The page updates about a minute later.
4. **One paper doesn't belong:** open the **Files changed** tab, click **⋯** next to `_data/publications.yml`, then **Edit file**. Delete that paper's lines, from its `- year:` line down to the line before the next `- year:`, click **Commit changes**, then merge. It won't be suggested again.
5. **None of them belong:** click **Close pull request**. They won't be suggested again.

Before merging you can also fix a typo, change the type (`journal`, `conference`, `abstract`, `preprint`), or add `highlight: true` or a `cover:` badge, the same way as in step 4. Titles are changed to sentence case automatically, so check names of people, places and materials.

## If you get an issue instead of a pull request
GitHub lets the program open pull requests only if a setting allows it, and in the utacousticmems organization that setting is locked. Until it is turned on, the program opens an issue called **New publications found: please review** instead, assigned to the reviewers:

1. Open the issue and click **Open the pull request page**.
2. Click the green **Create pull request** button.
3. Review the pull request as above, then merge it.

To skip all the papers, close the issue. The program closes the issue by itself once the papers are merged. The link always shows the latest list, so the link in an older email still works.

To turn the setting on, an owner of the utacousticmems organization opens the organization's **Settings → Actions → General**, ticks **Allow GitHub Actions to create and approve pull requests** under **Workflow permissions**, and clicks **Save**. Then a repository admin ticks the same box in this repository's **Settings → Actions → General**. After that, pull requests arrive directly.

## What it doesn't do
- **Papers without a DOI**, such as most patents and theses, still need to be added by hand. See [Editing this site]({{ '/wiki/editing-this-site/' | relative_url }}).
- **Missed papers.** Now and then OpenAlex doesn't connect a paper to Prof. Hall (the Transducers 2025 paper is one). Add those by hand too.
- **Older papers.** It only looks at papers published on or after the start date in the settings.
- It never changes or removes entries that are already on the page.

## Settings
They are in `.github/publications-bot/settings.yml`. Open it on GitHub, click the pencil icon, edit and commit.

| Setting | What it does |
|---|---|
| `people` | Whose papers to look for: a name and an ORCID iD. |
| `start_date` | Only papers published on or after this date are suggested. |
| `reviewers` | GitHub accounts asked to review each pull request (or assigned the issue, see above). |
| `skip` | Papers never to suggest: a DOI, or `arXiv:NUMBER` for an arXiv preprint. |
| `keep_capitalized` | Extra words to keep capitalized when titles are changed to sentence case. |

`already-suggested.txt` in the same folder is the program's memory of what it has suggested. You don't need to edit it.

## Run it now
In the repository, open **Actions**, then **Weekly publications check**, then **Run workflow**. Tick **Only show what would be added** to try it without opening a pull request. Each run's page shows a short report of what it found and what it skipped.

## If something stops working
- **An issue appeared instead of a pull request:** see [If you get an issue instead of a pull request](#if-you-get-an-issue-instead-of-a-pull-request).
- **GitHub paused the weekly run:** GitHub pauses scheduled runs after 60 days without any change to the repository. The program tries to prevent this. To restart it, open **Actions → Weekly publications check** and click **Enable workflow**.
- **A run failed with an OpenAlex error about an API key:** get a free key at [openalex.org](https://openalex.org) (sign up, then **Settings → API key**), and add it in the repository under **Settings → Secrets and variables → Actions → New repository secret**, named `OPENALEX_API_KEY`.

The program itself is `.github/publications-bot/update_publications.py`, and the schedule is in `.github/workflows/publications-bot.yml`.

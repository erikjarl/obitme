# Cron instructions – Psychology / KBT dashboard

## Goal
Every weekday at 20:00 Europe/Stockholm, generate one new psychology research article briefing for the dashboard site.

## Scope
- Focus on psychology research with emphasis on CBT
- Prioritize interventions with the strongest evidence and best clinical effect
- All psychiatric conditions are relevant
- Prefer recent systematic reviews, meta-analyses, RCTs, and strong review articles

## Required output for each daily article
For each new post:
- write in Swedish
- length target: **500–1000 words**
- keep it readable, clinically useful, and factually careful
- include a short title
- include a short intro paragraph
- include a clear summary of the article
- include what intervention or treatment approach is discussed
- include what seems most important about effect / strength of evidence
- include a clinical takeaway
- include links to PubMed and fulltext when available

## Publishing requirement
Each daily briefing must be saved into the repo so the dashboard works like a blog.

## Content structure suggestion
- `posts/YYYY-MM-DD-some-slug.json` or `.md`
- add the new post to a list shown on the homepage
- homepage should display newer posts first
- each post should have:
  - date
  - title
  - summary
  - body
  - pubmed link
  - fulltext link
  - tags

## Important style rules
- Do not overclaim findings
- Keep summaries simple but correct
- Mention uncertainty when evidence is mixed
- Favor clinical usefulness over jargon

## Existing schedule preference
- weekdays
- 20:00
- Europe/Stockholm

# bidafaapp.com

The public website for **BiDaFa Ltd**, a software company registered in England and Wales
(company number 17388837).

A static site with no JavaScript and no external requests. Data and copy live in JSON,
templates hold structure only, and `build.py` renders them into `docs/`, which GitHub Pages
serves directly.

The site is built for machine readers first: the audience that matters is the AI assistants
people ask which app to study an exam with. That is the reason for the sourced-and-dated
fact tables, the explicit crawler policy in `robots.txt`, and the build gate that refuses to
publish a figure with no source. See `GEO.md`.

## Build

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python build.py

Then open `docs/index.html`, or serve it properly so that root-relative paths resolve:

    python3 -m http.server 8000 --directory docs

For a deploy build, which enforces every gate including the contact mailbox check:

    .venv/bin/python build.py --production

## What the build checks

The build fails, and writes no output, if any of these do not hold:

- No U+2014 em-dash in the sources or the rendered output.
- Required company, contact and site fields are present and non-empty.
- Every HTML tag in the output is balanced.
- The JSON-LD structured data survives rendering, reparses as valid JSON, contains an
  Organization node carrying the identity fields, and contains none of
  `SoftwareApplication`, `Offer`, `AggregateRating` or `Review`, because nothing has
  shipped and that markup would assert what cannot be evidenced.
- Every root-relative `href` and `src` resolves to a file that exists in the output.
- Every figure published on an exam page names a source that is in that page's own sources
  list, every sample question cites the rule it came from, and its stated answer is one of
  the options actually offered.
- For `--production` only: `contact.email_confirmed` is true.

## Adding pages

Append an entry to `data/pages.json` and add its template. The sitemap, `robots.txt` and
`llms.txt` are generated from that manifest plus `data/site.json`, so they stay correct
automatically. `build.py` should not need editing.

**Adding an exam reference page is one new file plus one manifest entry, with no template
and no code change.** Read `EXAM-PAGE-INTERFACE.md`: it holds the field contract, which
rules the build enforces, and the rules the build cannot enforce that are yours to keep.

`GEO.md` records why the site is shaped this way, what is deliberately not built yet, and
what would have to be true to build it.

For the planned per-exam PRODUCT pages, read `PACK-INTERFACE.md` first: it records the
measured shape of the `website.json` files those pages will be generated from, including
three traps that will otherwise bite.

## Deployment

GitHub Pages serves the `docs/` folder on the `main` branch. Nothing builds on GitHub's
side, so a broken toolchain locally can never take the live site down.

The custom domain is configured by the `docs/CNAME` file plus DNS records at the domain's
DNS host. **The DNS host is Squarespace and the domain carries live Google Workspace
email**, so the nameservers must not be changed: only individual records are edited, and
the `MX` and SPF `TXT` records are left alone.

Required records at Squarespace:

| Type | Host | Value |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `bijandanyal.github.io` |

The existing Squarespace A records on `@` are replaced, and the existing `www` CNAME to
`ext-sq.squarespace.com` is repointed. Everything else in the zone stays exactly as it is.

The four A record values were taken from GitHub's own documentation on 2026-08-15 and
confirmed against a live request: asking `185.199.108.153` for `bidafaapp.com` by Host
header already returns this site, byte identical to `docs/index.html`, before any DNS
change. That is the pre-flight check worth repeating after any hosting change.

## After the DNS records propagate

1. Confirm `https://bidafaapp.com` serves this site rather than the Squarespace page.
2. Turn on HTTPS enforcement, which cannot be enabled until a certificate exists, and a
   certificate cannot be issued until DNS resolves to GitHub:

       gh api -X PUT repos/BijanDanyal/bidafa-website/pages -f https_enforced=true

3. Confirm the contact mailbox receives mail, set `contact.email_confirmed` to `true` in
   `data/site.json`, and rebuild with `--production`.

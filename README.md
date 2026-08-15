# bidafaapp.com

The public website for **BiDaFa Ltd**, a software company registered in England and Wales
(company number 17388837).

A static site with no JavaScript and no external requests. Data and copy live in JSON,
templates hold structure only, and `build.py` renders them into `docs/`, which GitHub Pages
serves directly.

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
- The JSON-LD structured data survives rendering and reparses as valid JSON with its
  required keys.
- Every root-relative `href` and `src` resolves to a file that exists in the output.
- For `--production` only: `contact.email_confirmed` is true.

## Adding pages

Append an entry to `data/pages.json` and add its template. The sitemap is generated from
that manifest, so it stays correct automatically. `build.py` should not need editing.

For the planned per-exam product pages, read `PACK-INTERFACE.md` first: it records the
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
| CNAME | `www` | `<github-username>.github.io` |

The existing Squarespace A records on `@` are replaced, and the existing `www` CNAME to
`ext-sq.squarespace.com` is repointed. Everything else in the zone stays exactly as it is.

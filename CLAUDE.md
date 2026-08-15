# CLAUDE.md - bidafa-website

The public website for BiDaFa Ltd, at `bidafaapp.com`. Separate repo on purpose: it is
public, it is deployed, and it must never be able to reach into `exam-factory` or
`exam-app`.

## Iron rules (never break)

1. **No fabricated claims.** Never state a download count, a user count, a testimonial, a
   rating, an award, a partner, or a shipped product that does not exist and cannot be
   evidenced. This is the factory's cardinal sin rule applied to public marketing copy,
   where it matters most, because here a false claim is visible to Apple, to customers and
   to a regulator rather than only to us. If a number cannot be sourced, it does not go on
   the page.
2. **No em-dashes (U+2014)** in any file, deliverable or internal. Use commas, colons or
   hyphens. This is ENFORCED, not merely documented: `build.py` scans both the sources and
   the rendered output and fails the build. Do not weaken the check to make a build pass.
   Note that a comment or detector that quotes the banned character reintroduces it, which
   is why `build.py` refers to it by codepoint.
3. **No prose in templates.** Every sentence lives in `data/site.json`. A template may
   contain structure, never copy. This is what makes the future per-exam pages a data
   problem rather than a rewrite.
4. **BiDaFa Ltd does not claim the RiverMap apps.** The exam apps authored in
   `exam-factory` ship under a different developer account and a different brand. Until
   BiDaFa self-publishes its own app, the site says its first apps are in development, and
   it names no product. Do not "improve" the copy by borrowing that catalogue's credibility.
5. **The legal footer is a legal requirement, not decoration.** A UK limited company must
   disclose its registered name, company number, place of registration and registered
   office. Those values come from the Companies House public register and must match it
   exactly. Re-verify against the register before changing any of them.
6. **Nothing builds on GitHub's side.** `docs/` holds pre-built output and is committed.
   GitHub Pages serves those files directly. Do not introduce a build action or a Jekyll
   dependency: a toolchain failure on the author's machine must never be able to take the
   live site down.

## The honest-count rule (governs the future per-exam pages)

When product pages are generated from a pack's `website.json`, **every bank-size figure
states the HONEST count, never a combined total that includes top-up filler.** The
reasoning, recorded in `exam-factory/docs/dev-terminal-machinery-queue.md` under the
2026-07-27 enforcement redesign, is that the artifact ships before anyone decides whether
to publish the filler, so the number has to be true under both branches, and the honest
count is the only number that is. It therefore fails safe: if filler is published the page
understates, which costs a little search ranking and lies to nobody. Any derived total is
derived from the honest count.

See `PACK-INTERFACE.md` for the measured shape of `website.json`.

## Layout

    data/site.json      every fact and every line of copy
    data/pages.json     page manifest; sitemap is generated from it
    templates/          Jinja2, autoescaped, structure only
    assets/             one stylesheet, one favicon, no fonts, no JavaScript
    build.py            renders data + templates into docs/, then gates the output
    docs/               BUILD OUTPUT, committed, served by GitHub Pages. Never hand-edit.

## Build

    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python build.py              # preview
    .venv/bin/python build.py --production # deploy build, enforces every gate

`--production` additionally refuses to build while `contact.email_confirmed` is false, so
an unverified contact address cannot reach the live site.

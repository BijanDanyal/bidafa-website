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

## The two pages the app stores require

`/privacy/` and `/support/` are not marketing pages. Apple requires a link to a privacy
policy and to a support page on every App Store listing, so a broken or missing one is a
submission blocker, and Google Play asks for the same. They are therefore load bearing in
the same way the legal footer is.

Three things about them are decisions, not accidents:

1. **They describe apps that do not exist yet, and they say so.** Each carries a status
   note stating that no BiDaFa app has been released and that the app sections apply from
   the day the first one ships. Iron rules 1 and 4 do not get suspended because a store
   form wants a policy. Delete those notes in the same change that ships a real app.
2. **The support page publishes no target reply time.** Bijan chose this on 2026-09-09,
   having been offered 5, 2 and 1 working day: a stated deadline he cannot always keep
   would be exactly the unevidenceable claim iron rule 1 exists to stop. Do not add one
   back without asking him.
3. **The registered details on the privacy page are rendered from the `company` block**,
   never retyped as prose, so they cannot drift away from the Companies House record that
   iron rule 5 pins them to.

Both pages render from `templates/document.html`, which carries structure only: hero,
sections of paragraphs, ordered steps, bullet points, and a definition list built from the
`company` block. A further policy page is an entry in `data/pages.json` plus a block in
`data/site.json`, with no new template.

## A date a page states about itself is gated

`build.py` checks every `effective_on` and `checked_on` in a page's data: it must be a real
YYYY-MM-DD date, it must not be in the future, and where a human readable twin such as
`effective_on_human` exists the two must agree on the year. The effective date of a privacy
policy is the most consequential date on the site, because users and store reviewers rely
on it to know which version binds them, and nothing else in the build would notice a typo.

`footer.links` is a required field for the same reason: `base.html` renders it on every
page, and it holds the two URLs a store listing points at, so its absence must fail as a
sentence naming the field rather than as a Jinja traceback.

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
    templates/document.html  reusable policy page: privacy, support, and the next one
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

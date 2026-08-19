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

## The audience is the machine (locked by Bijan 2026-08-19)

The site exists so that an AI assistant asked "what app should I use to study for exam X"
can name ours and prove why. Bijan's direction, verbatim: build it *"100% for the AI's"*,
and treat human readability as a concern only where it also serves that. Do not spend
effort on visual polish. Do spend it on sourced facts, extractable structure, correct
markup and crawler access.

Two consequences that are easy to get backwards:

1. **Do not make it hostile to humans either.** Assistants send real people to the site
   with tracked links, and thin machine-bait content is a documented reason assistants
   withhold a recommendation. Plain, dense and factual satisfies both. Ugly is fine;
   worthless is not.
2. **The honesty rule is the growth strategy, not a tax on it.** Asked independently, all
   three assistants named unverifiable superlatives, invented counts, fake freshness dates
   and self-asserted ratings as reasons they would NOT recommend an app. Iron rule 1 is
   therefore load bearing for the commercial goal, not merely for ethics. `GEO.md` records
   the evidence.

## What the build now refuses to publish

Beyond the gates already listed, `build.py` enforces two rules that exist to keep the above
true when nobody is watching:

- **A figure with no source is not publishable.** Every entry in an exam page's `stats`
  must cite an `id` present in that page's own `sources` list, every sample question must
  carry the rule it was drawn from, and its stated answer must be one of the options it
  actually offers. `checked_on` must be a real date and must not be in the future.
- **Product markup is blocked while there is no product.** The JSON-LD gate fails the build
  if `SoftwareApplication`, `MobileApplication`, `Offer`, `AggregateRating` or `Review`
  appears in the graph. Remove that block only in the same change that ships a real app,
  and only for values that can be evidenced.

**Do not prune `crawlers.agents` in `data/site.json` casually.** Each named agent is the
documented lever for one assistant's visibility, and dropping one is a decision to become
invisible to that assistant, which is silent from our side and total from theirs.

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

    data/site.json      every fact and every line of copy, plus labels and crawler policy
    data/pages.json     page manifest; sitemap, robots.txt and llms.txt come from it
    data/exams/*.json   one file per exam reference page. See EXAM-PAGE-INTERFACE.md
    templates/          Jinja2, autoescaped, structure only
    assets/             one stylesheet, one favicon, no fonts, no JavaScript
    build.py            renders data + templates into docs/, then gates the output
    docs/               BUILD OUTPUT, committed, served by GitHub Pages. Never hand-edit.

    GEO.md              why the site is shaped this way, and what is NOT built yet
    EXAM-PAGE-INTERFACE.md   how to add an exam: the field contract and the gates
    PACK-INTERFACE.md   the measured shape of a pack's website.json, for future product pages

## Build

    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python build.py              # preview
    .venv/bin/python build.py --production # deploy build, enforces every gate

`--production` additionally refuses to build while `contact.email_confirmed` is false, so
an unverified contact address cannot reach the live site.

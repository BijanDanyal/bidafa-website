# The pack interface: `website.json`

The future per-exam product pages on this site are generated from each exam pack's
`website.json` file, produced by the `exam-factory` pipeline. This note records the shape
of that file **as measured**, not as assumed, so whoever builds the generator starts from
the real contract.

Measured 2026-08-15 across all **48** packs in `exam-factory/packs/*/website.json`.

## Field coverage

| Field | Present in | Notes |
|---|---|---|
| `slug` | 48 / 48 | URL slug for the product page |
| `configSlug` | 48 / 48 | Internal pack id, e.g. `ca-sg-mb` |
| `country` | 48 / 48 | |
| `title` | 48 / 48 | |
| `seoTitle` | 48 / 48 | Currently carries the RiverMap brand. Must be rewritten for BiDaFa, never copied |
| `seoDescription` | 48 / 48 | Free prose. Subject to the honest-count rule |
| `eyebrow` | 48 / 48 | |
| `heroSub` | 48 / 48 | Free prose. Subject to the honest-count rule |
| `examHeading` | 48 / 48 | |
| `examProse` | 48 / 48 | List. See the heterogeneity warning below |
| `specRows` | 48 / 48 | List of `{dt, dd}` |
| `features` | 48 / 48 | List of `{index, h, p}`. Subject to the honest-count rule |
| `faq` | 48 / 48 | List of `{q, a}`. Subject to the honest-count rule |
| `disclaimer` | 48 / 48 | |
| `datePublished` | 48 / 48 | |
| `dateModified` | 48 / 48 | |
| `samples` | 47 / 48 | List of `{tag, q, opts, correct, note}`; `sourceRef` on only 5 |
| `store` | 15 / 48 | OPTIONAL. A generator must not assume it |
| `title_long` | 2 / 48 | OPTIONAL. Rare |

## Three traps a generator has to handle

1. **`examProse` items are NOT a uniform record.** Some carry only `p`. Others carry `h`,
   `p` and a `ul` list. Iterating as though every item has the same keys will drop content
   or raise. Branch on which keys are present.

2. **Values contain inline HTML.** `<strong>` appears inside `p`, `ul` entries and `a`
   answers. So a template cannot blanket-escape these fields, and equally must not blanket
   trust every field. Decide escape versus raw **per field**, and keep the raw set as small
   as the content genuinely requires. This repo's templates run with Jinja2 autoescaping on
   by default, so any raw field has to be opted in deliberately and visibly.

3. **`store` and `samples` are optional.** Fifteen of forty eight packs carry `store` and
   one pack has no `samples`. Guard both.

## The honest-count rule applies to four fields

Bank-size figures appear in `seoDescription`, `heroSub`, `features[].p` and `faq[].a`.
Nineteen of the thirty seven packs measured at the time of the original 2026-07-27 audit
stated a bank size in one of those places, and one stated a derived total.

Every such figure must state the **honest count**, never a combined total inflated by
top-up filler. See `CLAUDE.md` for why this is forced rather than preferred.

Two figures are safe by construction and need no special handling: the mock size, which no
top-up removal moves, and the flashcard count, because `top_up` is a questions-only field
and no flashcard in the corpus carries it.

## What this repo does NOT do yet

No product template exists. There is no BiDaFa product to put in one, and building a
speculative template that nothing renders is how unused code rots. When the first app is
real, adding it means appending entries to `data/pages.json` and writing one template.
`build.py` should not need to change.

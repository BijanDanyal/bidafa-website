# Adding an exam page

Adding an exam is **one new data file plus one manifest entry**. No template change, no
`build.py` change. That is the point of the machinery: the expensive part of an exam page
should be finding and checking the facts, never the plumbing.

## The two steps

**1. Write `data/exams/<slug>.json`.** Copy `faa-part-107.json` and replace the values. The
field contract is below.

**2. Append an entry to `data/pages.json`:**

```json
{
  "id": "exam-<slug>",
  "template": "exam.html",
  "output": "exams/<slug>/index.html",
  "url_path": "/exams/<slug>/",
  "data_file": "exams/<slug>.json",
  "kind": "exam",
  "article": true,
  "breadcrumb": "<short name of the exam>",
  "seo_title_key": "data.seo_title",
  "seo_description_key": "data.seo_description",
  "llms_note": "<one line for llms.txt>",
  "sitemap": { "changefreq": "monthly", "priority": "0.9" }
}
```

Then add a matching entry under `home.exams.entries` in `data/site.json` so the new page is
linked from the homepage, and run:

    .venv/bin/python build.py --production

`kind: "exam"` is what subjects the file to the exam-data gate. Omitting it means the page
still renders but the sourcing rules are **not** enforced, which is exactly the mistake this
document exists to prevent. Always set it.

## The field contract

`build.py` enforces the rules marked ENFORCED. The build fails and writes nothing if one is
broken, so a page that renders is a page whose figures are all attributed.

| Field | Required | Notes |
|---|---|---|
| `id` | ENFORCED | Slug, matches the filename |
| `checked_on` | ENFORCED | `YYYY-MM-DD`, must be a real date and must not be in the future |
| `seo_title` | ENFORCED | Lead with the facts a searcher types, not the brand |
| `seo_description` | ENFORCED | State the headline numbers here; this is what gets shown and quoted |
| `summary` | ENFORCED | ONE sentence that defines the exam and stands alone if quoted with nothing around it |
| `exam` | yes | `name`, `official_name`, `test_code`, `also_known_as` (list), `country`, `regulator`, `grants`, `governed_by` |
| `sources` | ENFORCED | List of `{id, label, short, url, note}`. `id`, `label`, `short` and `url` are all required. `short` is what appears in the Source column of the fact table, so it must read as a source name ("FAA-S-ACS-10B"), never as an internal token ("acs") |
| `stats` | ENFORCED | List of `{label, value, source}`. **`source` must be an `id` in `sources`** |
| `stats_note` | no | Sits under the table |
| `topics_*` | no | `topics_heading`, `topics_intro`, `topics_source`, `topics` list of `{area, weight, detail}` |
| `limits_*` | no | `limits_heading`, `limits_intro`, `limits` list of `{limit, value, rule}`. **`rule` ENFORCED non-empty** |
| `samples_*` | no | `samples_heading`, `samples_intro`, `samples` list. See below |
| `mistakes_*` | no | `mistakes_heading` and a list of strings |
| `faq_*` | no | `faq_heading` and a list of `{q, a}`. **Both ENFORCED non-empty.** Emitted as `FAQPage` JSON-LD |
| `publisher_note_*` | no | Who published the page and what is or is not being claimed |
| `disclaimer` | no | Non-affiliation statement |

### `samples` entries, all ENFORCED

- `source_ref` must be non-empty. A question whose answer cannot be checked against a named
  rule is worth less than no question at all.
- `options` needs at least two entries.
- `answer` must be **exactly one of** the strings in `options`. This catches the copy-paste
  error where an option is reworded and the answer is not.
- `explanation` must be non-empty.

`area` is free text, conventionally the area of operation the question belongs to.

## The rules that are not mechanical

The gate can check that a figure names a source. It cannot check that the source actually
says it. Those rules are yours to keep:

1. **Read the figure in the source yourself.** Do not carry a number across from another
   site, from a question pack, or from an AI answer. Two packs agreeing with each other is
   not evidence; the regulator's own document is.
2. **Copy the regulator's precision.** If the FAA says "approximately 175 dollars", the page
   says approximately. Sharpening an approximate figure into a precise-looking one is the
   most common way an honest page becomes a false one.
3. **Move `checked_on` only when you actually checked.** It feeds `dateModified` in the
   structured data. A freshness signal that moves without a check having happened is a lie
   that happens to be machine readable, and it is the specific failure named in the research
   this design came from.
4. **A figure with no source does not go on the page.** Not in a smaller font, not hedged.
   Leave it out and say nothing.
5. **No product claims until there is a product.** No question counts for an unshipped app,
   no ratings, no download numbers, no testimonials. `build.py` blocks the markup forms of
   this (`SoftwareApplication`, `Offer`, `AggregateRating`, `Review`); it cannot block the
   prose forms, so that part is on the author.

## Why the page is ordered the way it is

A retrieved page is quoted in fragments, never whole. So the one-sentence definition and the
fact table come before any prose, each block is written to survive being lifted alone, and
the numbers live in tables because table rows extract intact. That ordering is the machine
readability decision on the page, and it is worth more than any markup on it.

See `GEO.md` for the evidence behind that claim and for what is deliberately not built yet.

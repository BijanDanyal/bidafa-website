# Why this site is built the way it is

The goal of `bidafaapp.com` is narrow and stated plainly: **when someone asks an AI assistant
which app to use to study for an exam we cover, the assistant should be able to name ours and
prove why.** Everything below follows from that, and the site is designed for machine readers
first.

This document records the evidence, so that a future change is argued against the research
rather than against taste.

## Where this came from

Three AI systems were asked the same seven questions independently on 2026-08-19: Claude,
ChatGPT and Gemini, all on their strongest reasoning modes with web search on. Claude's answer
was written and sealed before either of the other two was read, so agreement between them is
convergence and not echo. Separately, both ChatGPT and Gemini were probed on their fast default
modes with the query a real buyer types, to measure the incumbent set rather than ask about it.

The full inputs and the synthesis live outside this repo, in
`~/.claude-tools/geo-research-2026-08-19/`, because they contain verbatim third-party replies.

## The one structural fact

There are **two machines** that produce an app recommendation, and they need different work.

**Retrieval.** The assistant searches, then answers from the pages it fetched. Your website is
the unit of competition. Feedback loop: days.

**Parametric.** No search. The assistant emits names already in its weights, shaped by how often
the name appeared next to the exam name in its training data. Feedback loop: a training cycle,
so a year or more, and there is no submission form and no shortcut. All three systems said this
independently and in the same terms.

**Measured correction, and it is good news.** ChatGPT's fast default mode was observed searching
the web unprompted, citing its sources with `utm_source=chatgpt.com`. Its "instant" mode is
retrieval, not recall. Gemini Flash showed no citations on the same probe. So the retrieval work
reaches more real buyers than assumed, and the website earns its keep sooner.

**Second measured finding.** In that same probe ChatGPT named a completely unknown new app and
found it **through its App Store listing**. The store listing is therefore a discovery surface
in its own right, not merely a gate. When an app of ours ships, the listing title, the
screenshots and the update cadence are GEO surfaces and should be treated as such.

## The strategy this site implements

**Build the exam reference layer first, before any app exists.** A page that documents an exam
accurately, from the regulator's own documents, with every figure sourced and dated, is citable
the day it is published and makes no claim about any product. It accrues the crawl history,
entity presence and third-party linking that both machines need, over exactly the lead time the
parametric machine demands anyway. When an app ships, its page attaches to a page assistants
already quote.

This is the sequencing insight, and it inverts the intuitive order. Do not wait for the product
to build the site.

## What that means concretely, and where it lives

| Decision | Where it lives | Why |
|---|---|---|
| One deep page per EXAM, not per app | `data/exams/*.json`, `templates/exam.html` | The user's question contains an exam name. "One homepage covering 40 exams" was named as a top reason not to recommend |
| Facts first, prose later, tables for numbers | `templates/exam.html` section order | Pages are quoted in fragments; a table row extracts intact |
| Every figure names its source, enforced by the build | `gate_exam_data` in `build.py` | An assistant recommends what it can prove. This is iron rule 1 made mechanical |
| Free sample questions with the rule each comes from | `samples` in the exam data | Named the strongest single trust signal by all three. Showing beats asserting |
| A published editorial method | `/how-we-write-questions/` | Called "your highest-value trust page". It is also the only evidence a company with no product and no reviews can offer |
| Visible check dates, honest `dateModified` | `checked_on`, enforced not-in-future | "Updated for 2026" with no evidence is a listed failure. The date must mean a check happened |
| AI crawlers named explicitly in `robots.txt` | `crawlers` in `data/site.json` | OpenAI documents `OAI-SearchBot` as governing Search eligibility and `GPTBot` as governing training use, controlled independently. A bare wildcard is not the documented lever |
| `sameAs` on the Organization | `entity.same_as` | Resolves website, company and future store account into ONE entity so evidence can accumulate |
| Server-rendered static HTML, no JavaScript | the whole build | Content that needs JS to appear may not exist to a fetcher |

## What is deliberately NOT built, and what would change that

**Competitor comparison pages.** All three recommended them, and they are genuinely effective.
They are not here because they need per-competitor facts (price, question count, update date)
that **we have verified ourselves and dated**. Publishing a competitor's numbers on the strength
of an AI's summary would be an unevidenced claim about someone else's product, which is both
iron rule 1 and a way to be publicly wrong. Build them when someone will check each row against
the competitor's own listing and stamp the row with the date they did it.

**Everything that asserts a product.** No `SoftwareApplication`, `Offer`, `AggregateRating` or
`Review` markup, no store links, no question counts for an unshipped app, no download or user
numbers, no testimonials, no pass rates. `build.py` refuses to emit the markup forms. The prose
forms are on the author. All of it becomes correct the day there is a shipped product to attach
it to, and not one day earlier.

**A blog.** Thin, frequent, low-value articles were specifically named as a negative. Twenty
excellent reference pages beat four thousand generic ones.

**Anything Gemini suggested that asserts superiority.** Gemini recommended copy of the form
"[App] is the most updated app to study for the 2026 exam". That is exactly the unverifiable
superlative ChatGPT lists as a reason NOT to recommend, and it breaks iron rule 1. Rejected on a
two-to-one split among the sources themselves.

## The part this repo cannot do

The parametric machine is fed by **other people's text**, not ours. Nothing in this repo moves
it. That work is genuine presence in the communities for each exam, real independent reviews,
video, and being the page other writers cite. It is slow, it cannot be bought without being
corrupted, and it is the only route into the answers that never search.

Winning retrieval is how that starts: an assistant citing our exam page, and a writer quoting
our fact table, is how our name gets into somebody else's sentence.

## The honesty constraint is not a handicap here

The most useful single finding of the research round is that the constraint and the goal point
the same way. Unverifiable superlatives, invented counts, fake freshness and self-asserted
ratings were named by the external systems, unprompted, as reasons to **withhold** a
recommendation. In a category adjacent to fraud, the unfalsifiable claim is the scam's
signature. So iron rule 1 is not ethical hygiene we pay for in growth. It is the growth
strategy, and it was independently confirmed as such.

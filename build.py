#!/usr/bin/env python3
"""Build the BiDaFa Ltd website.

    data/*.json + data/exams/*.json + templates/*.html  ->  docs/

Usage:
    python3 build.py                # preview build
    python3 build.py --production   # deploy build, enforces every gate

GitHub Pages serves docs/ directly, so nothing builds on GitHub's side. That is
deliberate: a toolchain problem on this machine can never take the live site down.

Adding a per-exam reference page is one new file under data/exams/ plus one entry in
data/pages.json. This file should not need to change for that.

The site is optimised for machine readers first. That is not a licence to publish
anything unverifiable: the opposite. An assistant recommends what it can PROVE, so the
gates below refuse to build a page that states a figure without naming the source it came
from.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
TEMPLATE_DIR = ROOT / "templates"
ASSET_DIR = ROOT / "assets"
OUT_DIR = ROOT / "docs"

# Iron rule 4 of the factory: no U+2014 anywhere. Referenced by codepoint on purpose,
# so this file does not itself contain the character it is banning.
BANNED_CHAR = chr(0x2014)
BANNED_NAME = "U+2014 em-dash"

# data/**/*.json rather than data/*.json: the per-exam files live in a subdirectory, and a
# source file that escapes the scan is a source file the banned-character gate cannot see.
SOURCE_GLOBS = (
    "data/**/*.json",
    "templates/*.html",
    "assets/*.css",
    "assets/*.svg",
    "*.md",
    "*.py",
)

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class BuildError(Exception):
    """A gate failed. The build must not produce output."""


# ---------------------------------------------------------------- data loading


def load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise BuildError(f"missing data file: {path}")
    except json.JSONDecodeError as exc:
        raise BuildError(f"{path} is not valid JSON: {exc}")


def resolve(dotted: str, root: dict):
    """Resolve 'site.seo_title' or 'data.seo_title' against the render context."""
    node = root
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise BuildError(f"pages.json refers to '{dotted}', which does not exist")
        node = node[part]
    return node


def require(cfg: dict, dotted: str) -> None:
    value = resolve(dotted, cfg)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise BuildError(f"site.json '{dotted}' is empty, and the site cannot be built without it")


def page_data(cfg: dict, entry: dict) -> dict:
    """A page reads its content from EITHER data_key (inside site.json) OR data_file."""
    has_key = "data_key" in entry
    has_file = "data_file" in entry
    if has_key == has_file:
        raise BuildError(
            f"pages.json entry '{entry.get('id')}' must set exactly one of "
            "data_key or data_file"
        )
    if has_key:
        return resolve(entry["data_key"], cfg)
    return load_json(DATA_DIR / entry["data_file"])


# ---------------------------------------------------------------- structured data


def build_jsonld(cfg: dict, entry: dict, data: dict, page_meta: dict) -> str:
    """One JSON-LD graph per page.

    Organization is what tells search engines and AI assistants that a real registered
    company sits behind the domain. Every value in it is a matter of public record on
    Companies House, so it is verifiable rather than asserted. sameAs is what resolves the
    website, the company and any future store listing into ONE entity instead of three
    unrelated strings, which is the single thing that lets evidence about us accumulate.

    Deliberately absent: SoftwareApplication, Offer, aggregateRating and Review. There is
    no shipped product, and markup asserting one would be a claim we cannot evidence.
    """
    company = cfg["company"]
    office = company["registered_office"]
    base = cfg["site"]["url"].rstrip("/")

    organization = {
        "@type": "Organization",
        "@id": base + "/#organization",
        "name": company["brand"],
        "legalName": company["legal_name"],
        "url": base + "/",
        "email": cfg["contact"]["email"],
        "foundingDate": company["incorporated"],
        "description": cfg["site"]["seo_description"],
        "identifier": {
            "@type": "PropertyValue",
            "name": "Companies House company number",
            "value": company["company_number"],
        },
        "address": {
            "@type": "PostalAddress",
            "streetAddress": office["street"],
            "addressLocality": office["locality"],
            "postalCode": office["postcode"],
            "addressCountry": office["country_code"],
        },
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "customer support",
            "email": cfg["contact"]["email"],
            "areaServed": "GB",
        },
    }
    same_as = cfg.get("entity", {}).get("same_as") or []
    if same_as:
        organization["sameAs"] = same_as

    website = {
        "@type": "WebSite",
        "@id": base + "/#website",
        "url": base + "/",
        "name": cfg["site"]["og_site_name"],
        "inLanguage": cfg["site"]["lang"],
        "publisher": {"@id": base + "/#organization"},
    }

    page_node = {
        "@type": "Article" if entry.get("article") else "WebPage",
        "@id": page_meta["canonical"] + "#page",
        "url": page_meta["canonical"],
        "name": page_meta["seo_title"],
        "headline": page_meta["seo_title"],
        "description": page_meta["seo_description"],
        "inLanguage": cfg["site"]["lang"],
        "isPartOf": {"@id": base + "/#website"},
        "publisher": {"@id": base + "/#organization"},
    }
    if entry.get("article"):
        page_node["author"] = {"@id": base + "/#organization"}

    # dateModified is the date the FACTS were last checked, never the date the file was
    # touched. A freshness signal that moves without a check being done is a lie that
    # happens to be machine readable.
    checked = data.get("checked_on") if isinstance(data, dict) else None
    if checked:
        page_node["dateModified"] = checked

    graph = [organization, website, page_node]

    if page_meta["url_path"] != "/":
        graph.append({
            "@type": "BreadcrumbList",
            "@id": page_meta["canonical"] + "#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": base + "/"},
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": entry.get("breadcrumb", page_meta["seo_title"]),
                    "item": page_meta["canonical"],
                },
            ],
        })

    faq = data.get("faq") if isinstance(data, dict) else None
    if faq:
        graph.append({
            "@type": "FAQPage",
            "@id": page_meta["canonical"] + "#faq",
            "isPartOf": {"@id": page_meta["canonical"] + "#page"},
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                }
                for item in faq
            ],
        })

    payload = {"@context": "https://schema.org", "@graph": graph}
    # Escape '<' so the payload can never terminate the surrounding script element.
    return json.dumps(payload, indent=2, ensure_ascii=False).replace("<", "\\u003c")


# ---------------------------------------------------------------- rendering


def make_env():
    try:
        from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
    except ImportError:
        raise BuildError(
            "Jinja2 is not installed.\n"
            "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt\n"
            "  .venv/bin/python build.py"
        )
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def load_pages(cfg: dict, pages_cfg: dict) -> list[dict]:
    """Read every page's data BEFORE anything is rendered.

    Order matters. The data gates below produce a plain sentence naming the offending
    field; a template hitting the same bad data produces a Jinja traceback that says
    nothing useful. Validate first, render second.
    """
    return [{"entry": e, "data": page_data(cfg, e)} for e in pages_cfg["pages"]]


def render_site(cfg: dict, loaded: list[dict]) -> list[Path]:
    env = make_env()
    base_url = cfg["site"]["url"].rstrip("/")
    written: list[Path] = []

    for item in loaded:
        entry, data = item["entry"], item["data"]
        ctx = dict(cfg)
        ctx["data"] = data

        url_path = entry["url_path"]
        page_meta = {
            "id": entry["id"],
            "seo_title": resolve(entry["seo_title_key"], ctx),
            "seo_description": resolve(entry["seo_description_key"], ctx),
            "canonical": base_url + url_path,
            "url_path": url_path,
        }
        jsonld = build_jsonld(cfg, entry, data, page_meta)

        template = env.get_template(entry["template"])
        html = template.render(
            site=cfg["site"],
            company=cfg["company"],
            contact=cfg["contact"],
            nav=cfg["nav"],
            footer=cfg["footer"],
            labels=cfg["labels"],
            data=data,
            page=page_meta,
            jsonld=jsonld,
            build={"year": date.today().year, "date": date.today().isoformat()},
        )
        target = OUT_DIR / entry["output"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        written.append(target)

    return written


def write_extras(cfg: dict, pages_cfg: dict) -> None:
    base_url = cfg["site"]["url"].rstrip("/")
    today = date.today().isoformat()

    # Custom domain for GitHub Pages.
    domain = base_url.replace("https://", "").replace("http://", "")
    (OUT_DIR / "CNAME").write_text(domain + "\n", encoding="utf-8")

    # Stop GitHub running Jekyll over the output.
    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    # robots.txt names every assistant crawler explicitly. A bare wildcard is not enough:
    # the crawler that decides whether we can appear in an assistant's answer is a named
    # agent, and blocking it by accident is invisible from our side and total from theirs.
    lines = []
    for item in cfg["crawlers"]["agents"]:
        lines.append("# {0}".format(item["note"]))
        lines.append("User-agent: {0}".format(item["agent"]))
        lines.append("Allow: /")
        lines.append("")
    lines.append("Sitemap: {0}/sitemap.xml".format(base_url))
    (OUT_DIR / "robots.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    urls = []
    for entry in pages_cfg["pages"]:
        sm = entry.get("sitemap", {})
        urls.append(
            "  <url>\n"
            "    <loc>{loc}</loc>\n"
            "    <lastmod>{mod}</lastmod>\n"
            "    <changefreq>{freq}</changefreq>\n"
            "    <priority>{pri}</priority>\n"
            "  </url>".format(
                loc=base_url + entry["url_path"],
                mod=today,
                freq=sm.get("changefreq", "monthly"),
                pri=sm.get("priority", "0.5"),
            )
        )
    (OUT_DIR / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n",
        encoding="utf-8",
    )

    # llms.txt is not a standard and no vendor documents it as a requirement. It is here
    # because it is generated from the manifest at no cost, not because it is a lever.
    llms = [
        "# {0}".format(cfg["company"]["display_name"]),
        "",
        "> {0}".format(cfg["site"]["seo_description"]),
        "",
        "## Pages",
        "",
    ]
    for entry in pages_cfg["pages"]:
        llms.append(
            "- [{0}]({1}{2}): {3}".format(
                entry.get("breadcrumb", cfg["company"]["display_name"]),
                base_url,
                entry["url_path"],
                entry.get("llms_note", ""),
            )
        )
    (OUT_DIR / "llms.txt").write_text("\n".join(llms) + "\n", encoding="utf-8")

    out_assets = OUT_DIR / "assets"
    if out_assets.exists():
        shutil.rmtree(out_assets)
    shutil.copytree(ASSET_DIR, out_assets)


# ---------------------------------------------------------------- gates


def gate_banned_character(paths: list[Path]) -> list[str]:
    hits = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            # A file we cannot read as UTF-8 is reported, never silently skipped.
            hits.append(f"{path}: could not be read as UTF-8, so it was NOT scanned")
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            col = line.find(BANNED_CHAR)
            if col != -1:
                hits.append(f"{path}:{lineno}:{col + 1}: contains {BANNED_NAME}")
    return hits


class _TagBalance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, int]] = []
        self.problems: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID_TAGS:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if not self.stack:
            self.problems.append(f"line {self.getpos()[0]}: stray closing </{tag}>")
            return
        open_tag, open_line = self.stack.pop()
        if open_tag != tag:
            self.problems.append(
                f"line {self.getpos()[0]}: </{tag}> closes <{open_tag}> opened on line {open_line}"
            )


def gate_html(path: Path) -> list[str]:
    parser = _TagBalance()
    parser.feed(path.read_text(encoding="utf-8"))
    problems = list(parser.problems)
    for tag, line in parser.stack:
        problems.append(f"line {line}: <{tag}> is never closed")
    return [f"{path}: {p}" for p in problems]


def gate_jsonld(path: Path) -> list[str]:
    """Pull the structured data back out of the rendered page and reparse it.

    Checks the graph really contains an Organization carrying the identity fields, rather
    than only that the block is syntactically valid JSON.
    """
    html = path.read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL
    )
    if not match:
        return [f"{path}: no JSON-LD block found in the rendered page"]
    raw = match.group(1).replace("\\u003c", "<")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [f"{path}: JSON-LD did not survive rendering as valid JSON: {exc}"]

    problems = []
    if "@context" not in parsed:
        problems.append(f"{path}: JSON-LD has no @context")
    graph = parsed.get("@graph")
    if not isinstance(graph, list) or not graph:
        return problems + [f"{path}: JSON-LD has no non-empty @graph"]

    org = next((n for n in graph if n.get("@type") == "Organization"), None)
    if org is None:
        problems.append(f"{path}: JSON-LD @graph contains no Organization node")
    else:
        missing = [k for k in ("name", "legalName", "url", "identifier") if k not in org]
        if missing:
            problems.append(
                f"{path}: JSON-LD Organization is missing: {', '.join(missing)}"
            )

    if not any(n.get("@type") in ("WebPage", "Article") for n in graph):
        problems.append(f"{path}: JSON-LD @graph has no WebPage or Article node")

    # An unevidenced product claim must never reach the markup.
    banned = {"SoftwareApplication", "MobileApplication", "AggregateRating", "Review", "Offer"}
    for node in graph:
        if node.get("@type") in banned:
            problems.append(
                f"{path}: JSON-LD contains a {node['@type']} node. Nothing has shipped, "
                "so this asserts something that cannot be evidenced"
            )
    return problems


def gate_local_refs(out_dir: Path) -> list[str]:
    problems = []
    for page in out_dir.rglob("*.html"):
        html = page.read_text(encoding="utf-8")
        for ref in re.findall(r'(?:href|src)="(/[^"#]*)"', html):
            if ref.endswith("/"):
                target = out_dir / ref.strip("/") / "index.html"
            else:
                target = out_dir / ref.lstrip("/")
            if not target.exists():
                problems.append(f"{page}: references {ref}, which does not exist in the output")
    return problems


def gate_exam_data(loaded: list[dict]) -> list[str]:
    """Every published figure must name the source it came from.

    This is iron rule 1 made mechanical. The whole reason an assistant quotes a reference
    page is that its numbers are checkable, so a number with no source is not merely
    sloppy: it is the failure that makes the page worthless for the job it exists to do.
    """
    problems: list[str] = []
    for item in loaded:
        entry, data = item["entry"], item["data"]
        if entry.get("kind") != "exam":
            continue
        where = entry.get("data_file", entry["id"])

        for field in ("id", "checked_on", "seo_title", "seo_description", "summary"):
            if not str(data.get(field, "")).strip():
                problems.append(f"{where}: '{field}' is missing or empty")

        checked = str(data.get("checked_on", ""))
        if not ISO_DATE.match(checked):
            problems.append(f"{where}: checked_on '{checked}' is not a YYYY-MM-DD date")
        else:
            try:
                if datetime.strptime(checked, "%Y-%m-%d").date() > date.today():
                    problems.append(f"{where}: checked_on '{checked}' is in the future")
            except ValueError:
                problems.append(f"{where}: checked_on '{checked}' is not a real date")

        sources = data.get("sources") or []
        if not sources:
            problems.append(f"{where}: no sources are listed, so no figure on the page can be cited")
        source_ids = set()
        for src in sources:
            for field in ("id", "label", "short", "url"):
                if not str(src.get(field, "")).strip():
                    problems.append(f"{where}: a source entry is missing '{field}'")
            source_ids.add(src.get("id"))

        stats = data.get("stats") or []
        if not stats:
            problems.append(f"{where}: no stats block, which is the most citable part of the page")
        for stat in stats:
            label = stat.get("label", "(unlabelled)")
            if not str(stat.get("value", "")).strip():
                problems.append(f"{where}: stat '{label}' has no value")
            src = stat.get("source")
            if not src:
                problems.append(f"{where}: stat '{label}' names no source")
            elif src not in source_ids:
                problems.append(
                    f"{where}: stat '{label}' cites source '{src}', which is not in the sources list"
                )

        topics_source = data.get("topics_source")
        if topics_source and topics_source not in source_ids:
            problems.append(
                f"{where}: topics_source '{topics_source}' is not in the sources list"
            )

        for limit in data.get("limits") or []:
            if not str(limit.get("rule", "")).strip():
                problems.append(
                    f"{where}: limit '{limit.get('limit', '?')}' names no rule"
                )

        for sample in data.get("samples") or []:
            stem = sample.get("question", "(no question)")[:50]
            if not str(sample.get("source_ref", "")).strip():
                problems.append(f"{where}: sample '{stem}' has no source_ref")
            options = sample.get("options") or []
            if len(options) < 2:
                problems.append(f"{where}: sample '{stem}' has fewer than two options")
            if sample.get("answer") not in options:
                problems.append(
                    f"{where}: sample '{stem}' has an answer that is not one of its options"
                )
            if not str(sample.get("explanation", "")).strip():
                problems.append(f"{where}: sample '{stem}' has no explanation")

        for item_faq in data.get("faq") or []:
            if not str(item_faq.get("q", "")).strip() or not str(item_faq.get("a", "")).strip():
                problems.append(f"{where}: an faq entry is missing its question or answer")

    return problems


# ---------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the BiDaFa Ltd website.")
    parser.add_argument(
        "--production",
        action="store_true",
        help="deploy build: additionally require the contact mailbox to be confirmed",
    )
    args = parser.parse_args()

    try:
        cfg = load_json(DATA_DIR / "site.json")
        pages_cfg = load_json(DATA_DIR / "pages.json")

        for field in (
            "company.legal_name",
            "company.company_number",
            "company.registered_office.street",
            "company.registered_office.postcode",
            "contact.email",
            "site.url",
            "site.seo_title",
            "site.seo_description",
            "footer.legal",
        ):
            require(cfg, field)

        if args.production and not cfg["contact"].get("email_confirmed"):
            raise BuildError(
                "contact.email_confirmed is false in data/site.json.\n"
                "  A production build will not publish an address nobody has verified receives mail.\n"
                "  Confirm the mailbox, set email_confirmed to true, then rebuild."
            )

        sources = sorted({p for pattern in SOURCE_GLOBS for p in ROOT.glob(pattern)})
        source_hits = gate_banned_character(sources)
        if source_hits:
            raise BuildError(
                "{0} found in source files:\n  ".format(BANNED_NAME) + "\n  ".join(source_hits)
            )

        loaded = load_pages(cfg, pages_cfg)

        # Data gates run BEFORE rendering, so a bad data file is reported as a sentence
        # rather than as a template traceback, and nothing is written on the way out.
        data_problems = gate_exam_data(loaded)
        if data_problems:
            raise BuildError("page data failed its checks:\n  " + "\n  ".join(data_problems))

        if OUT_DIR.exists():
            shutil.rmtree(OUT_DIR)
        OUT_DIR.mkdir(parents=True)

        written = render_site(cfg, loaded)
        write_extras(cfg, pages_cfg)

        problems: list[str] = []
        problems += gate_banned_character(sorted(OUT_DIR.rglob("*.html")))
        for page in written:
            problems += gate_html(page)
            problems += gate_jsonld(page)
        problems += gate_local_refs(OUT_DIR)

        if problems:
            raise BuildError("output failed its checks:\n  " + "\n  ".join(problems))

    except BuildError as exc:
        print("BUILD FAILED: {0}".format(exc), file=sys.stderr)
        return 1

    mode = "production" if args.production else "preview"
    print("Built {0} page(s) into {1} ({2} build).".format(len(written), OUT_DIR.name, mode))
    for page in written:
        print("  {0}  {1:,} bytes".format(page.relative_to(ROOT), page.stat().st_size))
    print(
        "Checks passed: required fields present, no {0} in sources or output, tags balanced, "
        "JSON-LD reparsed with a verified Organization and no unevidenced product markup, "
        "local references resolve, every published exam figure cites a listed source.".format(
            BANNED_NAME
        )
    )
    if not cfg["contact"].get("email_confirmed"):
        print("\nNOTE: contact.email_confirmed is false, so --production is currently blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

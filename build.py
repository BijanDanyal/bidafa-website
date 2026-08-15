#!/usr/bin/env python3
"""Build the BiDaFa Ltd website.

    data/*.json + templates/*.html  ->  docs/

Usage:
    python3 build.py                # preview build
    python3 build.py --production   # deploy build, enforces every gate

GitHub Pages serves docs/ directly, so nothing builds on GitHub's side. That is
deliberate: a toolchain problem on this machine can never take the live site down.

Adding the future per-exam product pages is an edit to data/pages.json plus one new
template. This file should not need to change for that.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
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

SOURCE_GLOBS = ("data/*.json", "templates/*.html", "assets/*.css", "assets/*.svg", "*.md", "*.py")

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


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
    """Resolve 'site.seo_title' against the loaded config."""
    node = root
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise BuildError(f"pages.json refers to '{dotted}', which does not exist in site.json")
        node = node[part]
    return node


def require(cfg: dict, dotted: str) -> None:
    value = resolve(dotted, cfg)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise BuildError(f"site.json '{dotted}' is empty, and the site cannot be built without it")


# ---------------------------------------------------------------- structured data


def build_jsonld(cfg: dict) -> str:
    """Organization structured data.

    This is what tells Apple's reviewers, search engines and AI assistants that a real
    registered company sits behind the domain. Every value here is a matter of public
    record on Companies House, so it is verifiable rather than asserted.
    """
    company = cfg["company"]
    office = company["registered_office"]
    payload = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": company["brand"],
        "legalName": company["legal_name"],
        "url": cfg["site"]["url"] + "/",
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


def render_site(cfg: dict, pages_cfg: dict) -> list[Path]:
    env = make_env()
    jsonld = build_jsonld(cfg)
    base_url = cfg["site"]["url"].rstrip("/")
    written: list[Path] = []

    for entry in pages_cfg["pages"]:
        url_path = entry["url_path"]
        page_meta = {
            "id": entry["id"],
            "seo_title": resolve(entry["seo_title_key"], cfg),
            "seo_description": resolve(entry["seo_description_key"], cfg),
            "canonical": base_url + url_path,
            "url_path": url_path,
        }
        template = env.get_template(entry["template"])
        html = template.render(
            site=cfg["site"],
            company=cfg["company"],
            contact=cfg["contact"],
            nav=cfg["nav"],
            footer=cfg["footer"],
            data=cfg[entry["data_key"]],
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

    (OUT_DIR / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: {0}/sitemap.xml\n".format(base_url),
        encoding="utf-8",
    )

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
    """Pull the structured data back out of the rendered page and reparse it."""
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
    missing = [k for k in ("@context", "@type", "name", "legalName", "url") if k not in parsed]
    if missing:
        return [f"{path}: JSON-LD is missing required keys: {', '.join(missing)}"]
    return []


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

        if OUT_DIR.exists():
            shutil.rmtree(OUT_DIR)
        OUT_DIR.mkdir(parents=True)

        written = render_site(cfg, pages_cfg)
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
    print("Checks passed: no {0}, tags balanced, JSON-LD reparsed, local references resolve.".format(BANNED_NAME))
    if not cfg["contact"].get("email_confirmed"):
        print("\nNOTE: contact.email_confirmed is false, so --production is currently blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

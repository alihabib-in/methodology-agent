"""Research source policy for the International Research Agent (Phase E).

The agent must rely only on verified published information from credible
statistical organizations and discard user-generated content (blogs, videos,
forums, wikis). This module encodes:

- the authoritative standards reference (from the SCAD methodology skill),
- the nine research categories,
- a domain allowlist/blocklist with a credibility classifier.
"""

from __future__ import annotations

from enum import Enum
from urllib.parse import urlparse

# --- Research scope ----------------------------------------------------------

RESEARCH_CATEGORIES = [
    "Conceptual frameworks and definitions",
    "Classification systems (activity, product, geographic)",
    "Data collection standards and survey methodology",
    "Index number theory and price/volume measurement",
    "Quality frameworks (GSBPM, DQAF, Code of Practice)",
    "Seasonal adjustment and time series methods",
    "Dissemination and metadata standards (SDMX, SDDS)",
    "Best practices from leading NSOs",
    "GCC-Stat regional harmonization standards",
]

# Issuing body -> purpose (authoritative standards reference).
STANDARDS_REFERENCE = [
    {"standard": "IRIIP 2010", "org": "UNSD", "purpose": "Principal methodological reference"},
    {"standard": "ISIC Rev.4", "org": "UNSD", "purpose": "Activity classification"},
    {"standard": "SNA 2008", "org": "UN", "purpose": "Volume measurement conceptual framework"},
    {"standard": "CPC Ver.2.1", "org": "UNSD", "purpose": "Product classification"},
    {"standard": "GSBPM v5.1", "org": "UNECE", "purpose": "Statistical process framework"},
    {"standard": "IMF DQAF", "org": "IMF", "purpose": "Data quality assessment"},
    {"standard": "PPI Manual", "org": "IMF", "purpose": "Deflation and price index guidance"},
    {"standard": "ESS Seasonal Adjustment Guidelines", "org": "Eurostat", "purpose": "Seasonal adjustment methods"},
    {"standard": "European Statistics Code of Practice", "org": "Eurostat", "purpose": "Quality framework"},
    {"standard": "SDMX Content-Oriented Guidelines", "org": "SDMX", "purpose": "Metadata standards"},
    {"standard": "IMF SDDS / GDDS", "org": "IMF", "purpose": "Dissemination standards"},
    {"standard": "GCC-Stat standards", "org": "GCC-Stat", "purpose": "Regional harmonization"},
]

# --- Credibility -------------------------------------------------------------


class Credibility(str, Enum):
    verified = "verified"          # known authoritative statistical organization
    official = "official"          # .gov / .int / .edu official body
    unverified = "unverified"      # plausible but not on the allowlist
    not_credible = "not_credible"  # user-generated / untrusted


# High-trust official statistical organizations.
CREDIBLE_DOMAINS = [
    "unstats.un.org", "un.org", "unece.org", "ilo.org", "oecd.org", "imf.org",
    "worldbank.org", "ec.europa.eu", "europa.eu", "sdmx.org", "gccstat.org",
    "iso.org", "bis.org", "fao.org", "who.int", "unesco.org", "unctad.org",
    "wto.org", "unfpa.org", "unicef.org", "ifad.org",
]

# User-generated / untrusted content to always discard.
BLOCKED_DOMAINS = [
    "youtube.com", "youtu.be", "blogspot.com", "medium.com", "wordpress.com",
    "wix.com", "reddit.com", "quora.com", "wikipedia.org", "wikimedia.org",
    "wikihow.com", "linkedin.com", "facebook.com", "x.com", "twitter.com",
    "instagram.com", "tiktok.com", "github.com", "gitlab.com", "stackexchange.com",
    "stackoverflow.com", "slideshare.net", "scribd.com", "news.ycombinator.com",
]

OFFICIAL_TLDS = (".gov", ".int", ".edu", ".gov.ae", ".gov.sa", ".gov.ae")


def _domain_of(url: str) -> str:
    host = (urlparse(url if "://" in url else f"https://{url}").hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def classify_url(url: str) -> Credibility:
    domain = _domain_of(url)
    if not domain:
        return Credibility.not_credible
    if any(domain == b or domain.endswith("." + b) for b in BLOCKED_DOMAINS):
        return Credibility.not_credible
    if any(domain == c or domain.endswith("." + c) for c in CREDIBLE_DOMAINS):
        return Credibility.verified
    if any(domain.endswith(t) for t in OFFICIAL_TLDS):
        return Credibility.official
    return Credibility.unverified


def is_credible(url: str) -> bool:
    return classify_url(url) in (Credibility.verified, Credibility.official)


def filter_source_register(sources: list[dict]) -> list[dict]:
    """Annotate each source with credibility and discard user-generated content."""
    kept: list[dict] = []
    for source in sources:
        url = (source.get("url") or "").strip()
        credibility = classify_url(url)
        if credibility == Credibility.not_credible:
            continue
        source["credibility"] = credibility.value
        kept.append(source)
    return kept

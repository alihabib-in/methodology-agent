from app.research.sources import Credibility, classify_url, filter_source_register, is_credible


def test_credible_official_org():
    assert classify_url("https://unstats.un.org/unsd/nationalaccount/") == Credibility.verified
    assert is_credible("https://www.imf.org/en/Data")


def test_official_tld():
    assert classify_url("https://www.fcsc.gov.ae/en-us/") == Credibility.official
    assert is_credible("https://www.somebody.gov.ae")


def test_blocked_user_generated_content():
    assert classify_url("https://www.youtube.com/watch?v=abc") == Credibility.not_credible
    assert classify_url("https://en.wikipedia.org/wiki/ISIC") == Credibility.not_credible
    assert classify_url("https://medium.com/@user/post") == Credibility.not_credible


def test_unknown_domain():
    assert classify_url("https://somerandomsite.com/x") == Credibility.unverified


def test_filter_source_register_discards_ugc():
    sources = [
        {"name": "ISIC Rev.4", "url": "https://unstats.un.org/unsd/classifications/"},
        {"name": "random blog", "url": "https://medium.com/@x/post"},
        {"name": "wiki", "url": "https://en.wikipedia.org/wiki/ISIC"},
    ]
    kept = filter_source_register(sources)
    assert len(kept) == 1
    assert kept[0]["name"] == "ISIC Rev.4"
    assert kept[0]["credibility"] == "verified"

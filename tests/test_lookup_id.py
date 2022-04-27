from tmms.tmms import get_id
import os

# api_key = os.getenv("TMDB_API_KEY")
api_key = "860cec2bd4872e01c7800f57d5f7a5ea"


def test_missing_title():
    assert -1 == get_id(api_key=api_key, strict=True, title="")


def test_lookupid_missing_entry():
    assert -1 == get_id(api_key=api_key, strict=True, title="missingtitleforthis")


def test_correct():
    assert 603 == get_id(api_key=api_key, strict=True, title="The Matrix", year="1999")

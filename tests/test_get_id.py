from tmms.tmms import get_id
import os 

def test_get_id():
    api_key = os.getenv("TMDB_API_KEY")
    strict = False
    title = "The Matrix"
    year = "1999"
    assert get_id(api_key = api_key, strict = strict, title = title, year = year) == 603

def test_get_id_notitle():
    api_key = os.getenv("TMDB_API_KEY")
    strict = False
    title = ""
    year = "1999"
    assert get_id(api_key = api_key, strict = strict, title = title, year = year) == -1


def test_get_id_badtitle():
    api_key = os.getenv("TMDB_API_KEY")
    strict = False
    title = "hasdlfjasfdasjösaldf"
    year = "1999"
    assert get_id(api_key = api_key, strict = strict, title = title, year = year) == -1

def test_get_id_noapikey():
    api_key = ""
    strict = False
    title = "The Matrix"
    year = "1999"
    assert get_id(api_key = api_key, strict = strict, title = title, year = year) == -1

def test_get_id_strict():
    api_key = os.getenv("TMDB_API_KEY")
    strict = True
    title = "The Matrix"
    year = "1900"
    assert get_id(api_key = api_key, strict = strict, title = title, year = year) == -1

def test_get_id_notstrict():
    api_key = os.getenv("TMDB_API_KEY")
    strict = False
    title = "The Matrix"
    year = "1900"
    assert get_id(api_key = api_key, strict = strict, title = title, year = year) == 603
    assert get_id(api_key = api_key, strict = strict, title = title) == 603
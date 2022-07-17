import os


def test_check_api_key():
    assert os.getenv("TMDB_API_KEY") is not None
    assert os.getenv(
        "POETRY_TMDB_API_KEY") is not None

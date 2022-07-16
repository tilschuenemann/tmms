from tmms.tmms import get_ids
import os

def test_get_ids():
    api_key = os.getenv("TMDB_API_KEY")
    strict = True
    items_names = ["1999 - The Matrix"]
    style = 1

    assert get_ids(api_key, strict, item_names)

# test no api key

# test no item names

# test no style supplied / style -1

# check with malformed entries
items_names = [
    "1999 - The Matrix",
    "199 - The Matrix",
    "",
    "The Matrix",
    "1999"
    "1999 - "
            ]
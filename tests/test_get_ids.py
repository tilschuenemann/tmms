from tmms.tmms import get_ids
import os

def test_get_ids():
    api_key = os.getenv("TMDB_API_KEY")
    strict = True
    item_names = ["1999 - The Matrix"]
    style = 1

    result = get_ids(api_key=api_key, strict=strict, item_names=item_names,style=style)

    # check for schema
    assert result.shape == (1,2)
    assert result.columns.values.tolist() == ["item","tmdb_id"]
    assert result["item"].dtypes == "object"
    assert result["tmdb_id"].dtypes == "int64"
    
    # check for correct id
    assert result["tmdb_id"][0] == 603

def test_get_ids_noapikey():
    api_key = ""
    strict = True
    item_names = ["1999 - The Matrix"]
    style = 1

    result = get_ids(api_key=api_key, strict=strict, item_names=item_names,style=style)

    # check for schema
    assert result.shape == (1,2)
    assert result.columns.values.tolist() == ["item","tmdb_id"]
    assert result["item"].dtypes == "object"
    assert result["tmdb_id"].dtypes == "int64"
    
    # check for correct id
    assert result["tmdb_id"][0] == -1




# test no item names

# test no style supplied / style -1

# def test_get_ids_malformeditems():
#     api_key = os.getenv("TMDB_API_KEY")
#     strict = True
#     item_names = [
#     "1999 - The Matrix",
#     "199 - The Matrix",
#     "",
#     "The Matrix",
#     "1999"
#     "1999 - "
#             ]
#     style = 1

#     result = get_ids(api_key=api_key, strict=strict, item_names=item_names,style=style)

#     # check for schema
#     assert result.shape == (6,2)
#     assert result.columns.values.tolist() == ["item","tmdb_id"]
#     assert result["item"].dtypes == "object"
#     assert result["tmdb_id"].dtypes == "int64"
    
    # check for correct id
    #assert result["tmdb_id"][0] == 603


# check with malformed entries

from tmms.tmms import _str_empty


def test_str_empty():
    assert _str_empty("")
    assert _str_empty("   ")

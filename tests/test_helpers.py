from tmms.tmms import _str_empty, _guess_convention


def test_str_empty():
    assert _str_empty("")
    assert _str_empty("  ")


def test_guess_convention():
    t1 = ["The Matrix (1999) (subs)"]
    t2 = ["1999 - The Matrix (1999)"]
    t3 = [""]

    assert _guess_convention(t1) == 1
    assert _guess_convention(t2) == 2
    assert _guess_convention(t3) == -1
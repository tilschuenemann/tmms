from tmms.tmms import _str_empty, _guess_convention, _write_to_disk
import pathlib
import pandas as pd 

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

def test_write_to_disk(tmp_path):
    output_folder = tmp_path / "output"
    output_folder.mkdir()
    df = pd.DataFrame.from_dict({"col":["testing"]})

    d = output_folder

    output_folder_contents = list(output_folder.glob('*.*'))
    assert len(output_folder_contents) == 0
    _write_to_disk(df, "test.csv",d)
    
    output_folder_contents = list(output_folder.glob('*.*'))
    assert len(output_folder_contents) == 1
    assert output_folder_contents[0].name == "test.csv"
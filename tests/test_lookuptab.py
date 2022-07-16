from tmms.tmms import _update_lookup_table
import os
def test_update_lookup_table(tmp_path):
    # tests if lookuptab gets created
    
    i = tmp_path / "inputfolder"
    i.mkdir()
    m1 = i / "The Matrix (1999) (nosubs)"
    m1.mkdir()

    o = tmp_path / "output_folder"
    o.mkdir()

    api_key = os.getenv("TMDB_API_KEY")
    strict = True

    file_count = len(list(o.glob('*.*')))
    assert file_count == 0

    lookuptab = _update_lookup_table(api_key=api_key, strict=strict, input_folder=i, output_folder=o)
    assert lookuptab.shape==(1,3)


    file_count = len(list(o.glob('*.*')))
    assert file_count == 1
    assert list(o.glob('*.*'))[0].name == "tmms_lookuptab.csv"

    m2 = i / "The Matrix Revolutions (2003) (nosubs)"
    m2.mkdir()

    lookuptab = _update_lookup_table(api_key=api_key, strict=strict, input_folder=i, output_folder=o)
    assert lookuptab.shape==(2,3)

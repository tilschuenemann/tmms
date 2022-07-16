from tmms.tmms import main
import pathlib
import os
import pytest

def test_argparse_lookuptaboutput(tmp_path):
    d = tmp_path / "input_folder"
    d.mkdir()

    d2 = d / "The Matrix (1999) (nosubs)"
    d2.mkdir()

    o = tmp_path / "output_folder"
    o.mkdir()

    assert len(list(o.glob('*.*'))) == 0

    api_key = os.getenv("TMDB_API_KEY")
    main([str(d),"--output_folder",str(o),"--style","0"])
    assert len(list(o.glob('*.*'))) == 1

def test_argparse_lookuptaboutput(tmp_path):
    d = tmp_path / "input_folder"
    d.mkdir()

    d2 = d / "The Matrix (1999) (nosubs)"
    d2.mkdir()

    o = tmp_path / "output_folder"
    o.mkdir()

    assert len(list(o.glob('*.*'))) == 0

    api_key = os.getenv("TMDB_API_KEY")
    main([str(d),"--output_folder",str(o),"--style","0","--m","--c"])
    assert len(list(o.glob('*.*'))) == 7

def test_argparse_badinputfolder(capsys):

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main(["non-existing-folder"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == "input folder doesnt exist or is not a directory"
    
def test_argparse_badoutputfolder(capsys, tmp_path):
    d = tmp_path / "input_folder"
    d.mkdir()

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main([str(d),"--output_folder","non-existing-folder"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == "output folder doesnt exist or is not a directory"

def test_argparse_noapikey(tmp_path):
    
    os.environ.pop('TMDB_API_KEY', None)
    d = tmp_path / "input_folder"
    d.mkdir()

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main([str(d),"--api_key",None])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == "no api key supplied"

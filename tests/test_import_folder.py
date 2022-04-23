from tmms.tmms import import_folder

# TODO test with file


def test_input_folder_not_existing(tmpdir):
    df = import_folder("non-existing-dir", 0)
    assert df.empty


def test_input_folder_empty(tmpdir):
    empty_dir = tmpdir.mkdir("mydir")
    df = import_folder(input_folder=str(empty_dir), style=0)
    assert df.empty


def test_input_folder_success(tmpdir):
    input_folder = tmpdir.mkdir("movies")
    input_folder.mkdir("The Matrix (1999) (subs)")

    df = import_folder(str(input_folder), 0)
    assert df["disk.fname"][0] == "The Matrix (1999) (subs)"
    assert df["disk.year"][0] == "1999"
    assert df["disk.subtitles"][0] == "subs"
    assert df["disk.title"][0] == "The Matrix"
    assert df["tmms.id_auto"][0] == 0
    assert df["tmms.id_man"][0] == 0

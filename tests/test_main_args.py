from tmms.tmms import main
import os
import pytest

api_key = "MYAPIKEY"
input_folder = os.getcwd()
output_folder = os.getcwd()
style = 0
m = False
c = False


def test_no_apikey():
    with pytest.raises(SystemExit) as e:
        main("", input_folder, output_folder, m, c, style)
    assert e.type == SystemExit
    assert e.value.code == "no api key supplied"


def test_no_input_arg():
    with pytest.raises(SystemExit) as e:
        main(api_key, "", output_folder, m, c, style)
    assert e.type == SystemExit
    assert e.value.code == "input folder doesnt exit or is not a directory"


def test_style_not_in_range():
    with pytest.raises(SystemExit) as e:
        main(api_key, input_folder, output_folder, m, c, 2)
    assert e.type == SystemExit
    assert e.value.code == "style not in range"


def test_no_output_arg():
    with pytest.raises(SystemExit) as e:
        main(api_key, input_folder, "", m, c, style)
    assert e.type == SystemExit
    assert e.value.code == "output folder doesnt exit or is not a directory"

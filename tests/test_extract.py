from tmms.tmms import _extract
import pandas as pd 

def test_extract_style0success():

    act_df = _extract(["The Matrix (1999) (nosubs)"],0)
    exp_df = pd.DataFrame.from_dict({
        "item":["The Matrix (1999) (nosubs)"],
        "title":["The Matrix"],
        "year":["1999"],
        "subtitles": ["nosubs"]})
    assert  act_df.equals(exp_df)
    
def test_extract_style0badinput():
    # empty input
    act_df = _extract([""],0)
    exp_df = pd.DataFrame.from_dict({
        "item":[""],
        "title":[""],
        "year":[""],
        "subtitles": [""]})
    assert  act_df.equals(exp_df)
    
    # bad input 
    act_df = _extract(["The Matrix"],0)
    exp_df = pd.DataFrame.from_dict({
        "item":["The Matrix"],
        "title":[""],
        "year":[""],
        "subtitles": [""]})
    assert  act_df.equals(exp_df)
    
    act_df = _extract(["The Matrix (199) (nosubs)"],0)
    exp_df = pd.DataFrame.from_dict({
        "item":["The Matrix (199) (nosubs)"],
        "title":[""],
        "year":[""],
        "subtitles": [""]})
    assert  act_df.equals(exp_df)

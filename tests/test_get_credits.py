from tmms.tmms import get_credits
import os 
import pandas as pd


def test_get_credits():
    api_key = os.getenv("TMDB_API_KEY")
    act_df = get_credits(api_key, [603])
    exp_df = pd.read_csv("tests/credits.csv",encoding="UTF-8",sep=";",thousands=".",decimal=",")
    exp_df["cc.cast_id"] = exp_df["cc.cast_id"].astype(float)
    exp_df["cc.order"] = exp_df["cc.order"].astype(float)
    
    print(act_df["cc.popularity"])
    print(exp_df["cc.popularity"])

    assert pd.testing.assert_frame_equal(act_df.reset_index(drop=True), exp_df.reset_index(drop=True)) is None
    
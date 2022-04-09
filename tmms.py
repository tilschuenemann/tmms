import requests
import pandas as pd
import os
import re
import json
from pandas import json_normalize
from datetime import datetime


def import_folder(parent_folder: str) -> pd.DataFrame():

    movies_disk = next(os.walk(parent_folder))[1]
    df = pd.DataFrame(movies_disk)
    df.columns = ["disk.fname"]

    # year column

    year = []
    for values in df["disk.fname"]:
        year.append(re.search(r"\d{4}", values).group())

    df["disk.year"] = year

    # subtitles

    subtitles = []
    for values in df["disk.fname"]:
        subtitles.append(re.search(r"\(([A-Za-z]*)\)", values).group(1))

    df["disk.subtitles"] = subtitles

    # title

    titles = []

    for i in range(0, len(df)):
        ori_length = len(df.iloc[i]["disk.fname"])
        sub_length = len(df.iloc[i]["disk.subtitles"])
        fix_length = len(" (1234) ()")
        new_length = ori_length - sub_length - fix_length

        titles.append(df.iloc[i]["disk.fname"][:new_length])

    df["disk.title"] = titles

    return df


def lookup_id(api_key: str, title: str, year: int) -> int():
    url = f"https://api.themoviedb.org/3/search/movie/?api_key={api_key}&query={title}&year={year}&include_adult=true"

    id = 0

    response = requests.get(url).json()

    try:
        id = response["results"][0]["id"]
        return id
    except IndexError:
        url = f"https://api.themoviedb.org/3/search/movie/?api_key={api_key}&query={title}&include_adult=true"

    response = requests.get(url).json()
    try:
        id = response["results"][0]["id"]
        return id
    except IndexError:
        return 0


def lookup_details(api_key: str, m_id: str) -> pd.DataFrame:

    url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={api_key}&include_adult=true"
    response = requests.get(url).json()

    # TODO belongs_to_collection doesnt get flattened

    to_unnest = [
        "spoken_languages",
        "genres",
        "production_companies",
        "production_countries",
    ]

    for col in to_unnest:
        df = pd.json_normalize(
            response,
            record_path=col,
            meta=[
                "adult",
                "backdrop_path",
                "budget",
                "homepage",
                "id",
                "imdb_id",
                "original_language",
                "original_title",
                "overview",
                "popularity",
                "poster_path",
                "release_date",
                "revenue",
                "runtime",
                "status",
                "tagline",
                "title",
                "video",
                "vote_average",
                "vote_count",
            ],
            record_prefix=col + ".",
            errors="ignore",
        )

    return df


def main(api_key: str, parent_folder: str):

    start = datetime.now()

    df = import_folder(parent_folder)

    tmdb_id_auto = []

    df["tmdb_id_auto"] = df.apply(
        lambda row: lookup_id(api_key, row["disk.title"], row["disk.year"]), axis=1
    )

    details_df = pd.DataFrame()
    for index, row in df.iterrows():
        m_details = lookup_details(api_key, row["tmdb_id_auto"])
        details_df = pd.concat([details_df, m_details], axis=0)

    details_df = details_df.reset_index(drop=True)

    m_details = df.merge(details_df, left_on="tmdb_id_auto", right_on="id")

    m_details.to_csv("tmdb_movie_metadata.csv", sep=";", encoding="UTF-8", index=False)
    duration = datetime.now() - start
    print(duration)


if __name__ == "__main__":
    main()

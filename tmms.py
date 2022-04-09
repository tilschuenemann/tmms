import requests
import pandas as pd
import os
import re
import json
from pandas import json_normalize
from datetime import datetime


def import_folder(parent_folder: str) -> pd.DataFrame():

    if os.path.exists(parent_folder) == False:
        exit("exiting")

    movies_disk = next(os.walk(parent_folder))[1]
    df = pd.DataFrame(movies_disk)
    df.columns = ["disk.fname"]

    if df.empty:
        exit("no subfolders found! exiting")

    df["disk.year"] = df["disk.fname"].str.extract(
        r"\((\d{4})\) \(\w*\)$", expand=False
    )
    df["disk.subtitles"] = df["disk.fname"].str.extract(
        r"\(\d{4}\) \((\w+)\)$", expand=False
    )
    df["disk.title"] = df["disk.fname"].str.extract(
        r"(.*) \(.*\) \(.*\)$", expand=False
    )

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


def main(api_key: str, parent_folder: str, output_fpath: str):

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

    dict_columns_type = {
        "disk.fname": str,
        "disk.year": int,
        "disk.subtitles": str,
        "disk.title": str,
        "tmdb_id_auto": int,
        "production_countries.iso_3166_1": str,
        "production_countries.name": str,
        "adult": str,
        "backdrop_path": str,
        "budget": int,
        "homepage": str,
        "id": int,
        "imdb_id": str,
        "original_language": str,
        "original_title": str,
        "overview": str,
        "popularity": int,
        "poster_path": str,
        "release_date": str,
        "revenue": int,
        "runtime": int,
        "status": str,
        "tagline": str,
        "title": str,
        "video": str,
        "vote_average": float,
        "vote_count": int,
    }

    m_details = m_details.astype(dict_columns_type)

    m_details.to_csv(output_fpath, sep=";", encoding="UTF-8", index=False, decimal=",")
    duration = datetime.now() - start
    print(duration)


if __name__ == "__main__":
    main()

import pandas as pd
from pandas import json_normalize


import argparse
from datetime import datetime
import json
import re
import requests
import os
from progress.bar import Bar


def str_empty(my_string: str):
    if my_string and my_string.strip():
        return False
    else:
        return True


def import_folder(parent_folder: str, style: int) -> pd.DataFrame():
    """Reads the parent_folders subdirectory names,
    extracts title, year and subtitles (if available).
    If a non-existant parent_folder is supplied or if it's
    empty, an empty dataframe will be returned.

    Parameters
    --------
    parent_folder : str
        filepath to folder containing all movies

    Returns
    --------
    pd.DataFrame

    """

    if os.path.exists(parent_folder) == False:
        return pd.DataFrame()

    movies_disk = next(os.walk(parent_folder))[1]
    df = pd.DataFrame(movies_disk)
    df.columns = ["disk.fname"]

    if df.empty:
        return pd.DataFrame()

    if style == 0:
        df["disk.year"] = df["disk.fname"].str.extract(
            r"\((\d{4})\) \(\w*\)$", expand=False
        )
        df["disk.subtitles"] = df["disk.fname"].str.extract(
            r"\(\d{4}\) \((\w+)\)$", expand=False
        )
        df["disk.title"] = df["disk.fname"].str.extract(
            r"(.*) \(.*\) \(.*\)$", expand=False
        )
    elif style == 1:
        df["disk.year"] = df["disk.fname"].str.extract(
            r"(^\d{4})(?= - .+)", expand=False
        )
        df["disk.title"] = df["disk.fname"].str.extract(r"^\d{4} - (.+)", expand=False)
    else:
        return pd.DataFrame()
    return df


def lookup_id(api_key: str, title: str, year: str) -> int():
    """Creates a search get request for TMDB API.
    Searches for combination of title and year first -
    if response is empty another search only using the title
    is performed.

    Incase of multiple results the first one is taken.

    If the supplied title is an empty string or no final
    results can be returned, -1 is returned.

    Parameters
    --------
    api_key : str
        TMDB API key
    title : str
        movie title
    year : str
        movie release year

    Returns
    --------
    int
        TMDB id for first search result
    """

    ERROR_ID = -1
    retry = False

    if str_empty(title):
        return ERROR_ID
    elif str_empty(title) == False and str_empty(year) == False:
        url = f"https://api.themoviedb.org/3/search/movie/?api_key={api_key}&query={title}&year={year}&include_adult=true"
        retry = True
    elif str_empty(title) == False and str_empty(year):
        url = f"https://api.themoviedb.org/3/search/movie/?api_key={api_key}&query={title}&include_adult=true&page=1"

    response = requests.get(url).json()

    try:
        id = int(response["results"][0]["id"])
        return id
    except IndexError:
        if retry:
            url = f"https://api.themoviedb.org/3/search/movie/?api_key={api_key}&query={title}&include_adult=true&page=1"
            response = requests.get(url).json()

            try:
                id = int(response["results"][0]["id"])
                return id
            except IndexError:
                return ERROR_ID
        return ERROR_ID


def lookup_details(api_key: str, m_id: int) -> pd.DataFrame:
    """Queries the TMDB API for movie details for m_id. The
    resulting JSON is flattened and fed into a DataFrame.

    Parameters
    --------
    api_key : str
        TMDB API key
    m_id : int
        TMDB movie id

    Returns
    --------
    pd.DataFrame
        DataFrame containing m_id metadata
    """
    if m_id == -1:
        return pd.DataFrame()

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
    df = df.add_prefix("m.")

    col_types = {
        "m.production_countries.iso_3166_1": str,
        "m.production_countries.name": str,
        "m.adult": str,
        "m.backdrop_path": str,
        "m.budget": int,
        "m.homepage": str,
        "m.id": int,
        "m.imdb_id": str,
        "m.original_language": str,
        "m.original_title": str,
        "m.overview": str,
        "m.popularity": int,
        "m.poster_path": str,
        "m.release_date": str,
        "m.revenue": int,
        "m.runtime": int,
        "m.status": str,
        "m.tagline": str,
        "m.title": str,
        "m.video": str,
        "m.vote_average": float,
        "m.vote_count": int,
    }

    df = df.astype(col_types)

    return df


def lookup_credits(api_key: str, m_id: int) -> pd.DataFrame():
    """Queries the TMDB API for movie cast and crew for m_id. The
    resulting JSON is flattened and fed into a DataFrame.

    Parameters
    --------
    api_key : str
        TMDB API key
    m_id : int
        TMDB movie id

    Returns
    --------
    pd.DataFrame
        DataFrame containing m_id cast and crew
    """
    if m_id == -1:
        return pd.DataFrame()

    url = f"https://api.themoviedb.org/3/movie/{m_id}/credits?api_key={api_key}"
    response = requests.get(url).json()

    response["m_id"] = response.pop("id")

    cast = pd.json_normalize(
        response,
        record_path="cast",
        meta="m_id",
        errors="ignore",
    )

    crew = pd.json_normalize(
        response,
        record_path="crew",
        meta="m_id",
        errors="ignore",
    )

    cast["credit.type"] = "cast"
    crew["credit.type"] = "crew"
    cast_crew = pd.concat([cast, crew], axis=0)
    cast_crew = cast_crew.add_prefix("cc.")
    cast_crew.fillna(0, inplace=True)

    col_types = {
        "cc.adult": bool,
        "cc.gender": int,
        "cc.id": int,
        "cc.known_for_department": str,
        "cc.name": str,
        "cc.original_name": str,
        "cc.popularity": float,
        "cc.profile_path": str,
        "cc.cast_id": int,
        "cc.character": str,
        "cc.credit_id": str,
        "cc.order": int,
        "cc.m_id": int,
        "cc.credit.type": str,
        "cc.department": str,
        "cc.job": str,
    }

    return cast_crew


def main(
    api_key: str,
    parent_folder: str,
    style: int,
    m: bool,
    c: bool,
    output_fpath: str = None,
):

    start = datetime.now()

    if str_empty(api_key):
        exit("no api key supplied")

    df = import_folder(parent_folder, style)

    # API calls for id
    bar = Bar(
        "Ids    ",
        max=len(df.index),
        suffix="%(index)d / %(max)d  %(percent)d%% (ETA %(eta)ds | %(elapsed_td)s)",
    )

    tmdb_id_auto = []
    for index, row in df.iterrows():
        tmdb_id_auto.append(lookup_id(api_key, row["disk.title"], row["disk.year"]))
        bar.next()
    df["tmdb_id_auto"] = tmdb_id_auto
    bar.finish()

    if m is True:
        # API calls for details
        bar = Bar(
            "Details",
            max=len(df.index),
            suffix="%(index)d / %(max)d  %(percent)d%% (ETA %(eta)ds | %(elapsed_td)s)",
        )

        details = pd.DataFrame()
        for index, row in df.iterrows():
            details_tmp = lookup_details(api_key, row["tmdb_id_auto"])
            details = pd.concat([details, details_tmp], axis=0)
            bar.next()
        details = details.reset_index(drop=True)

        bar.finish()

    if c is True:
        # API calls for credits
        bar = Bar(
            "Credits",
            max=len(df.index),
            suffix="%(index)d / %(max)d  %(percent)d%% (ETA %(eta)ds | %(elapsed_td)s)",
        )

        cc = pd.DataFrame()
        for index, row in df.iterrows():
            cc_tmp = lookup_credits(api_key, row["tmdb_id_auto"])
            cc = pd.concat([cc, cc_tmp], axis=0)
            bar.next()
        cc = cc.reset_index(drop=True)

        bar.finish()

    if m is not False:
        df = df.merge(details, left_on="tmdb_id_auto", right_on="m.id")
        df.drop("m.id", axis=1, inplace=True)
    if c is not False:
        df = df.merge(cc, left_on="tmdb_id_auto", right_on="cc.m_id")
        df.drop("cc.m_id", axis=1, inplace=True)

    if output_fpath == None:
        output_fpath = os.getcwd() + "/tmms_table.csv"

    df.to_csv(output_fpath, sep=";", encoding="UTF-8", index=False, decimal=",")

    duration = datetime.now() - start
    print(f"finished in {duration}, saved results to {output_fpath}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Scrape TMDB metadata")
    parser.add_argument(
        "--api_key", dest="api_key", type=str, required=True, help="TMDB api key"
    )
    parser.add_argument(
        "--parent_folder",
        dest="parent_folder",
        type=str,
        required=True,
        help="folder containing movies",
    )

    parser.add_argument(
        "--style", dest="style", type=int, required=True, help="parsing style"
    )

    parser.add_argument(
        "--output_fpath",
        dest="output_fpath",
        type=str,
        required=False,
        help="results get written to this file. If nothing is specified,"
        + "tmms_table.csv gets written to the current working directry.",
    )

    parser.add_argument(
        "--m", action="store_false", help="set flag for skipping movie detail data"
    )
    parser.add_argument(
        "--c", action="store_false", help="set flag for skipping credit data"
    )

    args = parser.parse_args()

    main(
        args.api_key, args.parent_folder, args.style, args.output_fpath, args.m, args.c
    )

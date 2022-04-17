import pandas as pd
from pandas import json_normalize
from tqdm import tqdm
import numpy as np


import argparse
from datetime import datetime
import json
import logging
import re
import requests
import os


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

    df["tmms.id_man"] = 0
    df["tmms.id_auto"] = 0
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


def lcm_merge(df_list: list(pd.DataFrame())) -> pd.DataFrame():
    """For a given list of dataframes, the lowest common multiple
    of their lengths is determined. Every df is copied along its
    rows until their length matches the LCM.
    All df are concatenated and returned.

    If a df has no elements or the LCM is zero, an empty df is
    returned.

    Parameters
    -------
    df_list: list(pd.DataFrame())
        List of dataframes

    Returns
    -------
        pd.DataFrame
    """
    lengths = []
    for df in df_list:
        lengths.append(len(df.index))

    if len(lengths) <= 0:
        return pd.DataFrame()

    lcm = np.lcm.reduce(lengths)
    if lcm <= 0:
        return pd.DataFrame()

    result = pd.DataFrame()

    for datf in df_list:
        df_tmp = datf.copy()
        df_tmp = pd.concat([df_tmp] * int(lcm / len(df_tmp.index)))
        df_tmp.reset_index(drop=True, inplace=True)
        result = pd.concat([result, df_tmp], axis=1)
    return result


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

    df = pd.json_normalize(
        response,
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
        errors="ignore",
    )
    to_unlist = [
        "genres",
        "production_companies",
        "production_countries",
        "spoken_languages",
    ]

    df.drop(
        to_unlist,
        axis=1,
        inplace=True,
    )

    df = df.add_prefix("m.")

    df_list = [df]
    for col in to_unlist:
        tmp_df = pd.json_normalize(response, record_path=col, record_prefix=f"m.{col}.")
        df_list.append(tmp_df)

    df = lcm_merge(df_list)

    col_types = {
        "m.adult": bool,
        "m.backdrop_path": str,
        "m.belongs_to_collection.backdrop_path": str,
        "m.belongs_to_collection.id": "Int64",
        "m.belongs_to_collection.name": str,
        "m.belongs_to_collection.poster_path": str,
        "m.budget": "Int64",
        "m.genres.id": "Int64",
        "m.genres.name": str,
        "m.homepage": str,
        "m.id": "Int64",
        "m.imdb_id": str,
        "m.original_language": str,
        "m.original_title": str,
        "m.overview": str,
        "m.popularity": float,
        "m.poster_path": str,
        "m.production_companies.id": "Int64",
        "m.production_companies.logo_path": str,
        "m.production_companies.name": str,
        "m.production_companies.origin_country": str,
        "m.production_countries.iso_3166_1": str,
        "m.production_countries.name": str,
        "m.release_date": str,
        "m.revenue": "Int64",
        "m.runtime": "Int64",
        "m.spoken_languages.english_name": str,
        "m.spoken_languages.iso_639_1": str,
        "m.spoken_languages.name": str,
        "m.status": str,
        "m.tagline": str,
        "m.title": str,
        "m.video": bool,
        "m.vote_average": float,
        "m.vote_count": "Int64",
    }

    for key, value in col_types.items():
        if key in df.columns:
            df[key] = df[key].astype({key: value})

    if "m.belongs_to_collection" in df.columns:
        df.drop("m.belongs_to_collection", inplace=True, axis=1)

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

    response["m.id"] = response.pop("id")

    cast = pd.json_normalize(
        response,
        record_path="cast",
        meta="m.id",
        errors="ignore",
    )

    crew = pd.json_normalize(
        response,
        record_path="crew",
        meta="m.id",
        errors="ignore",
    )

    cast["credit.type"] = "cast"
    crew["credit.type"] = "crew"
    cast_crew = pd.concat([cast, crew], axis=0)
    cast_crew = cast_crew.add_prefix("cc.")

    col_types = {
        "cc.adult": bool,
        "cc.gender": "Int64",
        "cc.id": "Int64",
        "cc.known_for_department": str,
        "cc.name": str,
        "cc.original_name": str,
        "cc.popularity": float,
        "cc.profile_path": str,
        "cc.cast_id": "Int64",
        "cc.character": str,
        "cc.credit_id": str,
        "cc.order": "Int64",
        "cc.m.id": "Int64",
        "cc.credit.type": str,
        "cc.department": str,
        "cc.job": str,
    }

    for key, value in col_types.items():
        if key in cast_crew.columns:
            cast_crew[key] = cast_crew[key].astype({key: value})

    return cast_crew


def update_lookup_table(
    api_key: str, parent_folder: str, style: int, lookuptab_path: str = None
) -> pd.DataFrame:
    """Creates or updates the lookup table.

    Parameters
    --------
    api_key : str
        TMDB API key
    parent_folder : str
        filepath to folder containing all movies
    style : int
        parsing style
    lookuptab_path : str
        (Optional) path to lookup table

    Returns
    --------
    pd.DataFrame
        updated lookup table
    """
    df = import_folder(parent_folder, style)

    if lookuptab_path == None:
        lookuptab_path = os.getcwd() + "/tmms_lookuptab.csv"
        logging.info(f"creating new lookuptable at {lookuptab_path}")
    if os.path.exists(lookuptab_path):
        logging.info("lookuptable already exists")

        df_stale = pd.read_csv(lookuptab_path, sep=";", encoding="UTF-8")
        diff = df[~(df["disk.fname"].isin(df_stale["disk.fname"]))]
        df = pd.concat([df_stale, diff], axis=0)
        df["tmms.id_auto"] = df["tmms.id_auto"].fillna(-2).astype(int)
        df.reset_index(drop=True)

    # GET IDs

    auto_ids = []
    for index, row in tqdm(df.iterrows(), desc="IDs    ", total=len(df["disk.fname"])):
        fname = row["disk.fname"]

        if row["tmms.id_man"] != 0:
            auto_ids.append(row["tmms.id_auto"])
            logging.info(f"{fname}: tmms.id_man entered")
        elif int(row["tmms.id_auto"]) > 0:
            auto_ids.append(row["tmms.id_auto"])
            logging.info(f"{fname}: tmms.id_auto already exists")
        else:
            new_id = lookup_id(api_key, row["disk.title"], str(row["disk.year"]))
            auto_ids.append(new_id)
            if new_id == -1:
                logging.info(f"{fname}: tmms.id_auto not found")
            else:
                logging.info(f"{fname}: tmms.id_auto found {new_id}")

    df["tmms.id_auto"] = auto_ids
    return df


def get_metadata(api_key: str, id_list: list, m: bool, c: bool) -> pd.DataFrame:
    """Query TMDB for movie metadata or credits for specified ids.

    Parameters
    --------
    api_key : str
        tmdb API key
    id_list : list
        list of ids
    m : bool
        flag for pulling movie metadata
    c : bool
        flag for pulling credits

    Returns
    --------
        DataFrame containing metadata and/or credits for supplied
        id_list
    """
    if (m == False and c == False) or not id_list:
        return pd.DataFrame()

    # GET DETAILS
    if m:
        details = pd.DataFrame()
        for movie_id in tqdm(id_list, desc="Details"):
            tmp = lookup_details(api_key, movie_id)
            details = pd.concat([details, tmp], axis=0)
        details.reset_index(drop=True)
        details.replace("None", "", inplace=True)

    # GET CREDITS
    if c:
        cast_crew = pd.DataFrame()
        for movie_id in tqdm(id_list, desc="Credits"):
            tmp = lookup_credits(api_key, movie_id)
            cast_crew = pd.concat([cast_crew, tmp], axis=0)
        cast_crew.reset_index(drop=True)
        cast_crew.replace("nan", "", inplace=True)
        cast_crew.replace("None", "", inplace=True)

    # merge, sort and ave
    if m and c:
        df = details.merge(cast_crew, left_on="m.id", right_on="cc.m.id")
    elif m:
        df = details
    elif c:
        df = cast_crew

    df = df[sorted(df.columns)]
    return df


def write_to_disk(
    df: pd.DataFrame,
    default_name: str,
    path: str = None,
):
    """Write df to path. If path is not specified, it is written
    to as default_name.csv to the working directory.

    Parameters
    --------
    df : pd.DataFrame
        DataFrame to be written.
    default_name : str
        Name to use for writing if no path is supplied.
    path : str
        Optional, path to write df to.
    """
    if path == None:
        path = os.getcwd() + f"/{default_name}.csv"

    df.to_csv(
        path,
        sep=";",
        encoding="UTF-8",
        index=False,
        decimal=",",
        date_format="%Y-%m-%d",
    )
    print(f"saved {default_name}.csv to {path}")


def main(
    api_key: str,
    parent_folder: str,
    style: int,
    m: bool,
    c: bool,
    lookuptab_path: str = None,
    metadata_path: str = None,
):

    logger = logging.getLogger("tmmslogger")
    logging.basicConfig(
        filename="./tmms-log.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s",
    )

    logging.info(
        "start parameters:\n"
        + f"parent_folder: {parent_folder}\n"
        + f"style: {style}\n"
        + f"m: {m}\n"
        + f"c: {c}\n"
        + f"lookuptab_path: {lookuptab_path}\n"
        + f"metadata_path: {metadata_path}"
    )

    start = datetime.now()

    if str_empty(api_key):
        exit("no api key supplied")

    lookup_df = update_lookup_table(api_key, parent_folder, 0, lookuptab_path)

    write_to_disk(lookup_df, "tmms_lookuptab", lookuptab_path)

    unique_ids = np.where(
        lookup_df["tmms.id_man"] != 0,
        lookup_df["tmms.id_man"],
        lookup_df["tmms.id_auto"],
    )
    unique_ids = list(dict.fromkeys(unique_ids))

    if m or c:
        metadata_df = get_metadata(api_key, unique_ids, m, c)
        write_to_disk(metadata_df, "tmms_metadata", metadata_path)

    duration = datetime.now() - start
    print(f"finished in {duration}")


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
        "--lookuptab_path",
        dest="lookuptab_path",
        type=str,
        required=False,
        help="results get written to this file. If nothing is specified,"
        + "tmms_lookuptab.csv gets written to the current working directry.",
    )

    parser.add_argument(
        "--metadata_path",
        dest="metadata_path",
        type=str,
        required=False,
        help="metadata gets written to this file. If nothing is specified,"
        + "tmms_metadata.csv gets written to the current working directry.",
    )

    parser.add_argument(
        "--m", action="store_true", help="set flag for pulling movie detail data"
    )
    parser.add_argument(
        "--c", action="store_true", help="set flag for pulling credit data"
    )

    args = parser.parse_args()

    main(
        api_key=args.api_key,
        parent_folder=args.parent_folder,
        style=args.style,
        c=args.c,
        m=args.m,
        lookuptab_path=args.lookuptab_path,
        metadata_path=args.metadata_path,
    )

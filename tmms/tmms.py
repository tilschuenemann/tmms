import pandas as pd
from tqdm import tqdm
import numpy as np


import argparse
from datetime import datetime
import json
import logging
import re
import requests
import os


def str_empty(my_string: str) -> bool:
    """Helper to check for empty strings"""
    if my_string and my_string.strip():
        return False
    else:
        return True


def import_folder(input_folder: str, style: int) -> pd.DataFrame():
    """Reads the input_folder subdirectory names,
    extracts title, year and subtitles (if available).

    If a non-existant parent_folder is supplied or if it's
    empty, an empty dataframe will be returned.

    Parameters
    --------
    input_folder : str
        filepath to folder containing all movies
    style : int
        parsing style
    Returns
    --------
    pd.DataFrame

    """

    if os.path.exists(input_folder) == False:
        return pd.DataFrame()

    movies_disk = next(os.walk(input_folder))[1]
    if len(movies_disk) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(movies_disk, columns=["disk.fname"])

    if style == 0:
        extract = df["disk.fname"].str.extract(
            r"(?P<title>^.*) \((?P<year>\d{4})\) \((?P<subtitles>.*)\)$"
        )
    elif style == 1:
        extract = df["disk.fname"].str.extract(r"^(?P<year>\d{4}) - (?P<title>.*)$")

    extract = extract.add_prefix("disk.")
    extract = extract.fillna(-1)
    extract = extract.replace(r"^\s*$", -1, regex=True)

    df = pd.concat([df, extract], axis=1)

    df["tmms.id_man"] = 0
    df["tmms.id_auto"] = 0
    return df


def lookup_id(api_key: str, title: str, year: str = None) -> int:
    """Creates a search get request for TMDB API.

    Searches for combination of title and year first -
    if response is empty another search only using the title
    is performed.

    Incase of multiple results the first one is taken.

    If the supplied title is an empty string or nothing
    is found, -1 is returned.


    Parameters
    -------
    api_key : str
        TMDB API key
    title : str
        movie title
    year : str
        movie release year

    Returns
    -------
    int
        TMDB id

    """
    if str_empty(api_key) or str_empty(title):
        return -1

    if year is not None:
        url = f"https://api.themoviedb.org/3/search/movie/?api_key={api_key}&query={title}&year={year}&include_adult=true"
        response = requests.get(url).json()

        try:
            mid = int(response["results"][0]["id"])
            return mid
        except IndexError:
            return lookup_id(api_key, title)

    elif year is None:
        url = f"https://api.themoviedb.org/3/search/movie/?api_key={api_key}&query={title}&include_adult=true"
        response = requests.get(url).json()

        try:
            mid = int(response["results"][0]["id"])
            return mid
        except IndexError:
            return -1


def lookup_details(response: dict) -> pd.DataFrame:
    """Queries the TMDB API for movie details for m_id. The
    resulting JSON is flattened and fed into a DataFrame.

    Parameters
    --------
    response : dict
        TMDB API response for movie endpoint

    Returns
    --------
    pd.DataFrame
        DataFrame containing m_id metadata
    """

    df = pd.json_normalize(
        response,
        errors="ignore",
    )

    df.drop(
        [
            "belongs_to_collection",
            "genres",
            "production_companies",
            "production_countries",
            "spoken_languages",
        ],
        axis=1,
        inplace=True,
        errors="ignore",
    )

    df = df.add_prefix("m.")

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
    api_key: str, input_folder: str, style: int, output_folder: str
) -> pd.DataFrame:
    """Creates or updates the lookup table.

    If a lookup table exists in the output folder, it's compared
    to the actual files on disk. The difference gets added to df.

    If a manual or an automatic id exist, they are kept. Missing
    or new automatic ids are filled in with -2, which get looked
    up.

    The list of automatic ids overwrites itself.

    Parameters
    --------
    api_key : str
        TMDB API key
    input_folder : str
        folder containing all movies
    style : int
        parsing style
    output_folder : str
        folder to write lookup table to

    Returns
    --------
    pd.DataFrame
        updated lookup table
    """
    df = import_folder(input_folder, style)
    lookuptab = output_folder + "/tmms_lookuptab.csv"

    if os.path.exists(lookuptab):
        logging.info("lookuptable already exists")

        df_stale = pd.read_csv(lookuptab, sep=";", encoding="UTF-8")
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


def write_to_disk(
    df: pd.DataFrame,
    output_path: str,
):
    """Write df to output_path with European settings.

    Parameters
    --------
    df : pd.DataFrame
        DataFrame to be written.
    output_path : str
        Optional, path to write df to.
    """
    df.to_csv(
        output_path,
        sep=";",
        encoding="UTF-8",
        index=False,
        decimal=",",
        date_format="%Y-%m-%d",
    )
    logging.info(f"saved {output_path}")


def unnest(response: dict, mid: int, column: str) -> pd.DataFrame:
    """Unnests column in specified response and adds mid as identifier.

    Parameters
    -------
    response : dict
        JSON response from API
    mid : int
        movie id to add as identifier
    column : str
        column to unnest

    Returns
    -------
    pd.DataFrame
        unnested DataFrame
    """
    df = pd.json_normalize(response, record_path=column)
    df["m.id"] = mid
    return df


def main(
    api_key: str,
    input_folder: str,
    style: int,
    m: bool,
    c: bool,
    output_folder: str,
):
    # check inputs
    if str_empty(api_key):
        exit("no api key supplied")
    if os.path.isdir(input_folder) == False:
        exit("input folder doesnt exit or is not a directory")
    elif os.path.isdir(output_folder) == False:
        exit("output folder doesnt exit or is not a directory")
    elif style not in range(0, 2):
        exit("style not in range")

    # setup logging
    logger = logging.getLogger("tmmslogger")
    logging.basicConfig(
        filename=output_folder + "/tmms-log.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s",
    )

    logging.info(
        "start parameters:\n"
        + f"input_folder: {input_folder}\n"
        + f"style: {style}\n"
        + f"m: {m}\n"
        + f"c: {c}\n"
        + f"output_folder: {output_folder}"
    )

    start = datetime.now()

    # update or create lookup table
    lookup_df = update_lookup_table(api_key, input_folder, style, output_folder)
    write_to_disk(lookup_df, output_folder + "tmms_lookuptab.csv")

    # get ids to lookup
    if m or c:
        unique_ids = np.where(
            lookup_df["tmms.id_man"] != 0,
            lookup_df["tmms.id_man"],
            lookup_df["tmms.id_auto"],
        )
        unique_ids = list(dict.fromkeys(unique_ids))
        unique_ids.remove(-1) if -1 in unique_ids else None

    if m:
        details = pd.DataFrame()
        genres = pd.DataFrame()
        prod_comp = pd.DataFrame()
        prod_count = pd.DataFrame()
        spoken_langs = pd.DataFrame()

        for mid in tqdm(unique_ids, "Details"):

            url = f"https://api.themoviedb.org/3/movie/{mid}?api_key={api_key}&include_adult=true"
            response = requests.get(url).json()

            tmp = lookup_details(response)
            details = pd.concat([details, tmp], axis=0)

            to_unlist = [
                "genres",
                "production_companies",
                "production_countries",
                "spoken_languages",
            ]

            for col in to_unlist:
                tmp = unnest(response, mid, col)

                if col == "genres":
                    genres = pd.concat([genres, tmp], axis=0)
                elif col == "production_companies":
                    prod_comp = pd.concat([prod_comp, tmp], axis=0)
                elif col == "production_countries":
                    prod_count = pd.concat([prod_count, tmp], axis=0)
                elif col == "spoken_languages":
                    spoken_langs = pd.concat([spoken_langs, tmp], axis=0)

        details.replace("None", "", inplace=True)
        genres.add_prefix("genres.")
        prod_comp.add_prefix("production_countries.")
        prod_count.add_prefix("production_countries.")
        spoken_langs.add_prefix("spoken_languages.")

        write_to_disk(details, output_folder + "tmms_moviedetails.csv")
        write_to_disk(genres, output_folder + "tmms_genres.csv")
        write_to_disk(prod_comp, output_folder + "tmms_production_companies.csv")
        write_to_disk(prod_count, output_folder + "tmms_production_countries.csv")
        write_to_disk(spoken_langs, output_folder + "tmms_spoken_languages.csv")

    if c:
        cast_crew = pd.DataFrame()

        for mid in tqdm(unique_ids, "Credits"):
            tmp = lookup_credits(api_key, mid)
            cast_crew = pd.concat([cast_crew, tmp], axis=0)

        cast_crew.replace("nan", "", inplace=True)
        cast_crew.replace("None", "", inplace=True)
        write_to_disk(cast_crew, output_folder + "tmms_credits.csv")

    duration = datetime.now() - start
    logger.info(f"finished in {duration}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Scrape TMDB metadata")
    parser.add_argument(
        "--api_key", dest="api_key", type=str, required=True, help="TMDB API key"
    )
    parser.add_argument(
        "--input_folder",
        dest="input_folder",
        type=str,
        required=True,
        help="folder containing movies",
    )

    parser.add_argument(
        "--style", dest="style", type=int, required=True, help="parsing style"
    )

    parser.add_argument(
        "--output_folder",
        dest="output_folder",
        type=str,
        required=True,
        help="Folder to write results to. If nothing is specified,"
        + "files get written to the current working directry.",
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
        input_folder=args.input_folder,
        style=args.style,
        c=args.c,
        m=args.m,
        output_folder=args.output_folder,
    )

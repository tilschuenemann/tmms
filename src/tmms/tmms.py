import pandas as pd  # type: ignore
from tqdm import tqdm  # type: ignore
import numpy as np


import argparse
from datetime import datetime
import logging
import requests  # type: ignore
import os


def _str_empty(my_string: str) -> bool:
    """Helper to check for empty strings

    Parameter
    -------
    my_string: str
        string to check

    Returns
    -------
    bool
        whether string is empty
    """
    if my_string and my_string.strip():
        return False
    else:
        return True


def _guess_convention(item_names: list[str]) -> int:
    """Takes a list of item names and checks,
    if they fit one of the defined styles.

    The styles id is then returned.

    A match is returned if every item matches
    the regex of a style.

    Parameters:
    -------
    item_names : list
        list to be checked against naming conventions

    Returns
    -------
    int
        style id
    """

    my_style = -1

    styles_for_convention = {
        0: r"(^.*\s\(\d{4}\)\s\(.*\)$)",
        1: r"(^\d{4}\s-\s.*$)",
        2: r"(.*)",
    }

    df = pd.DataFrame(item_names, columns=["fnames"])

    for style, regex in styles_for_convention.items():
        result = df["fnames"].str.extract(regex)
        match = len(result[result.isnull().any(axis=1)]) == 0
        if match:
            my_style = style

    return my_style


def generic_id_lookup(item_names: list[str], style: int = -1) -> pd.DataFrame:
    """

    Parameters
    -------
    item_names: list
        List of movie title strings
    style: int
        (Optional) style id
    Returns
    -------
    pd.DataFrame
        DataFrame containing items, their extracts according
        to convention and their TMDB id
    """

    if len(item_names) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(item_names, columns=["disk.fname"])

    if style == -1:
        style = _guess_convention(item_names)

    df = pd.DataFrame(item_names, columns=["disk.fname"])
    df["tmms.id_man"] = 0
    df["tmms.id_auto"] = 0

    if style == -1:
        exit("no style could be guessed, please supply style yourself")
    if style == 0:
        extract = df["disk.fname"].str.extract(
            r"(?P<title>^.*) \((?P<year>\d{4})\) \((?P<subtitles>.*)\)$"
        )
    elif style == 1:
        extract = df["disk.fname"].str.extract(r"^(?P<year>\d{4}) - (?P<title>.*)$")
    elif style == 2:
        extract = df["disk.fname"].str.extract(r"^(?P<title>.*)$")

    extract = extract.add_prefix("disk.")
    extract = extract.fillna(-1)
    extract = extract.replace(r"^\s*$", -1, regex=True)

    df = pd.concat([df, extract], axis=1)
    return df


def import_folder(input_folder: str, style: int = -1) -> pd.DataFrame:
    """Passes the contents of the input folder as item_list to
    generic_id_lookup.

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

    if os.path.exists(input_folder) is False:
        return pd.DataFrame()

    movies_disk = next(os.walk(input_folder))[1]

    df = generic_id_lookup(movies_disk, style)

    return df


def get_id(api_key: str, strict: bool, title: str, year: str = "") -> int:
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
    strict : bool
        if strict==False, another lookup without the year will be performed
    title : str
        movie title
    year : str
        movie release year

    Returns
    -------
    int
        TMDB id

    """
    if _str_empty(api_key) or _str_empty(title):
        return -1

    if _str_empty(year) is False:
        url = f"https://api.themoviedb.org/3/search/movie/?api_key={api_key}&query={title}&year={year}&include_adult=true"
        response = requests.get(url).json()

        try:
            mid = int(response["results"][0]["id"])
            return mid
        except IndexError:
            return get_id(api_key=api_key, strict=strict, title=title)

    else:
        if strict:
            return -1

        url = f"https://api.themoviedb.org/3/search/movie/?api_key={api_key}&query={title}&include_adult=true"
        response = requests.get(url).json()

        try:
            mid = int(response["results"][0]["id"])
            return mid
        except IndexError:
            return -1


def _update_lookup_table(
    api_key: str, input_folder: str, output_folder: str, strict: bool, style: int = -1
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
    output_folder : str
        folder to write lookup table to
    style : int
        parsing style

    Returns
    --------
    pd.DataFrame
        updated lookup table
    """
    df = import_folder(input_folder, style)
    lookuptab = output_folder + "/tmms_lookuptab.csv"

    if os.path.exists(lookuptab):
        df_stale = pd.read_csv(lookuptab, sep=";", encoding="UTF-8")
        diff = df[~(df["disk.fname"].isin(df_stale["disk.fname"]))]
        df = pd.concat([df_stale, diff], axis=0)
        df["tmms.id_auto"] = df["tmms.id_auto"].fillna(-2).astype(int)
        df.reset_index(drop=True)

    # GET IDs

    auto_ids = []
    for index, row in tqdm(df.iterrows(), desc="IDs    ", total=len(df["disk.fname"])):
        fname = row["disk.fname"]
        auto_id = int(row["tmms.id_auto"])
        man_id = int(row["tmms.id_man"])
        title = row["disk.title"]
        year = str(row["disk.year"])

        if man_id != 0 or auto_id > 0:
            auto_ids.append(auto_id)
        else:
            new_id = get_id(api_key=api_key, strict=strict, title=title, year=year)
            auto_ids.append(new_id)

    df["tmms.id_auto"] = auto_ids
    return df


def get_credits(
    api_key: str, id_list: list[int], language: str = "en-US"
) -> pd.DataFrame:
    """
    Parameters
    api_key: str
        TMDB API key
    id_list: list
        list of TMDB ids

    Returns
    -------
    pd.DataFrame
        credits
    """
    cast_crew = pd.DataFrame()

    for mid in tqdm(id_list, "Credits"):

        url = f"https://api.themoviedb.org/3/movie/{mid}/credits?api_key={api_key}&language={language}"
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
        tmp = pd.concat([cast, crew], axis=0)
        cast_crew = pd.concat([cast_crew, tmp], axis=0)

    cast_crew = cast_crew.add_prefix("cc.")

    col_types = {
        "cc.adult": bool,
        "cc.gender": int,
        "cc.id": int,
        "cc.known_for_department": str,
        "cc.name": str,
        "cc.original_name": str,
        "cc.popularity": float,
        "cc.profile_path": str,
        "cc.cast_id": float,
        "cc.character": str,
        "cc.credit_id": str,
        "cc.order": float,
        "cc.m.id": int,
        "cc.credit.type": str,
        "cc.department": str,
        "cc.job": str,
    }

    for key, value in col_types.items():
        if key in cast_crew.columns:
            cast_crew[key] = cast_crew[key].astype({key: value})

    cast_crew.replace("nan", None, inplace=True)
    cast_crew.replace("None", None, inplace=True)

    return cast_crew


def get_details(
    api_key: str, id_list: list[int], language: str = "en-US"
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Parameters
    -------
    api_key: str
        TMBD API key
    id_list: list
        list of TMDB ids

    Returns
    -------
    pd.DataFrame
        movie details
    pd.DataFrame
        genres
    pd.DataFrame
        production companies
    pd.DataFrame
        production countries
    pd.DataFrame
        spoken languages
    """
    details = pd.DataFrame()
    genres = pd.DataFrame()
    prod_comp = pd.DataFrame()
    prod_count = pd.DataFrame()
    spoken_langs = pd.DataFrame()

    to_unlist = [
        "genres",
        "production_companies",
        "production_countries",
        "spoken_languages",
    ]

    for mid in tqdm(id_list, "Details"):

        url = f"https://api.themoviedb.org/3/movie/{mid}?api_key={api_key}&include_adult=true&language={language}"
        response = requests.get(url).json()

        tmp = pd.json_normalize(
            response,
            errors="ignore",
        )

        tmp.drop(
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

        details = pd.concat([details, tmp], axis=0)

        for col in to_unlist:
            tmp = pd.json_normalize(response, record_path=col)
            tmp["m.id"] = mid

            if col == "genres":
                genres = pd.concat([genres, tmp], axis=0)
            elif col == "production_companies":
                prod_comp = pd.concat([prod_comp, tmp], axis=0)
            elif col == "production_countries":
                prod_count = pd.concat([prod_count, tmp], axis=0)
            elif col == "spoken_languages":
                spoken_langs = pd.concat([spoken_langs, tmp], axis=0)

    genres = genres.astype({"id": int, "name": str, "m.id": int})
    genres = genres.add_prefix("genres.")

    prod_comp = prod_comp.astype(
        {"id": int, "logo_path": str, "name": str, "origin_country": str, "m.id": int}
    )
    prod_comp = prod_comp.add_prefix("production_companies.")
    prod_comp.replace("None", "", inplace=True)

    prod_count = prod_count.astype({"iso_3166_1": str, "name": str, "m.id": int})
    prod_count = prod_count.add_prefix("production_countries.")

    spoken_langs = spoken_langs.astype(
        {"english_name": str, "iso_639_1": str, "name": str, "m.id": int}
    )
    spoken_langs = spoken_langs.add_prefix("spoken_languages.")

    details = details.astype(
        {
            "adult": bool,
            "backdrop_path": str,
            "budget": int,
            "homepage": str,
            "id": int,
            "imdb_id": str,
            "original_language": str,
            "original_title": str,
            "overview": str,
            "popularity": float,
            "poster_path": str,
            "release_date": str,
            "revenue": int,
            "runtime": int,
            "status": str,
            "tagline": str,
            "title": str,
            "video": bool,
            "vote_average": float,
            "vote_count": int,
        }
    )
    details.replace("None", "", inplace=True)
    details = details = details.add_prefix("m.")

    return details, genres, prod_comp, prod_count, spoken_langs


def _write_to_disk(
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


def main(
    api_key: str,
    input_folder: str,
    output_folder: str,
    m: bool,
    c: bool,
    strict: bool,
    style: int = -1,
):
    # check inputs
    if _str_empty(api_key):
        exit("no api key supplied")
    if os.path.isdir(input_folder) is False:
        exit("input folder doesnt exit or is not a directory")
    elif os.path.isdir(output_folder) is False:
        exit("output folder doesnt exit or is not a directory")
    elif style is not None and style not in range(0, 2):
        exit("style not in range")

    start = datetime.now()

    # update or create lookup table
    lookup_df = _update_lookup_table(
        api_key, input_folder, output_folder, strict, style
    )
    _write_to_disk(lookup_df, output_folder + "tmms_lookuptab.csv")

    # get ids to lookup
    if m or c:
        unique_ids: list[int] = np.ndarray.tolist(
            np.where(
                lookup_df["tmms.id_man"] != 0,
                lookup_df["tmms.id_man"],
                lookup_df["tmms.id_auto"],
            )
        )

        unique_ids = list(dict.fromkeys(unique_ids))
        unique_ids.remove(-1) if -1 in unique_ids else None

    if m:
        details, genres, prod_comp, prod_count, spoken_langs = get_details(
            api_key, unique_ids
        )

        _write_to_disk(details, output_folder + "tmms_moviedetails.csv")
        _write_to_disk(genres, output_folder + "tmms_genres.csv")
        _write_to_disk(prod_comp, output_folder + "tmms_production_companies.csv")
        _write_to_disk(prod_count, output_folder + "tmms_production_countries.csv")
        _write_to_disk(spoken_langs, output_folder + "tmms_spoken_languages.csv")

    if c:
        cast_crew = get_credits(api_key, unique_ids)
        _write_to_disk(cast_crew, output_folder + "tmms_credits.csv")

    duration = datetime.now() - start


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

    parser.add_argument("--s", action="store_true", help="set flag for no more lookups")

    parser.add_argument(
        "--style", dest="style", type=int, required=False, help="parsing style"
    )

    args = parser.parse_args()

    main(
        api_key=args.api_key,
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        m=args.m,
        c=args.c,
        strict=args.s,
        style=args.style,
    )

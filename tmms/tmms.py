import pandas as pd  # type: ignore
from tqdm import tqdm  # type: ignore
import numpy as np


import argparse
import requests  # type: ignore
import os


def _str_empty(my_string: str) -> bool:
    """Helper to check for empty strings

    :param my_string: str to check
    :returns: True if my_string is empty
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

    :param items_names:
        list to be checked against naming conventions
    :returns: style id
    """

    my_style = -1

    styles_for_convention = {
        0: r"(^.*\s\(\d{4}\)\s\(.*\)$)",
        1: r"(^\d{4}\s-\s.*$)",
        2: r"(.*)",
    }

    df = pd.DataFrame(item_names, columns=["item"])

    for style, regex in styles_for_convention.items():
        result = df["item"].str.extract(regex)
        match = len(result[result.isnull().any(axis=1)]) == 0
        if match:
            my_style = style

    return my_style


def _update_lookup_table(
    api_key: str, strict: bool, input_folder: str, output_folder: str, style: int = -1
):
    fresh_items = next(os.walk(input_folder))[1]

    if len(fresh_items) == 0:
        exit("input folder empty")

    lookuptab = f"{output_folder}/tmms_lookuptab.csv"

    if os.path.exists(lookuptab) is False:
        lookup_df = get_ids(
            api_key=api_key, strict=True, item_names=fresh_items, style=style
        )
        lookup_df["tmdb_id_man"] = 0
    else:
        stale_items = pd.read_csv(lookuptab, sep=";", encoding="UTF-8")

        list_with_ids = stale_items[
            (stale_items["tmdb_id"] >= 0) | (stale_items["tmdb_id_man"] != 0)
        ]

        list_without_ids = stale_items[
            (stale_items["tmdb_id"] < 0) & (stale_items["tmdb_id_man"] == 0)
        ]["item"].tolist()

        list_new_items = list(
            set(list_without_ids) | (set(fresh_items) - set(list_with_ids["item"]))
        )

        renewed = get_ids(api_key, strict, list_new_items, style=style)
        renewed["tmdb_id_man"] = 0
        lookup_df = pd.concat([list_with_ids, renewed], axis=0)

        lookup_df = lookup_df.reset_index(drop=True)

    lookup_df = lookup_df.sort_values(by="item")

    _write_to_disk(lookup_df, f"{output_folder}tmms_lookuptab.csv")
    return lookup_df


def get_id(api_key: str, strict: bool, title: str, year: str = "") -> int:
    """Creates a search get request for TMDB API.

    Searches for combination of title and year first -
    if response is empty another search only using the title
    is performed.

    Incase of multiple results the first one is taken.

    If the supplied title is an empty string or nothing
    is found, -1 is returned.

    :param api_key: TMDB API key
    :param strict: if strict==False, another lookup without the year will be performed
    :param title: movie title
    :param year: movie release year
    :returns: TMDB id
    """
    if _str_empty(api_key) or _str_empty(title):
        return -1

    if _str_empty(year) is False:
        url = (
            f"https://api.themoviedb.org/3/search/movie/?api_key={api_key}"
            + f"&query={title}&year={year}&include_adult=true"
        )
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


def get_ids(
    api_key: str, strict: bool, item_names: list[str], style: int = -1
) -> pd.DataFrame:

    if len(item_names) == 0:
        return pd.DataFrame()

    if style == -1:
        style = _guess_convention(item_names)

    df = pd.DataFrame(item_names, columns=["item"])

    if style == -1:
        exit("no style could be guessed, please supply style yourself")
    elif style == 0:
        extract = df["item"].str.extract(
            r"(?P<title>^.*) \((?P<year>\d{4})\) \((?P<subtitles>.*)\)$"
        )
    elif style == 1:
        extract = df["item"].str.extract(r"^(?P<year>\d{4}) - (?P<title>.*)$")
    elif style == 2:
        extract = df["item"].str.extract(r"^(?P<title>.*)$")

    extract = extract.fillna(-1)
    extract = extract.replace(r"^\s*$", -1, regex=True)

    df = pd.concat([df, extract], axis=1)
    df.reset_index()

    tmdb_ids = []
    for index, row in tqdm(df.iterrows(), desc="IDs    ", total=len(df["item"])):
        title = row["title"]

        if style == 0 or style == 1:
            year = str(row["year"])
        else:
            year = ""

        new_id = get_id(api_key=api_key, strict=strict, title=title, year=year)
        tmdb_ids.append(new_id)

    df["tmdb_id"] = tmdb_ids

    df.drop(["title", "year", "subtitles"], axis=1, inplace=True, errors="ignore")

    return df


def get_credits(
    api_key: str, id_list: list[int], language: str = "en-US"
) -> pd.DataFrame:
    """

    :param api_key: TMDB API key
    :param id_list: .ist of TMDB ids
    :returns: credits as dataframe
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
    
    :param api_key: TMDB API key
    :param id_list: list of TMDB ids
    :returns: dfs movie_details, genres, production companies, production countr
    ies, spoken languages
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

    :param df: dataframe to be written
    :param output_path: path to write df to
    """
    df.to_csv(
        output_path,
        sep=";",
        encoding="UTF-8",
        index=False,
        decimal=",",
        date_format="%Y-%m-%d",
    )


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

    # update or create lookup table
    lookup_df = _update_lookup_table(
        api_key, strict, input_folder, output_folder, style
    )
    _write_to_disk(lookup_df, output_folder + "tmms_lookuptab.csv")

    # get ids to lookup
    if m or c:
        unique_ids: list[int] = np.ndarray.tolist(
            np.where(
                lookup_df["tmdb_id_man"] != 0,
                lookup_df["tmdb_id_man"],
                lookup_df["tmdb_id"],
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

# :movie_camera: TMDB Movie Metadata Scraper

This program creates a CSV with movie metadata from the TMDB for every folder inside the parent folder.

The supported naming convention is "movie title (4-digit year) (word)"
```
The Matrix (1999) (subs)
```

## Usage
```python
import tmms

tmms.main(api_key = "MY_API_KEY", 
          parent_folder="/home/til/my_movie_library", 
          style=0, 
          m=True,
          c=True)
```

Alternatively the script can be called from the command line
```bash
python tmms.py 
    --api_key="MY_API_KEY" 
    --parent_folder = "/home/til/my_movie_library" 
    --style=0
```

For every subfolder the TMDB API is queried. Incase of multiple results for querying with title and year, the most popular one is kept. If there no results, another query only including the title is sent.

The resulting dataframe is flattened; eg. one movie with two genres will feature two rows with different genres. 

## How it works

Two files are created:
1. a lookup table where all subfolders and their title, year is stored
2. the metadata file for movie details and cast

If no lookup table exists, the parent_folders contents are parsed into a dataframe. Two additional columns
are created, tmms.id_auto and tmms.id_man.

Incase a lookup file exists, it is read and compared to the actual directory. New folders get appended.

For all rows the TMDB is searched and the most populars result id is written into tmms.id_auto.

tmms.id_man and tmms.id_auto are coalesced so that the automatic id is overwritten by the manual one.
Duplicate ids get removed from that list.

Depending on the m or c flag, movie details and respective credits are pulled from the TMDB API.
If both flags are set, results get joined by the TMDB id and written to disk as metadata file.
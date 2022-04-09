# TMDB Movie Metadata Scraper

This program creates a CSV with movie metadata from the TMDB for every folder inside the parent folder.
Supported naming convention:
| movie title (release year) (subtitle shorthand)

## Documentation
```python
import tmms
api_key = "MY_API_KEY"
parent_folder = "/home/til/my_movie_library"

main.main(api_key, parent_folder)
```

For every subfolder the TMDB API is queried. Incase of multiple results for querying with title and year, the most popular one is kept. If there no results, another query only including the year is sent.

The resulting dataframe is flattened; eg. one movie with two genres will feature two rows with different genres. 

## Todo
* output arg
* check for naming convention of folders
* cast datatypes before returning dfs
* prefix original
* custom id column for manual ids
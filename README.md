# :movie_camera: TMDB Movie Metadata Scraper

This program creates a CSV with movie metadata from the TMDB for every folder inside the parent folder.

The supported naming convention is "movie title (4-digit year) (word)"
```
The Matrix (1999) (subs)
```

## Documentation
```python
import tmms
api_key = "MY_API_KEY"
parent_folder = "/home/til/my_movie_library"

tmms.main(api_key, parent_folder,"./metadata-table.csv")
```

For every subfolder the TMDB API is queried. Incase of multiple results for querying with title and year, the most popular one is kept. If there no results, another query only including the year is sent.

The resulting dataframe is flattened; eg. one movie with two genres will feature two rows with different genres. 

## Todo
* custom id column for manual ids
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
          input_folder="/home/til/my_movie_library/", 
          style=0, 
          m=True,
          c=True,
          output_folder="/home/til/tmms/")
```

Alternatively the script can be called from the command line:
```bash
python tmms.py 
    --api_key="MY_API_KEY" 
    --input_folder="/home/til/my_movie_library/", 
    --style=0
    --m
    --c
    --output_folder="/home/til/tmms/")
```

For every subfolder the TMDB API is queried. Incase of multiple results for querying with title and year, the most popular one is kept. If there no results, another query only including the title is sent.

## Result Specs
|attribute|m flag|c flag|output file|
|---|---|---|---|
|m.adult|x||tmms_moviedetails.csv|
|m.backdrop_path|x||tmms_moviedetails.csv|
|m.belongs_to_collection|x||tmms_moviedetails.csv|
|m.budget|x||tmms_moviedetails.csv|
|m.homepage|x||tmms_moviedetails.csv|
|m.id|x||tmms_moviedetails.csv|
|m.imdb_id|x||tmms_moviedetails.csv|
|m.original_language|x||tmms_moviedetails.csv|
|m.original_title|x||tmms_moviedetails.csv|
|m.overview|x||tmms_moviedetails.csv|
|m.popularity|x||tmms_moviedetails.csv|
|m.poster_path|x||tmms_moviedetails.csv|
|m.release_date|x||tmms_moviedetails.csv|
|m.revenue|x||tmms_moviedetails.csv|
|m.runtime|x||tmms_moviedetails.csv|
|m.status|x||tmms_moviedetails.csv|
|m.tagline|x||tmms_moviedetails.csv|
|m.title|x||tmms_moviedetails.csv|
|m.video|x||tmms_moviedetails.csv|
|m.vote_average|x||tmms_moviedetails.csv|
|m.vote_count|x||tmms_moviedetails.csv|
|genres.id|x||tmms_genres.csv|
|genres.name|x||tmms_genres.csv|
|genres.m.id|x||tmms_genres.csv|
|production_companies.id|x||tmms_production_companies.csv|
|production_companies.logo_path|x||tmms_production_companies.csv|
|production_companies.name|x||tmms_production_companies.csv|
|production_companies.origin_country|x||tmms_production_companies.csv|
|production_companies.m.id|x||tmms_production_companies.csv|
|production_countries.iso_3166_1|x||tmms_production_countries.csv|
|production_countries.name|x||tmms_production_countries.csv|
|production_countries.m.id|x||tmms_production_countries.csv|
|spoken_languages.english_name|x||tmms_spoken_languages.csv|
|spoken_languages.iso_639_1|x||tmms_spoken_languages.csv|
|spoken_languages.name|x||tmms_spoken_languages.csv|
|spoken_languages.m.id|x||tmms_spoken_languages.csv|
|cc.adult||x|tmms_credits.csv|
|cc.cast_id||x|tmms_credits.csv|
|cc.character||x|tmms_credits.csv|
|cc.credit.type **||x|tmms_credits.csv|
|cc.credit_id||x|tmms_credits.csv|
|cc.department||x|tmms_credits.csv|
|cc.gender||x|tmms_credits.csv|
|cc.id||x|tmms_credits.csv|
|cc.job||x|tmms_credits.csv|
|cc.known_for_department||x|tmms_credits.csv|
|cc.m_id *||x|tmms_credits.csv|
|cc.name||x|tmms_credits.csv|
|cc.order||x|tmms_credits.csv|
|cc.original_name||x|tmms_credits.csv|
|cc.popularity||x|tmms_credits.csv|
|cc.profile_path||x|tmms_credits.csv|

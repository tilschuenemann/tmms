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
**Movie Details**
```
m.adult
m.backdrop_path
m.belongs_to_collection
m.budget
m.homepage
m.id
m.imdb_id
m.original_language
m.original_title
m.overview
m.popularity
m.poster_path
m.release_date
m.revenue
m.runtime
m.status
m.tagline
m.title
m.video
m.vote_average
m.vote_count
```
In the APIs JSON response the following columns are arrays of nested objects - these get unlisted, multiplying each record depending on the arrays cardinality:
* spoken_languages
* production_companies
* production_countries
* genres

**Credits**
```
cc.adult
cc.cast_id
cc.character
cc.credit.type **
cc.credit_id
cc.department
cc.gender
cc.id
cc.job
cc.known_for_department
cc.m_id *
cc.name
cc.order
cc.original_name
cc.popularity
cc.profile_path
```
\* original name without prefix would be id, which conflicts with id for the respective cast / crew. 

** credit type is a new colum imposed by the script so that cast and crew can be differentiated while appending similar columns.

**Genres**
```
genres.id
genres.name
genres.m.id
```

**Production Companies**
```
production_companies.id
production_companies.logo_path
production_companies.name
production_companies.origin_country
production_companies.m.id
```

**production_countries**
```
production_countries.iso_3166_1
production_countries.name
production_countries.m.id
```

**production_countries**
```
spoken_languages.english_name
spoken_languages.iso_639_1
spoken_languages.name
spoken_languages.m.id
```
from setuptools import setup

setup(
    name="tmms",
    version="0.1",
    description="TMDB Movie Metadata Scraper",
    url="https://github.com/tilschuenemann/tmms",
    author="Til Schuenemann",
    author_email="",
    license="GNU-GPL3",
    packages=["tmms", "pandas", "numpy", "tqdm"],
    zip_safe=False,
)

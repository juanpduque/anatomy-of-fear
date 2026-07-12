# The Anatomy of Fear

**100 years of horror movie posters, one pixel at a time.**
A data-driven visual essay by [Pulp Analytics](https://medium.com/pulp-analytics), in the style of [The Pudding](https://pudding.cool).

We analyze the color of 32,000+ horror movie posters (1920–2025) to measure how the way we sell fear has changed: the Darkness Curve, the Rise of Red, and six visual eras of terror.

## Structure

```
pipeline/   Python pipeline: dataset -> posters -> color metrics -> JSON
site/       The scrollytelling page (self-contained HTML prototype)
docs/       Strategy & editorial plan (Spanish)
data/       Pipeline outputs (posters/ is gitignored)
```

## Run the pipeline

```bash
cd pipeline
pip3 install pandas numpy pillow scikit-learn matplotlib requests
python3 fear_pipeline.py                    # 1,000-poster validation sample
python3 fear_pipeline.py --all              # full dataset (~30k posters, ~1GB)
python3 fear_pipeline.py --refresh --api-key YOUR_TMDB_KEY   # add post-2022 films
```

Outputs land in `pipeline/data/`: `posters.csv` (per-poster metrics), `yearly.json` (feeds the site), `darkness_curve.png` (validation chart), and a Continue/Pivot verdict in the console.

## View the site

Open `site/index.html` in a browser. Current version runs on sample data; the real `yearly.json` replaces it after the pipeline runs.

## Data & credits

Film data and posters from [TMDB](https://www.themoviedb.org/) (this project uses the TMDB API but is not endorsed or certified by TMDB). Base dataset: [horror-movies](https://github.com/tashapiro/horror-movies) by Tanya Shapiro (TidyTuesday 2022-11-01). Palette method adapted from ["The Colour of Horror"](https://dl.acm.org/doi/10.1145/3565516.3565523) (ACM EVMP 2022). Industry context: [Stephen Follows' Horror Movie Report](https://stephenfollows.com/p/the-horror-movie-report).

#!/usr/bin/env python3
"""
THE ANATOMY OF FEAR — Step 1 pipeline
=====================================
Horror poster color analysis for the Pulp Analytics visual essay.

Pipeline:
  1. Load the horror-movies dataset (32,540 films, TMDB, via Tanya Shapiro /
     TidyTuesday 2022-11-01). Downloads automatically on first run.
  2. Stratified sample by decade (default 1,000 posters; use --all for full run).
  3. Download posters from TMDB image CDN (no API key needed for images).
  4. Per poster: dominant 5-color palette (k-means in CIELAB, saturation-weighted
     sampling, per "The Colour of Horror" ACM 2022), mean brightness (L*),
     mean saturation, share of near-black pixels, share of blood-red pixels.
  5. Aggregate by year -> data/yearly.json + data/posters.csv
  6. Quick validation chart -> data/darkness_curve.png
     (the Continue / Pivot checkpoint: does the Darkness Curve exist?)

Usage:
  pip install pandas numpy pillow scikit-learn matplotlib requests
  python fear_pipeline.py                 # 1,000-poster validation sample
  python fear_pipeline.py --n 200         # smaller/faster
  python fear_pipeline.py --all           # full dataset (~30k posters, ~1GB)

TMDB API key (optional, only to refresh the film list beyond 2022):
  python fear_pipeline.py --refresh --api-key YOUR_KEY
Attribution: this product uses the TMDB API but is not endorsed by TMDB.
"""
import argparse, io, json, math, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from PIL import Image
from sklearn.cluster import KMeans

# ----------------------------------------------------------------------------
DATASET_URLS = [
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2022/2022-11-01/horror_movies.csv",
    "https://raw.githubusercontent.com/tashapiro/horror-movies/main/data/horror_movies.csv",
]
IMG_BASE = "https://image.tmdb.org/t/p/w342"   # w342 is plenty for color work
OUT = Path("data"); POSTERS = OUT / "posters"
ANALYSIS_SIZE = (96, 144)                       # downsample before clustering
K = 5                                           # palette size
HEADERS = {"User-Agent": "PulpAnalytics-AnatomyOfFear/1.0"}

# ---------------------------- color math (numpy) -----------------------------
def srgb_to_lab(rgb):
    """rgb float array (...,3) in [0,1] -> CIELAB (D65). Vectorized."""
    r = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = r @ M.T
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16/116)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], axis=-1)

def rgb_to_hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    idx = m & (mx == r); h[idx] = (60 * ((g - b)[idx] / d[idx])) % 360
    idx = m & (mx == g); h[idx] = 60 * ((b - r)[idx] / d[idx]) + 120
    idx = m & (mx == b); h[idx] = 60 * ((r - g)[idx] / d[idx]) + 240
    s = np.where(mx > 1e-9, d / np.maximum(mx, 1e-9), 0)
    return h, s, mx

def lab_to_hex(lab):
    """Approximate LAB -> sRGB hex for palette output."""
    L, a, b = lab
    fy = (L + 16) / 116; fx = fy + a / 500; fz = fy - b / 200
    def finv(t): return np.where(t**3 > 0.008856, t**3, (t - 16/116) / 7.787)
    xyz = np.array([finv(fx) * 0.95047, finv(fy), finv(fz) * 1.08883])
    M = np.array([[ 3.2404542, -1.5371385, -0.4985314],
                  [-0.9692660,  1.8760108,  0.0415560],
                  [ 0.0556434, -0.2040259,  1.0572252]])
    rgb = M @ xyz
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1/2.4) - 0.055)
    rgb = np.clip(rgb, 0, 1)
    return "#{:02x}{:02x}{:02x}".format(*(rgb * 255).astype(int))

# ---------------------------- per-poster metrics ------------------------------
def analyze_poster(img_bytes, rng):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize(ANALYSIS_SIZE)
    rgb = np.asarray(img, dtype=np.float64) / 255.0
    px = rgb.reshape(-1, 3)
    lab = srgb_to_lab(px)
    h, s, v = rgb_to_hsv(px)

    brightness = float(lab[:, 0].mean())                       # mean L*, 0-100
    dark_share = float((lab[:, 0] < 20).mean())                # near-black px
    saturation = float(s.mean())
    red = ((h >= 345) | (h <= 15)) & (s > 0.4) & (v > 0.15)    # blood red
    red_share = float(red.mean())

    # saturation-weighted k-means palette (ACM "Colour of Horror" method)
    w = 0.25 + s                                # keep some weight on neutrals
    idx = rng.choice(len(px), size=min(4000, len(px)), p=w / w.sum())
    km = KMeans(n_clusters=K, n_init=4, random_state=0).fit(lab[idx])
    counts = np.bincount(km.labels_, minlength=K)
    order = np.argsort(-counts)
    palette = [lab_to_hex(km.cluster_centers_[i]) for i in order]
    pal_share = [round(float(counts[i]) / counts.sum(), 3) for i in order]

    return dict(brightness=round(brightness, 2), dark_share=round(dark_share, 4),
                saturation=round(saturation, 4), red_share=round(red_share, 4),
                palette=palette, palette_share=pal_share)

# ---------------------------- dataset ----------------------------------------
def load_dataset():
    OUT.mkdir(exist_ok=True)
    cache = OUT / "horror_movies.csv"
    if not cache.exists():
        for url in DATASET_URLS:
            try:
                print(f"Downloading dataset: {url}")
                r = requests.get(url, headers=HEADERS, timeout=60)
                r.raise_for_status()
                cache.write_bytes(r.content)
                break
            except Exception as e:
                print(f"  failed ({e}), trying next source...")
        else:
            sys.exit("Could not download dataset from any source.")
    df = pd.read_csv(cache)
    df = df.dropna(subset=["poster_path", "release_date"]).copy()
    df["year"] = pd.to_datetime(df["release_date"], errors="coerce").dt.year
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df = df[(df.year >= 1920) & (df.year <= 2026)]
    df["decade"] = (df.year // 10) * 10
    print(f"Dataset: {len(df):,} horror films with posters, {df.year.min()}–{df.year.max()}")
    return df

def stratified_sample(df, n):
    if n >= len(df):
        return df
    per = max(1, n // df.decade.nunique())
    out = (df.groupby("decade", group_keys=False)
             .apply(lambda g: g.sample(min(len(g), per), random_state=42)))
    return out

def refresh_from_api(api_key, pages=50):
    """Optional: pull recent horror films from TMDB discover API."""
    rows = []
    for page in range(1, pages + 1):
        r = requests.get("https://api.themoviedb.org/3/discover/movie",
                         params=dict(api_key=api_key, with_genres=27,
                                     sort_by="primary_release_date.desc", page=page),
                         headers=HEADERS, timeout=30)
        r.raise_for_status()
        for m in r.json().get("results", []):
            rows.append(dict(id=m["id"], title=m["title"],
                             release_date=m.get("release_date"),
                             poster_path=m.get("poster_path"),
                             vote_average=m.get("vote_average")))
        time.sleep(0.05)
    return pd.DataFrame(rows).dropna(subset=["poster_path", "release_date"])

# ---------------------------- download + run ---------------------------------
def fetch_poster(row):
    pid, path = row["id"], row["poster_path"]
    f = POSTERS / f"{pid}.jpg"
    if f.exists():
        return pid, f.read_bytes()
    try:
        r = requests.get(IMG_BASE + path, headers=HEADERS, timeout=30)
        if r.status_code == 200 and r.content:
            f.write_bytes(r.content)
            return pid, r.content
    except Exception:
        pass
    return pid, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000, help="sample size (stratified by decade)")
    ap.add_argument("--all", action="store_true", help="run the full dataset")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--refresh", action="store_true", help="also pull recent films from TMDB API")
    ap.add_argument("--api-key", default=os.environ.get("TMDB_API_KEY"))
    args = ap.parse_args()

    POSTERS.mkdir(parents=True, exist_ok=True)
    df = load_dataset()
    if args.refresh:
        if not args.api_key:
            sys.exit("--refresh requires --api-key or TMDB_API_KEY env var")
        extra = refresh_from_api(args.api_key)
        extra["year"] = pd.to_datetime(extra.release_date, errors="coerce").dt.year
        extra = extra.dropna(subset=["year"]); extra["year"] = extra.year.astype(int)
        extra["decade"] = (extra.year // 10) * 10
        df = pd.concat([df, extra]).drop_duplicates("id")
        print(f"After API refresh: {len(df):,} films")

    sample = df if args.all else stratified_sample(df, args.n)
    print(f"Analyzing {len(sample):,} posters...")

    rng = np.random.default_rng(42)
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_poster, row): row for _, row in sample.iterrows()}
        done = 0
        for fut in as_completed(futs):
            row = futs[fut]
            pid, content = fut.result()
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(sample)}")
            if content is None:
                continue
            try:
                m = analyze_poster(content, rng)
            except Exception:
                continue
            m.update(id=pid, title=row.get("title"), year=int(row["year"]))
            results.append(m)

    res = pd.DataFrame(results)
    if res.empty:
        sys.exit("No posters analyzed — check network access to image.tmdb.org")
    print(f"Analyzed {len(res):,} posters successfully "
          f"({len(res)/len(sample):.0%} success rate)")

    # ---- outputs ----
    res_flat = res.copy()
    res_flat["palette"] = res_flat.palette.apply(json.dumps)
    res_flat["palette_share"] = res_flat.palette_share.apply(json.dumps)
    res_flat.to_csv(OUT / "posters.csv", index=False)

    yearly = (res.groupby("year")
                 .agg(n=("id", "count"), brightness=("brightness", "mean"),
                      dark_share=("dark_share", "mean"),
                      saturation=("saturation", "mean"),
                      red_share=("red_share", "mean"))
                 .round(4).reset_index())
    yearly.to_json(OUT / "yearly.json", orient="records")

    # ---- Continue / Pivot checkpoint ----
    dec = res.copy(); dec["decade"] = (dec.year // 10) * 10
    d = dec.groupby("decade")[["brightness", "red_share", "dark_share"]].mean().round(2)
    print("\n=== DARKNESS CURVE CHECKPOINT (by decade) ===")
    print(d.to_string())
    pre70 = dec[dec.decade < 1970].brightness.mean()
    post70 = dec[(dec.decade >= 1970) & (dec.decade < 2010)].brightness.mean()
    verdict = "CONTINUE — the curve exists" if pre70 - post70 > 3 else \
              "PIVOT? — gap is weak, look at what the data IS saying"
    print(f"\nPre-1970 mean brightness: {pre70:.1f} | 1970-2009: {post70:.1f} -> {verdict}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(11, 5), facecolor="#0a0a0c")
        ax.set_facecolor("#0a0a0c")
        roll = yearly.set_index("year").brightness.rolling(5, min_periods=2).mean()
        ax.plot(roll.index, roll.values, color="#e5a00d", lw=2.5)
        ax.scatter(yearly.year, yearly.brightness, s=8, color="#e5a00d", alpha=.25)
        ax.set_title("The Darkness Curve — mean poster brightness (L*), 5yr rolling",
                     color="#e8e4da")
        ax.tick_params(colors="#9a958a")
        for sp in ax.spines.values(): sp.set_color("#2a2a30")
        fig.savefig(OUT / "darkness_curve.png", dpi=150, bbox_inches="tight")
        print(f"Chart saved: {OUT/'darkness_curve.png'}")
    except ImportError:
        print("matplotlib not installed — skipping chart")

    print(f"\nOutputs: {OUT/'posters.csv'}, {OUT/'yearly.json'}")

if __name__ == "__main__":
    main()

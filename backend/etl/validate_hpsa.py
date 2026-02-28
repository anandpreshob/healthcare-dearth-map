"""Validate Dearth Scores against HRSA HPSA designations.

Downloads HPSA data from data.hrsa.gov, joins against computed dearth_scores
in the database, and produces:
  - Point-biserial correlation (Dearth Score vs HPSA designation)
  - Spearman rank correlation (Dearth Score vs HPSA Score, designated only)
  - ROC/AUC analysis (HPSA designation as ground truth)
  - Chi-square contingency (Dearth Label vs HPSA status)
  - Visualizations (box plot, scatter, ROC, heatmap)

Usage:
    python -m backend.etl.validate_hpsa
    python -m backend.etl.validate_hpsa --skip-download   # reuse cached CSV
"""

import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")  # non-interactive backend

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg2
import requests
import seaborn as sns
from scipy import stats
from sklearn.metrics import roc_auc_score, roc_curve

from .config import get_db_params

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# HRSA direct download URLs (updated nightly)
HPSA_CSV_URL = "https://data.hrsa.gov/DataDownload/DD_Files/BCD_HPSA_FCT_DET_PC.csv"
HPSA_MH_CSV_URL = "https://data.hrsa.gov/DataDownload/DD_Files/BCD_HPSA_FCT_DET_MH.csv"

# Fallback: the combined dashboard CSV has all disciplines
HPSA_DASHBOARD_URL = "https://data.hrsa.gov/DataDownload/DD_Files/HPSA_DASHBOARD.csv"

# Where to cache downloaded files
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "hpsa_cache")

# Output directory for plots and summary
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "submissions", "amia-2026", "validation"
)

# Mapping: HPSA discipline → our specialty_code
DISCIPLINE_MAP = {
    "primary_care": "primary_care",
    "mental_health": "psychiatry",
}


# ---------------------------------------------------------------------------
# Step 1: Download HPSA data
# ---------------------------------------------------------------------------


def download_hpsa_data(skip_download: bool = False) -> pd.DataFrame:
    """Download and parse HPSA data from HRSA. Returns combined DataFrame."""
    os.makedirs(CACHE_DIR, exist_ok=True)

    dashboard_path = os.path.join(CACHE_DIR, "HPSA_DASHBOARD.csv")

    if skip_download and os.path.exists(dashboard_path):
        print(f"  Using cached file: {dashboard_path}")
    else:
        print(f"  Downloading HPSA dashboard data from HRSA...")
        # Use the dashboard CSV which contains all disciplines in one file
        resp = requests.get(HPSA_DASHBOARD_URL, timeout=120)
        resp.raise_for_status()
        with open(dashboard_path, "wb") as f:
            f.write(resp.content)
        print(f"  Saved {len(resp.content) / 1e6:.1f} MB to {dashboard_path}")

    print("  Parsing HPSA CSV...")
    df = pd.read_csv(dashboard_path, dtype=str, low_memory=False)
    print(f"  Raw HPSA records: {len(df):,}")

    # Print columns for debugging
    print(f"  Columns: {list(df.columns[:20])}...")

    return df


# ---------------------------------------------------------------------------
# Step 2: Parse and filter HPSA data to county-level flags
# ---------------------------------------------------------------------------


def build_county_name_lookup(conn) -> dict:
    """Build a (county_name_lower, state_abbr_lower) → fips lookup from the DB."""
    with conn.cursor() as cur:
        cur.execute("SELECT fips, name, state_abbr FROM counties")
        rows = cur.fetchall()
    lookup = {}
    for fips, name, state_abbr in rows:
        # Store both with and without " County" suffix for flexible matching
        key = (name.lower().strip(), state_abbr.lower().strip())
        lookup[key] = fips
        # Also store without " County" suffix
        name_lower = name.lower().strip()
        for suffix in [" county", " parish", " borough", " census area",
                       " municipality", " city and borough", " city"]:
            if name_lower.endswith(suffix):
                short = name_lower[: -len(suffix)]
                lookup[(short, state_abbr.lower().strip())] = fips
                break
    return lookup


def parse_hpsa_to_county_flags(
    hpsa_df: pd.DataFrame,
    county_fips_lookup: dict | None = None,
) -> pd.DataFrame:
    """Filter HPSA data and build county-level designation flags.

    Returns DataFrame with columns:
        fips, discipline, is_hpsa, hpsa_score
    """
    # Normalize column names (HRSA uses varied casing across file versions)
    hpsa_df.columns = [c.strip() for c in hpsa_df.columns]

    # Identify the key columns by searching for common patterns
    col_map = _identify_columns(hpsa_df)
    print(f"  Column mapping: {col_map}")

    # Filter: Geographic HPSAs only, Designated status
    df = hpsa_df.copy()

    # Filter by HPSA type (geographic area only, not facility/population-based)
    if col_map["hpsa_type"]:
        type_col = col_map["hpsa_type"]
        type_vals = df[type_col].str.strip().str.lower().unique()
        print(f"  HPSA types found: {type_vals}")
        # Keep geographic area designations
        geo_mask = df[type_col].str.strip().str.lower().str.contains(
            "geographic|geo area|single county|whole county|part of|county",
            na=False,
        )
        # Also keep "Single County" and "Whole County" types
        df = df[geo_mask]
        print(f"  After geographic filter: {len(df):,} records")

    # Filter by status (keep only designated/active)
    if col_map["status"]:
        status_col = col_map["status"]
        status_vals = df[status_col].str.strip().str.lower().unique()
        print(f"  HPSA statuses found: {status_vals}")
        active_mask = df[status_col].str.strip().str.lower().str.contains(
            "designated|active", na=False
        )
        df = df[active_mask]
        print(f"  After status filter: {len(df):,} records")

    # Filter by discipline
    if col_map["discipline"]:
        disc_col = col_map["discipline"]
        disc_vals = df[disc_col].str.strip().str.lower().unique()
        print(f"  Disciplines found: {disc_vals}")
        disc_mask = df[disc_col].str.strip().str.lower().str.contains(
            "primary care|mental health", na=False
        )
        df = df[disc_mask]
        print(f"  After discipline filter: {len(df):,} records")

    # Extract FIPS codes
    fips_col = col_map["fips"]
    if fips_col is None:
        # Try to construct FIPS from state + county FIPS columns
        fips_col = _construct_fips(df, col_map)

    # Detect county name column for name-based FIPS lookup
    county_name_col = None
    for c in df.columns:
        if "proper county" in c.lower():
            county_name_col = c
            break
    if county_name_col is None:
        # Fallback: try "County" + "State" columns
        for c in df.columns:
            if c.strip().lower() == "county":
                county_name_col = c
                break

    # Extract HPSA score
    score_col = col_map["score"]

    # Build county-level records
    records = []
    name_miss = 0
    for _, row in df.iterrows():
        fips = _extract_fips(row, fips_col, col_map)
        if fips is None and county_fips_lookup and county_name_col:
            fips = _fips_from_county_name(row, county_name_col, df.columns, county_fips_lookup)
        if fips is None:
            name_miss += 1
            continue

        # Determine discipline
        disc = "primary_care"
        if col_map["discipline"]:
            raw_disc = str(row[col_map["discipline"]]).strip().lower()
            if "mental" in raw_disc:
                disc = "mental_health"

        # Extract score
        score = 0.0
        if score_col and pd.notna(row.get(score_col)):
            try:
                score = float(row[score_col])
            except (ValueError, TypeError):
                score = 0.0

        records.append(
            {"fips": fips, "discipline": disc, "is_hpsa": True, "hpsa_score": score}
        )

    result = pd.DataFrame(records)
    if name_miss > 0:
        print(f"  Warning: {name_miss:,} records could not be matched to a FIPS code")
    print(f"  Parsed {len(result):,} county-discipline HPSA records")

    if result.empty:
        return result

    # Aggregate: for counties with multiple HPSAs, take max score
    result = (
        result.groupby(["fips", "discipline"])
        .agg({"is_hpsa": "any", "hpsa_score": "max"})
        .reset_index()
    )
    print(f"  After aggregation: {len(result):,} unique county-discipline pairs")

    for disc in ["primary_care", "mental_health"]:
        n = (result["discipline"] == disc).sum()
        print(f"    {disc}: {n:,} counties designated")

    return result


def _identify_columns(df: pd.DataFrame) -> dict:
    """Identify key columns by matching common patterns in HRSA data."""
    cols = {c.lower().strip(): c for c in df.columns}
    mapping = {
        "hpsa_type": None,
        "status": None,
        "discipline": None,
        "fips": None,
        "state_fips": None,
        "county_fips": None,
        "score": None,
    }

    for lower, orig in cols.items():
        # HPSA type (Geographic, Facility, Population)
        # Guard: prefer first match (e.g., "HPSA Type (Category)" over "HPSA Type Code")
        if mapping["hpsa_type"] is None and any(
            kw in lower
            for kw in [
                "hpsa type",
                "hpsa_type",
                "type_desc",
                "component_type",
                "hpsa_component_type",
            ]
        ):
            mapping["hpsa_type"] = orig
        # Status
        # Guard: prefer first match (e.g., "HPSA Status" over "HPSA Status Code")
        elif mapping["status"] is None and any(
            kw in lower
            for kw in [
                "hpsa_status",
                "hpsa status",
                "status_desc",
                "designation_status",
                "hpsa designation status",
            ]
        ):
            mapping["status"] = orig
        # Discipline
        elif mapping["discipline"] is None and any(
            kw in lower
            for kw in [
                "discipline",
                "hpsa_discipline",
                "discipline_type",
                "hpsa discipline type",
            ]
        ):
            mapping["discipline"] = orig
        # County FIPS (5-digit combined)
        elif mapping["fips"] is None and any(
            kw in lower
            for kw in [
                "county_fips",
                "cnty_fips",
                "fips_county",
                "common_county_fips",
                "county fips code",
            ]
        ):
            mapping["fips"] = orig
        # State FIPS (2-digit)
        elif mapping["state_fips"] is None and any(
            kw in lower
            for kw in [
                "state_fips",
                "common_state_fips",
                "state fips code",
                "statefipscode",
            ]
        ):
            mapping["state_fips"] = orig
        # County FIPS 3-digit (within state)
        elif mapping["county_fips"] is None and mapping["fips"] is None and any(
            kw in lower
            for kw in [
                "countyfipscode",
                "county_fips_code",
                "county fips code",
                "common_county_fips_code",
            ]
        ):
            mapping["county_fips"] = orig
        # HPSA Score
        elif mapping["score"] is None and any(
            kw in lower
            for kw in ["hpsa_score", "hpsa score", "score", "hpsa_shortage_score"]
        ):
            mapping["score"] = orig

    return mapping


def _construct_fips(df: pd.DataFrame, col_map: dict) -> str | None:
    """If no single FIPS column exists, try to construct from state+county."""
    if col_map["state_fips"] and col_map["county_fips"]:
        return "__constructed__"
    return None


def _extract_fips(row, fips_col, col_map) -> str | None:
    """Extract 5-digit FIPS code from a row."""
    if fips_col == "__constructed__":
        state = str(row.get(col_map["state_fips"], "")).strip()
        county = str(row.get(col_map["county_fips"], "")).strip()
        if not state or not county or state == "nan" or county == "nan":
            return None
        return state.zfill(2) + county.zfill(3)

    if fips_col and pd.notna(row.get(fips_col)):
        val = str(row[fips_col]).strip()
        if val and val != "nan":
            # Some FIPS codes have leading zeros stripped
            return val.zfill(5)
    return None


# US state name → abbreviation for fallback matching
_STATE_ABBR = {
    "alabama": "al", "alaska": "ak", "arizona": "az", "arkansas": "ar",
    "california": "ca", "colorado": "co", "connecticut": "ct", "delaware": "de",
    "florida": "fl", "georgia": "ga", "hawaii": "hi", "idaho": "id",
    "illinois": "il", "indiana": "in", "iowa": "ia", "kansas": "ks",
    "kentucky": "ky", "louisiana": "la", "maine": "me", "maryland": "md",
    "massachusetts": "ma", "michigan": "mi", "minnesota": "mn",
    "mississippi": "ms", "missouri": "mo", "montana": "mt", "nebraska": "ne",
    "nevada": "nv", "new hampshire": "nh", "new jersey": "nj",
    "new mexico": "nm", "new york": "ny", "north carolina": "nc",
    "north dakota": "nd", "ohio": "oh", "oklahoma": "ok", "oregon": "or",
    "pennsylvania": "pa", "rhode island": "ri", "south carolina": "sc",
    "south dakota": "sd", "tennessee": "tn", "texas": "tx", "utah": "ut",
    "vermont": "vt", "virginia": "va", "washington": "wa",
    "west virginia": "wv", "wisconsin": "wi", "wyoming": "wy",
    "district of columbia": "dc",
}


def _fips_from_county_name(row, county_name_col, all_columns, lookup: dict) -> str | None:
    """Resolve FIPS from a county name column using the DB lookup."""
    val = row.get(county_name_col)
    if pd.isna(val):
        return None
    val = str(val).strip()
    if not val or val == "nan":
        return None

    # "Proper County Name and State Abbreviation" format: "Clay County, AR"
    if "," in val:
        parts = val.rsplit(",", 1)
        county_part = parts[0].strip().lower()
        state_abbr = parts[1].strip().lower()
        # Try with full county name (e.g., "clay county")
        fips = lookup.get((county_part, state_abbr))
        if fips:
            return fips
        # Try stripping common suffixes
        for suffix in [" county", " parish", " borough", " census area",
                       " municipality", " city and borough", " city"]:
            if county_part.endswith(suffix):
                fips = lookup.get((county_part[: -len(suffix)], state_abbr))
                if fips:
                    return fips
                break
        return None

    # Fallback: "County" + "State" columns (state is full name like "Arkansas")
    state_col = None
    for c in all_columns:
        if c.strip().lower() == "state":
            state_col = c
            break
    if state_col:
        state_val = str(row.get(state_col, "")).strip().lower()
        state_abbr = _STATE_ABBR.get(state_val, state_val)
        county_lower = val.lower()
        fips = lookup.get((county_lower, state_abbr))
        if fips:
            return fips
        # Try with " county" suffix
        fips = lookup.get((county_lower + " county", state_abbr))
        if fips:
            return fips

    return None


# ---------------------------------------------------------------------------
# Step 3: Query dearth_scores from database
# ---------------------------------------------------------------------------


def query_dearth_scores(conn, specialty_codes: list[str]) -> pd.DataFrame:
    """Query dearth_scores for given specialties. Returns DataFrame."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                ds.geo_id AS fips,
                c.name AS county_name,
                c.state_abbr,
                c.population,
                ds.specialty_code,
                ds.provider_count,
                ds.provider_density,
                ds.nearest_distance_miles,
                ds.drive_time_minutes,
                ds.density_score,
                ds.drivetime_score,
                ds.dearth_score,
                ds.dearth_label
            FROM dearth_scores ds
            JOIN counties c ON ds.geo_id = c.fips
            WHERE ds.geo_type = 'county'
              AND ds.specialty_code = ANY(%s)
            ORDER BY ds.specialty_code, ds.geo_id
            """,
            (specialty_codes,),
        )
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=columns)
    print(f"  Queried {len(df):,} dearth_scores for specialties: {specialty_codes}")
    return df


# ---------------------------------------------------------------------------
# Step 4: Join and analyze
# ---------------------------------------------------------------------------


def run_validation(
    dearth_df: pd.DataFrame, hpsa_flags: pd.DataFrame, discipline: str
) -> dict:
    """Run validation analyses for a single discipline. Returns stats dict."""
    specialty = DISCIPLINE_MAP[discipline]
    ds = dearth_df[dearth_df["specialty_code"] == specialty].copy()

    hf = hpsa_flags[hpsa_flags["discipline"] == discipline].copy()

    # Merge
    merged = ds.merge(
        hf[["fips", "is_hpsa", "hpsa_score"]], on="fips", how="left"
    )
    merged["is_hpsa"] = merged["is_hpsa"].fillna(False).astype(bool)
    merged["hpsa_score"] = merged["hpsa_score"].fillna(0.0)

    n_total = len(merged)
    n_hpsa = merged["is_hpsa"].sum()
    n_non = n_total - n_hpsa
    print(f"\n  --- {discipline.upper()} ({specialty}) ---")
    print(f"  Total counties: {n_total}, HPSA: {n_hpsa}, Non-HPSA: {n_non}")

    if n_hpsa == 0 or n_non == 0:
        print("  WARNING: Cannot run validation — one group is empty!")
        return {"discipline": discipline, "error": "insufficient data"}

    result = {"discipline": discipline, "n_total": n_total, "n_hpsa": int(n_hpsa)}

    # 4a. Point-biserial correlation
    r_pb, p_pb = stats.pointbiserialr(
        merged["is_hpsa"].astype(int), merged["dearth_score"]
    )
    result["pointbiserial_r"] = r_pb
    result["pointbiserial_p"] = p_pb
    print(f"  Point-biserial r = {r_pb:.4f} (p = {p_pb:.2e})")

    # 4b. Mann-Whitney U test (non-parametric comparison of distributions)
    hpsa_scores = merged.loc[merged["is_hpsa"], "dearth_score"]
    non_scores = merged.loc[~merged["is_hpsa"], "dearth_score"]
    u_stat, u_p = stats.mannwhitneyu(hpsa_scores, non_scores, alternative="greater")
    result["mannwhitney_U"] = u_stat
    result["mannwhitney_p"] = u_p
    result["mean_dearth_hpsa"] = hpsa_scores.mean()
    result["mean_dearth_non"] = non_scores.mean()
    print(
        f"  Mean Dearth Score: HPSA={hpsa_scores.mean():.1f} vs Non-HPSA={non_scores.mean():.1f}"
    )
    print(f"  Mann-Whitney U = {u_stat:.0f} (p = {u_p:.2e})")

    # 4c. Spearman correlation (designated counties only)
    designated = merged[merged["is_hpsa"] & (merged["hpsa_score"] > 0)]
    if len(designated) >= 10:
        rho, rho_p = stats.spearmanr(
            designated["dearth_score"], designated["hpsa_score"]
        )
        result["spearman_rho"] = rho
        result["spearman_p"] = rho_p
        print(
            f"  Spearman rho (designated only, n={len(designated)}): {rho:.4f} (p = {rho_p:.2e})"
        )
    else:
        result["spearman_rho"] = None
        print(f"  Spearman: too few designated counties with scores ({len(designated)})")

    # 4d. ROC/AUC
    y_true = merged["is_hpsa"].astype(int)
    y_score = merged["dearth_score"]
    auc = roc_auc_score(y_true, y_score)
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    result["auc"] = auc
    result["roc_fpr"] = fpr
    result["roc_tpr"] = tpr
    print(f"  ROC AUC = {auc:.4f}")

    # 4e. Chi-square contingency (Dearth Label vs HPSA status)
    ct = pd.crosstab(merged["dearth_label"], merged["is_hpsa"])
    chi2, chi_p, dof, expected = stats.chi2_contingency(ct)
    result["chi2"] = chi2
    result["chi2_p"] = chi_p
    result["crosstab"] = ct
    print(f"  Chi-square = {chi2:.1f} (p = {chi_p:.2e}, dof = {dof})")

    # Store merged data for plotting
    result["merged"] = merged
    result["designated"] = designated

    return result


# ---------------------------------------------------------------------------
# Step 5: Generate visualizations
# ---------------------------------------------------------------------------


def generate_plots(results: list[dict], output_dir: str):
    """Generate validation plots for each discipline."""
    os.makedirs(output_dir, exist_ok=True)
    sns.set_style("whitegrid")

    for res in results:
        if "error" in res:
            continue
        disc = res["discipline"]
        merged = res["merged"]
        designated = res["designated"]

        # 5a. Box plot: Dearth Score by HPSA status
        fig, ax = plt.subplots(figsize=(8, 5))
        merged["HPSA Status"] = merged["is_hpsa"].map(
            {True: "HPSA Designated", False: "Non-HPSA"}
        )
        sns.boxplot(
            data=merged,
            x="HPSA Status",
            y="dearth_score",
            palette=["#2ecc71", "#e74c3c"],
            ax=ax,
        )
        ax.set_title(
            f"Dearth Score by HPSA Designation — {disc.replace('_', ' ').title()}"
        )
        ax.set_ylabel("Dearth Score (0–100)")
        ax.annotate(
            f"HPSA mean: {res['mean_dearth_hpsa']:.1f}\n"
            f"Non-HPSA mean: {res['mean_dearth_non']:.1f}\n"
            f"Point-biserial r = {res['pointbiserial_r']:.3f}\n"
            f"p = {res['pointbiserial_p']:.2e}",
            xy=(0.02, 0.98),
            xycoords="axes fraction",
            va="top",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
        )
        fig.tight_layout()
        fig.savefig(
            os.path.join(output_dir, f"boxplot_{disc}.png"), dpi=150, bbox_inches="tight"
        )
        plt.close(fig)
        print(f"  Saved boxplot_{disc}.png")

        # 5b. Scatter: Dearth Score vs HPSA Score (designated only)
        if len(designated) >= 10:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.scatter(
                designated["hpsa_score"],
                designated["dearth_score"],
                alpha=0.4,
                s=20,
                color="#3498db",
            )
            # Fit line
            z = np.polyfit(designated["hpsa_score"], designated["dearth_score"], 1)
            p = np.poly1d(z)
            x_line = np.linspace(
                designated["hpsa_score"].min(), designated["hpsa_score"].max(), 100
            )
            ax.plot(x_line, p(x_line), "r--", linewidth=2)
            ax.set_xlabel("HPSA Score")
            ax.set_ylabel("Dearth Score")
            ax.set_title(
                f"Dearth Score vs HPSA Score — {disc.replace('_', ' ').title()} (Designated Counties)"
            )
            rho = res.get("spearman_rho")
            if rho is not None:
                ax.annotate(
                    f"Spearman ρ = {rho:.3f}\nn = {len(designated)}",
                    xy=(0.02, 0.98),
                    xycoords="axes fraction",
                    va="top",
                    fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                )
            fig.tight_layout()
            fig.savefig(
                os.path.join(output_dir, f"scatter_{disc}.png"),
                dpi=150,
                bbox_inches="tight",
            )
            plt.close(fig)
            print(f"  Saved scatter_{disc}.png")

        # 5c. ROC curve
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.plot(
            res["roc_fpr"], res["roc_tpr"], color="#e67e22", linewidth=2,
            label=f"AUC = {res['auc']:.3f}",
        )
        ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="Random (AUC = 0.5)")
        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_title(
            f"ROC Curve — {disc.replace('_', ' ').title()}\n"
            f"(Dearth Score predicting HPSA designation)"
        )
        ax.legend(loc="lower right", fontsize=11)
        fig.tight_layout()
        fig.savefig(
            os.path.join(output_dir, f"roc_{disc}.png"), dpi=150, bbox_inches="tight"
        )
        plt.close(fig)
        print(f"  Saved roc_{disc}.png")

        # 5d. Heatmap: Dearth Label vs HPSA status
        ct = res["crosstab"]
        # Compute proportions per Dearth Label row
        ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100
        fig, ax = plt.subplots(figsize=(6, 5))
        sns.heatmap(
            ct_pct,
            annot=True,
            fmt=".1f",
            cmap="RdYlGn_r",
            ax=ax,
            cbar_kws={"label": "% of counties"},
        )
        ax.set_title(
            f"HPSA Rate (%) by Dearth Label — {disc.replace('_', ' ').title()}"
        )
        ax.set_xlabel("HPSA Designated")
        ax.set_ylabel("Dearth Label")
        fig.tight_layout()
        fig.savefig(
            os.path.join(output_dir, f"heatmap_{disc}.png"), dpi=150, bbox_inches="tight"
        )
        plt.close(fig)
        print(f"  Saved heatmap_{disc}.png")


# ---------------------------------------------------------------------------
# Step 6: Summary report
# ---------------------------------------------------------------------------


def print_summary(results: list[dict], output_dir: str):
    """Print a summary report and save to text file."""
    lines = []
    lines.append("=" * 70)
    lines.append("HPSA VALIDATION SUMMARY")
    lines.append("=" * 70)

    for res in results:
        if "error" in res:
            lines.append(f"\n{res['discipline'].upper()}: {res['error']}")
            continue

        disc = res["discipline"]
        lines.append(f"\n--- {disc.replace('_', ' ').upper()} ---")
        lines.append(f"Counties: {res['n_total']} total, {res['n_hpsa']} HPSA-designated")
        lines.append(
            f"Mean Dearth Score: HPSA = {res['mean_dearth_hpsa']:.1f}, "
            f"Non-HPSA = {res['mean_dearth_non']:.1f}"
        )
        lines.append(
            f"Point-biserial r = {res['pointbiserial_r']:.4f} "
            f"(p = {res['pointbiserial_p']:.2e})"
        )
        lines.append(
            f"Mann-Whitney U = {res['mannwhitney_U']:.0f} "
            f"(p = {res['mannwhitney_p']:.2e})"
        )
        if res.get("spearman_rho") is not None:
            lines.append(
                f"Spearman rho = {res['spearman_rho']:.4f} "
                f"(p = {res.get('spearman_p', 'N/A')})"
            )
        lines.append(f"ROC AUC = {res['auc']:.4f}")
        lines.append(
            f"Chi-square = {res['chi2']:.1f} "
            f"(p = {res['chi2_p']:.2e})"
        )

    lines.append("\n" + "=" * 70)
    lines.append("INTERPRETATION")
    lines.append("=" * 70)
    lines.append(
        "AUC > 0.7 = acceptable discrimination; > 0.8 = excellent."
    )
    lines.append(
        "Point-biserial r > 0.3 with p < 0.01 indicates meaningful correlation."
    )
    lines.append(
        "Spearman rho > 0.3 indicates ordinal agreement between scoring systems."
    )
    lines.append(
        "Significant chi-square (p < 0.05) shows Dearth Labels are not "
        "independent of HPSA status."
    )

    report = "\n".join(lines)
    print(report)

    # Save to file
    report_path = os.path.join(output_dir, "validation_summary.txt")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved to {report_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Validate Dearth Scores vs HPSA")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading HPSA data (use cached CSV)",
    )
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=== HPSA Validation Pipeline ===\n")

    # Connect to DB early (needed for county name → FIPS lookup)
    db_params = get_db_params()
    conn = psycopg2.connect(**db_params)

    # Step 1: Download HPSA data
    print("Step 1: Download HPSA data")
    hpsa_raw = download_hpsa_data(skip_download=args.skip_download)

    # Step 2: Parse to county-level flags
    print("\nStep 2: Parse HPSA county flags")
    county_fips_lookup = build_county_name_lookup(conn)
    print(f"  Built county name lookup: {len(county_fips_lookup):,} entries")
    hpsa_flags = parse_hpsa_to_county_flags(hpsa_raw, county_fips_lookup)

    if hpsa_flags.empty:
        conn.close()
        print("\nERROR: No HPSA county-discipline records parsed.")
        print("This may indicate a change in the HRSA CSV format.")
        print(f"Please inspect the cached CSV in {CACHE_DIR}")
        sys.exit(1)

    # Step 3: Query dearth_scores from database
    print("\nStep 3: Query dearth_scores from database")
    try:
        specialty_codes = list(DISCIPLINE_MAP.values())
        dearth_df = query_dearth_scores(conn, specialty_codes)
    finally:
        conn.close()

    if dearth_df.empty:
        print("\nERROR: No dearth_scores found in database.")
        print("Run the ETL pipeline first: python -m backend.etl.run_pipeline")
        sys.exit(1)

    # Step 4: Run validation analyses
    print("\nStep 4: Statistical validation")
    results = []
    for discipline in DISCIPLINE_MAP:
        res = run_validation(dearth_df, hpsa_flags, discipline)
        results.append(res)

    # Step 5: Generate visualizations
    print(f"\nStep 5: Generate plots → {OUTPUT_DIR}")
    generate_plots(results, OUTPUT_DIR)

    # Step 6: Summary report
    print("\nStep 6: Summary report")
    print_summary(results, OUTPUT_DIR)

    print("\n=== Validation Complete ===")
    print(f"All outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

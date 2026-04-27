import glob
import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "src", "data")

WELL_FILES_PATTERN = os.path.join(DATA_DIR, "[0-9]*.csv")
PRODUCTION_FILE = os.path.join(DATA_DIR, "well-production.csv")

DATE_COLS = [
    "Status Date",
    "Permit Application Date",
    "Permit Issued Date",
    "Spud/Start Drilling Date",
    "Total Depth Date",
    "Well Completion Date",
    "Plugging & Abandonment Date",
    "Last Modified Date",
]

NUMERIC_COLS = [
    "Proposed Total Depth",
    "Surface Longitude",
    "Surface Latitude",
    "Bottom Hole Longitude",
    "Bottom Hole Latitude",
    "True Vertical Depth",
    "Bottom Hole Total Measured Depth",
    "Kickoff Depth",
    "Drilled Depth",
]

PRODUCTION_NUMERIC = ["OIL (Bbls)", "GAS (Mcf)", "WATER (Bbls)", "Months in Production"]


def _strip_df(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip()
    obj_cols = df.select_dtypes(include="object").columns
    df[obj_cols] = df[obj_cols].apply(lambda s: s.str.strip())
    return df


def load_production_raw() -> pd.DataFrame:
    prod = pd.read_csv(PRODUCTION_FILE, dtype=str, low_memory=False)
    prod = _strip_df(prod)
    prod = prod.drop(columns=[c for c in prod.columns if c == ""], errors="ignore")
    for col in PRODUCTION_NUMERIC:
        if col in prod.columns:
            prod[col] = pd.to_numeric(prod[col], errors="coerce")
    prod["Year"] = pd.to_numeric(prod["Year"], errors="coerce")
    return prod


def load_production() -> pd.DataFrame:
    prod = pd.read_csv(PRODUCTION_FILE, dtype=str, low_memory=False)
    prod = _strip_df(prod)
    prod = prod.drop(columns=[c for c in prod.columns if c == ""], errors="ignore")

    for col in PRODUCTION_NUMERIC:
        if col in prod.columns:
            prod[col] = pd.to_numeric(prod[col], errors="coerce")

    prod["Year"] = pd.to_numeric(prod["Year"], errors="coerce")

    agg = prod.groupby("API Well Number", as_index=False).agg(
        Total_Oil_Bbls=("OIL (Bbls)", "sum"),
        Total_Gas_Mcf=("GAS (Mcf)", "sum"),
        Total_Water_Bbls=("WATER (Bbls)", "sum"),
        Production_Years=("Year", "nunique"),
        Latest_Production_Year=("Year", "max"),
    )
    return agg


def load_data() -> pd.DataFrame:
    files = sorted(glob.glob(WELL_FILES_PATTERN))
    frames = [pd.read_csv(f, dtype=str, low_memory=False, on_bad_lines="skip") for f in files]
    df = pd.concat(frames, ignore_index=True)

    df = _strip_df(df)

    # drop any duplicate columns introduced by malformed rows
    df = df.loc[:, ~df.columns.duplicated()]

    df.drop_duplicates(subset=["API Well Number"], keep="last", inplace=True)
    df.reset_index(drop=True, inplace=True)

    for col in DATE_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Spud Year"] = df["Spud/Start Drilling Date"].dt.year

    df = df[
        (df["Surface Longitude"].between(-80, -72))
        & (df["Surface Latitude"].between(40, 46))
        | df["Surface Longitude"].isna()
    ]

    prod = load_production()
    df = df.merge(prod, on="API Well Number", how="left")

    prod_cols = ["Total_Oil_Bbls", "Total_Gas_Mcf", "Total_Water_Bbls",
                 "Production_Years", "Latest_Production_Year"]
    df[prod_cols] = df[prod_cols].fillna(0)

    return df

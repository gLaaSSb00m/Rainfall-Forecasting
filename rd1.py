import requests
import pandas as pd
import time
from pathlib import Path

# ============================================================
# NASA POWER API CONFIG
# ============================================================

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

START_YEAR = 1981
END_YEAR = 2025
CHUNK_SIZE_YEARS = 10

# ============================================================
# DIVISION COORDINATES
# ============================================================

DIVISION_COORDINATES = {
    "Rangpur": (25.7439, 89.2752),
    "Rajshahi": (24.3743, 88.6042),
    "Dhaka": (23.8103, 90.4125),
    "Mymensingh": (24.7471, 90.4203),
    "Sylhet": (24.8949, 91.8687),
    "Khulna": (22.8456, 89.5403),
    "Barishal": (22.7010, 90.3535),
    "Chattogram": (22.3569, 91.7832),
}

OUTPUT_DIR = Path("climate_data")

# ============================================================
# NASA PARAMETERS
# ============================================================

PARAMETERS = [
    "T2M_MAX",            # Maximum Temperature
    "T2M_MIN",            # Minimum Temperature
    "PRECTOT",            # Rainfall
    "RH2M",               # Relative Humidity
    "PS",                 # Surface Pressure
    "WS2M",               # Wind Speed
    "T2MDEW",             # Dew Point Temperature
    "ALLSKY_SFC_SW_DWN",  # Solar Radiation
]

PARAMETER_STRING = ",".join(PARAMETERS)

# ============================================================
# FETCH DATA
# ============================================================

def fetch_location_weather(latitude: float, longitude: float) -> pd.DataFrame:

    all_frames = []

    for year in range(START_YEAR, END_YEAR + 1, CHUNK_SIZE_YEARS):

        chunk_start = f"{year}0101"
        chunk_end_year = min(year + CHUNK_SIZE_YEARS - 1, END_YEAR)
        chunk_end = f"{chunk_end_year}1231"

        print(
            f"Fetching {latitude},{longitude} "
            f"from {chunk_start} to {chunk_end}"
        )

        params = {
            "community": "ag",
            "parameters": PARAMETER_STRING,
            "latitude": latitude,
            "longitude": longitude,
            "start": chunk_start,
            "end": chunk_end,
            "format": "JSON",
        }

        response = requests.get(URL, params=params)

        if response.status_code != 200:
            raise RuntimeError(
                f"NASA API Error ({response.status_code})\n"
                f"{response.text}"
            )

        data = response.json()

        parameter_data = data["properties"]["parameter"]

        df_chunk = pd.DataFrame(parameter_data)

        all_frames.append(df_chunk)

        time.sleep(1)

    df = pd.concat(all_frames)

    df.index.name = "Date"

    df = df.reset_index()

    # --------------------------------------------------------
    # Rename Columns
    # --------------------------------------------------------

    rename_map = {
        "T2M_MAX": "Tmax_C",
        "T2M_MIN": "Tmin_C",
        "PRECTOT": "Rainfall_mm",
        "RH2M": "Humidity_pct",
        "PS": "Pressure_kPa",
        "WS2M": "WindSpeed_mps",
        "T2MDEW": "DewPoint_C",
        "ALLSKY_SFC_SW_DWN": "SolarRadiation_Wm2",
    }

    df = df.rename(columns=rename_map)

    # NASA missing values
    df = df.replace(-999, pd.NA)

    return df


# ============================================================
# SAVE INDIVIDUAL DIVISION FILE
# ============================================================

def save_division_data(
    division_name: str,
    df: pd.DataFrame,
    output_dir: Path
) -> Path:

    filename = (
        f"{division_name.lower().replace(' ', '_')}"
        f"_climate_final.csv"
    )

    filepath = output_dir / filename

    df.to_csv(filepath, index=False)

    print(f"Saved: {filepath}")

    return filepath


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    combined_frames = []

    for division, (lat, lon) in DIVISION_COORDINATES.items():

        print("\n" + "=" * 60)
        print(f"Processing {division}")
        print("=" * 60)

        df = fetch_location_weather(lat, lon)

        df["Division"] = division

        save_division_data(
            division_name=division,
            df=df,
            output_dir=OUTPUT_DIR,
        )

        combined_frames.append(df)

    # ========================================================
    # COMBINED DATASET
    # ========================================================

    combined_df = pd.concat(
        combined_frames,
        ignore_index=True
    )

    combined_file = OUTPUT_DIR / "all_divisions_climate_final.csv"

    combined_df.to_csv(combined_file, index=False)

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)

    print(f"Combined Dataset: {combined_file}")
    print(f"Total Records: {len(combined_df):,}")

    print("\nColumns:")
    print(combined_df.columns.tolist())


if __name__ == "__main__":
    main()
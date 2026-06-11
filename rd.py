import requests
import pandas as pd
import time
from pathlib import Path

url = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Adjusted to 1981 based on NASA's database constraints
start_year = 1981
end_year = 2025
chunk_size_years = 10

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

OUTPUT_DIR = Path(".")


def fetch_location_weather(latitude: float, longitude: float) -> pd.DataFrame:
    all_frames = []

    for year in range(start_year, end_year + 1, chunk_size_years):
        chunk_start = f"{year}0101"
        chunk_end_year = min(year + chunk_size_years - 1, end_year)
        chunk_end = f"{chunk_end_year}1231"

        print(f"Fetching data from {chunk_start} to {chunk_end} for {latitude},{longitude}...")

        params = {
            "community": "ag",
            "parameters": "T2M_MAX,T2M_MIN,PRECTOT",
            "latitude": latitude,
            "longitude": longitude,
            "start": chunk_start,
            "end": chunk_end,
            "format": "JSON",
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            raise RuntimeError(
                f"NASA API error for {latitude},{longitude}: {response.status_code}\n{response.text}"
            )

        data = response.json()
        features = data["properties"]["parameter"]
        df_chunk = pd.DataFrame(features)
        all_frames.append(df_chunk)

        time.sleep(1)

    df = pd.concat(all_frames)
    df.index.name = "Date"
    df = df.reset_index()
    df.columns = ["Date", "Tmax_C", "Tmin_C", "Rainfall_mm"]
    df = df.replace(-999, pd.NA)
    return df


def save_division_data(name: str, df: pd.DataFrame, output_dir: Path) -> Path:
    file_name = f"{name.lower().replace(' ', '_')}_climate_final.csv"
    file_path = output_dir / file_name
    df.to_csv(file_path, index=False)
    print(f"Saved {name} climate data to {file_path}")
    return file_path


def main() -> None:
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    combined_frames = []

    for division, (lat, lon) in DIVISION_COORDINATES.items():
        print(f"\n=== Processing {division} ===")
        df_division = fetch_location_weather(lat, lon)
        df_division["Division"] = division
        save_division_data(division, df_division, output_dir)
        combined_frames.append(df_division)

    combined_df = pd.concat(combined_frames, ignore_index=True)
    combined_file = output_dir / "all_divisions_climate_final.csv"
    combined_df.to_csv(combined_file, index=False)
    print(f"\n🎉 Combined data saved to {combined_file}")
    print(f"Total records fetched: {len(combined_df)}")


if __name__ == "__main__":
    main()
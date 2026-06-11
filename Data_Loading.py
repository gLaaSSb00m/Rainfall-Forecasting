import pandas as pd
from pathlib import Path

output_files = []
combined_file = Path("all_divisions_climate_final.csv")
if combined_file.exists():
    output_files.append(combined_file)
else:
    for division in [
        "rangpur",
        "rajshahi",
        "dhaka",
        "mymensingh",
        "sylhet",
        "khulna",
        "barishal",
        "chattogram",
    ]:
        file_path = Path(f"{division}_climate_final.csv")
        if file_path.exists():
            output_files.append(file_path)

if not output_files:
    raise FileNotFoundError(
        "No climate CSV files found. Run rd.py first to generate the division datasets."
    )

print(f"Loading {len(output_files)} file(s): {output_files}")
df = pd.concat([pd.read_csv(path) for path in output_files], ignore_index=True)
print(df.info())
print(df.head())

#!/usr/bin/env python3
"""
ICON-EU downloader from DWD Open Data
Resolution: ~6.5 km (0.0625deg) over Europe
Coverage: today 00z run -> steps 0-120 (~5 days ahead)
          to get past day coverage use --run yesterday
Output: forecast_data.grib2 (directly openable in XyGrib, no conversion needed)

DWD step schedule: hourly 0-78, then 3-hourly 81,84,...,120 (93 steps total)
"""

import os
import sys
import datetime
import requests
import bz2
import subprocess
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://opendata.dwd.de/weather/nwp/icon-eu/grib"

# Correct DWD ICON-EU step schedule (verified from opendata.dwd.de)
STEPS_HOURLY = list(range(0, 79))          # 0, 1, ..., 78
STEPS_3H     = list(range(81, 121, 3))     # 81, 84, ..., 120
ALL_STEPS    = STEPS_HOURLY + STEPS_3H     # 93 steps total

# (DWD var name, dir name, description)
VARIABLES = [
    ("U_10M",     "u_10m",     "Wind U 10m"),
    ("V_10M",     "v_10m",     "Wind V 10m"),
    ("VMAX_10M",  "vmax_10m",  "Wind Gust"),
    ("T_2M",      "t_2m",      "Temperature 2m"),
    ("TOT_PREC",  "tot_prec",  "Total Precipitation"),
    ("CLCT",      "clct",      "Total Cloud Cover"),
    ("RELHUM_2M", "relhum_2m", "Relative Humidity 2m"),
    ("H_SNOW",    "h_snow",    "Snow Depth"),
    ("PMSL",      "pmsl",      "Mean Sea Level Pressure"),
    ("CAPE_CON",  "cape_con",  "CAPE"),
]


def get_run_info(use_yesterday=False):
    dt = datetime.datetime.utcnow()
    if use_yesterday:
        dt -= datetime.timedelta(days=1)
    return dt.strftime("%Y%m%d"), "00"


def build_url(run_date, run_hour, step, var_name, var_dir):
    fname = (
        f"icon-eu_europe_regular-lat-lon_single-level"
        f"_{run_date}{run_hour}_{step:03d}_{var_name}.grib2.bz2"
    )
    return f"{BASE_URL}/{run_hour}/{var_dir}/{fname}", fname


def download_variable(session, run_date, run_hour, var_name, var_dir, parts_dir):
    downloaded = []
    skipped = 0

    for step in ALL_STEPS:
        url, bz2_name = build_url(run_date, run_hour, step, var_name, var_dir)
        dest = os.path.join(parts_dir, bz2_name.replace(".bz2", ""))

        if os.path.exists(dest):
            downloaded.append(dest)
            continue

        try:
            r = session.get(url, verify=False, timeout=60)
            r.raise_for_status()
            raw = bz2.decompress(r.content)
            with open(dest, "wb") as f:
                f.write(raw)
            downloaded.append(dest)
            print(f"  step {step:03d}/{ALL_STEPS[-1]:03d}", end="\r")
        except Exception:
            skipped += 1

    return downloaded, skipped


def main():
    use_yesterday = "--yesterday" in sys.argv
    parts_dir = "icon_eu_parts"
    output = "forecast_data.grib2"
    os.makedirs(parts_dir, exist_ok=True)

    run_date, run_hour = get_run_info(use_yesterday)
    run_dt = datetime.datetime.strptime(run_date + run_hour, "%Y%m%d%H")
    valid_end = run_dt + datetime.timedelta(hours=ALL_STEPS[-1])

    print(f"ICON-EU run : {run_date} {run_hour}z")
    print(f"Coverage    : {run_dt:%Y-%m-%d %Hz} -> {valid_end:%Y-%m-%d %Hz}")
    print(f"Steps       : 0-78 (1h) + 81-120 (3h) = {len(ALL_STEPS)} steps/variable")
    print(f"Variables   : {len(VARIABLES)}")
    print(f"Total files : ~{len(ALL_STEPS) * len(VARIABLES)}")
    print()

    session = requests.Session()
    all_files = []
    total_skipped = 0

    for var_name, var_dir, desc in VARIABLES:
        print(f"[{var_name}] {desc} ...", flush=True)
        files, skipped = download_variable(
            session, run_date, run_hour, var_name, var_dir, parts_dir
        )
        total_skipped += skipped
        all_files.extend(files)
        status = f"{len(files)}/{len(ALL_STEPS)} steps"
        if skipped:
            status += f" ({skipped} skipped)"
        print(f"  {status}          ")

    if total_skipped:
        print(f"\nNote: {total_skipped} steps skipped (run not yet published?)")
        print("Tip: use --yesterday flag if today's 00z run isn't available yet")

    print(f"\nMerging {len(all_files)} GRIB2 files -> {output} ...")
    # Sort: group by variable then by step for consistent time ordering in XyGrib
    all_files_sorted = sorted(all_files)
    with open(output, "wb") as out:
        for f in all_files_sorted:
            with open(f, "rb") as inp:
                out.write(inp.read())

    size_mb = os.path.getsize(output) / (1024 * 1024)
    print(f"Merged: {output}  ({size_mb:.1f} MB)")

    # Convert for XyGrib: regrid to 0.125deg then repack to c3
    # Two steps because wgrib2 can't combine -new_grid and -set_grib_type in one pass
    xygrib_output = "forecast_data_xygrib.grib2"
    temp_grid = "_regrid_temp.grib2"
    print(f"\nConverting for XyGrib -> {xygrib_output}")
    print("  Step 1/2: regrid to 0.125deg over Europe [-15:45, 35:70] ...")
    try:
        r1 = subprocess.run(
            [
                "wgrib2", output,
                "-new_grid_winds", "earth",
                "-new_grid", "latlon", "-15:481:0.125", "35:281:0.125",
                temp_grid,
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if not os.path.exists(temp_grid):
            raise RuntimeError(r1.stderr.decode(errors="replace")[:300])

        print("  Step 2/2: repack to c3 (complex packing + spatial diff) ...")
        r2 = subprocess.run(
            ["wgrib2", temp_grid, "-set_grib_type", "c3", "-grib_out", xygrib_output],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if os.path.exists(temp_grid):
            os.remove(temp_grid)

        if os.path.exists(xygrib_output):
            xsize_mb = os.path.getsize(xygrib_output) / (1024 * 1024)
            print(f"Done: {xygrib_output}  ({xsize_mb:.1f} MB)")
            print(f"\nOpen {xygrib_output} in XyGrib.")
        else:
            raise RuntimeError(r2.stderr.decode(errors="replace")[:300])
    except FileNotFoundError:
        print("wgrib2 not in PATH — run grb2_to_grib2.bat manually")
    except RuntimeError as e:
        print(f"Conversion failed: {e}")
        print("Run grb2_to_grib2.bat manually")


if __name__ == "__main__":
    main()

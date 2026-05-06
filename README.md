# ICON-EU-Gribs
ICON EU Gribs downloader to import to XyGrib

![img](https://raw.githubusercontent.com/dayeggpi/ICON-EU-Gribs/refs/heads/main/XyGrib_UNCjI8q39W.png)

# What ?

This script will download grib2 files from ICON EU from DWD Open Data, for : 
```
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
```

Resolution: ~15 km (0.125deg) over Europe.

Coverage: today 00z run -> steps 0-120 (~5 days ahead) (1h step for first 3 days, then every 3hours).

To get past day coverage use --run yesterday



# How-to

1. Run `python icon_eu_downloader.py` (it will download a bunch of files, then combine into a single .grib2 file. Except around 1.5Gb for the file, and same for the folder)
2. Run `grb2_to_grib2.bat` (it will clean it up, and reduce it to around 150mb)
3. Open in XyGrib, and enjoy :)
4. Profit.

# Requirements

1. Need to have XyGrib installed (https://opengribs.org/en/xygrib)
2. Need to have wgrib2 installed (see here for Windows https://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/Windows10/v3.1.3/ or see in attachment for a zip file containing the Windows binary)

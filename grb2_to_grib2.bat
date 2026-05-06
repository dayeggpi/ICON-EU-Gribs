@echo off
REM ============================================================
REM GRIB2 -> XyGrib conversion
REM  Step 1: regrid to 0.125deg lat-lon (481x281 over Europe)
REM  Step 2: repack to c3 (complex + spatial diff, ~10x smaller than simple)
REM  Result: ~155 MB, XyGrib-compatible
REM
REM Usage:
REM   grb2_to_grib2.bat                  (convert forecast_data.grib2)
REM   grb2_to_grib2.bat myfile.grib2
REM ============================================================

set INPUT=%~1
if "%INPUT%"=="" set INPUT=forecast_data.grib2
set OUTPUT=forecast_data_xygrib.grib2
set TEMP_GRID=_regrid_temp.grib2

if not exist "%INPUT%" (
    echo ERROR: %INPUT% not found
    exit /b 1
)

echo Input : %INPUT%
echo Output: %OUTPUT%
echo.
echo Step 1/2: Regrid to 0.125deg over Europe [-15:45 lon, 35:70 lat] ...
wgrib2 "%INPUT%" ^
    -new_grid_winds earth ^
    -new_grid latlon "-15:481:0.125" "35:281:0.125" ^
    "%TEMP_GRID%"
if not exist "%TEMP_GRID%" (
    echo ERROR: regrid failed
    exit /b 1
)

echo.
echo Step 2/2: Repack to c3 (complex packing + spatial differencing) ...
wgrib2 "%TEMP_GRID%" -set_grib_type c3 -grib_out "%OUTPUT%"
del "%TEMP_GRID%"

if exist "%OUTPUT%" (
    echo.
    for %%A in ("%OUTPUT%") do echo Done: %OUTPUT%  (%%~zA bytes)
    echo Open %OUTPUT% in XyGrib.
) else (
    echo ERROR: output not created.
    exit /b 1
)

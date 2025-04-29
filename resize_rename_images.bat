@echo off
setlocal enabledelayedexpansion

echo Starting image processing script...
echo Current directory: %CD%

:: Ask user for name prefix
set /p "name_prefix=Enter name prefix for the images (e.g. 'Dyson'): "
echo Images will be named as: %name_prefix%1, %name_prefix%2, %name_prefix%3, etc.

:: Create output directory if it doesn't exist
if not exist "resized" mkdir "resized"
echo Created or verified "resized" directory exists.

:: Check if any image files exist
set "found_files=0"
for %%f in (*.jpg *.jpeg *.png) do set "found_files=1"

if "%found_files%"=="0" (
    echo No image files found in the current directory.
    echo Please make sure there are .jpg, .jpeg, or .png files in this folder.
    goto :end
)

:: Process all image files one by one
echo Found image files, starting processing...

:: Initialize counter for sequential numbering
set "counter=1"

:: Process JPG files
for %%f in (*.jpg) do (
    echo.
    echo Processing JPG file: %%f
    ffmpeg -i "%%f" -vf "crop=min(iw\,ih):min(iw\,ih):(iw-min(iw\,ih))/2:(ih-min(iw\,ih))/2,scale=1024:1024" "resized/%name_prefix%!counter!.jpg"
    if errorlevel 1 (
        echo Error processing %%f
    ) else (
        echo Successfully processed %%f to resized/%name_prefix%!counter!.jpg
        set /a "counter+=1"
    )
)

:: Process JPEG files
for %%f in (*.jpeg) do (
    echo.
    echo Processing JPEG file: %%f
    ffmpeg -i "%%f" -vf "crop=min(iw\,ih):min(iw\,ih):(iw-min(iw\,ih))/2:(ih-min(iw\,ih))/2,scale=1024:1024" "resized/%name_prefix%!counter!.jpg"
    if errorlevel 1 (
        echo Error processing %%f
    ) else (
        echo Successfully processed %%f to resized/%name_prefix%!counter!.jpg
        set /a "counter+=1"
    )
)

:: Process PNG files
for %%f in (*.png) do (
    echo.
    echo Processing PNG file: %%f
    ffmpeg -i "%%f" -vf "crop=min(iw\,ih):min(iw\,ih):(iw-min(iw\,ih))/2:(ih-min(iw\,ih))/2,scale=1024:1024" "resized/%name_prefix%!counter!.jpg"
    if errorlevel 1 (
        echo Error processing %%f
    ) else (
        echo Successfully processed %%f to resized/%name_prefix%!counter!.jpg
        set /a "counter+=1"
    )
)

echo.
echo Finished processing. Total images processed: !counter! - 1
echo Checking results:
dir resized

:end
echo.
echo Script completed. Press any key to exit.
pause > nul

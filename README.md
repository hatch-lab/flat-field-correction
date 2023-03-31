# Flat-field correction

This package contains two scripts: one to generate flat-field images from a tilescan, and one to use those flat-field images to correct micrographs.

## Installation
After cloning this repository, install packages:
```
pip install -r requirements.txt
```

## Generating flat-fields
1) Using Chromatek slides available in the Imaging Core. Find the center of the slide by moving the focus to the brightest point of the slide. You may need to adjust the gain to not blow out (and possibly damage) the detector; the slides are very bright.

2) Image the green slide with the 405 and 488 laser lines and the red slide with the 568 and 647 laser lines.

3) Set up a tile scan of ~25 non-overlapping images with a z-stack size >= the z-stack you wish to correct. By taking many positions, it will allow the script to smooth out imperfections in the slide to generate uniform images.

4) Save each tilescan as a separate LIF file to your computer.

4) Generate uniform TIFFs from each LIF file:
```
python make-flat-field.py /Path/To/Lif.lif
```
This will generate flat-field TIFFs in a `flat-fields` folder in the same directory as the LIF.


## Generating a dark-field
1) Take an image without the lasers on in each channel, from 647–405 and save the LIF. 

2) Save the LIF as a single TIFF stack.


## Correcting LIFs
Run:
```
python correct-lif.py /Path/To/Lif.lif /Path/to/dark-field.TIFF (channel /path/to/channel-flat-field.TIF)
```

## Examples
Correcting an image with 405 and 568 channels:
```
python correct-lif.py /Path/To/Lif.lif /Path/to/dark-field.TIFF 405 /path/to/405-flat-field.TIFF 568 /path/to/568-flat-field.TIFF
```
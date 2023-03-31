# coding=utf-8

"""
Takes a LIF with tilescans of a correction slide and makes a single z-stack for each tilescan where
each slice is the median of all slices in that z-stack

Usage:
  make-flat-field.py LIFPATH

Arguments:
  LIFPATH  Path to the .lif file

Options:
  -h --help  Show this screen.

Output:
  A TIFF for each tilescan that contains a single z-stack
"""

from pathlib import Path
from docopt import docopt
from tqdm import tqdm, trange
import numpy as np
from readlif.reader import LifFile

from tifffile import TiffWriter

arguments = docopt(__doc__, version='1.0')

lif_path = Path(arguments['LIFPATH']).resolve()
output_path = (lif_path / ('../flat-fields')).resolve()
output_path.mkdir(exist_ok=True)

lif = LifFile(str(lif_path))
tilescan = lif.get_image(0)
t = tqdm(total=tilescan.nz*tilescan.n_mosaic*len(lif.image_list), unit="slice")
for tilescan in lif.get_iter_image():
  if tilescan.channels > 1:
    exit("Too many channels")
  
  # We're going to go slice-by-slice
  # T, Z, C, Y, X
  new_image = np.empty(( 1, tilescan.nz, 1, tilescan.dims[0], tilescan.dims[1] ), dtype=np.uint8)
  for slice_idx in range(tilescan.nz):
    t.set_description('Processing %s, slice %d' % (tilescan.name, slice_idx+1))
    all_tilescans = np.empty(( tilescan.n_mosaic, tilescan.dims[0], tilescan.dims[1] ), dtype=np.uint8)
    for img_idx in range(tilescan.n_mosaic):
      t.set_description('Processing %s, slice %d, tile %d' % (tilescan.name, slice_idx+1, img_idx+1))
      all_tilescans[img_idx] = np.asarray(tilescan.get_frame(z=slice_idx, t=0, c=0, m=img_idx))
      t.update(1)
    new_image[0, slice_idx, 0] = np.median(all_tilescans, axis=0)
  
  writer = TiffWriter(output_path / (tilescan.name + ".tif"), imagej=True)
  meta = {
    'axes': 'TZCYX',
    'PhysicalSizeX': 1/tilescan.scale[0],
    'PhysicalSizeXUnit': "um",
    'PhysicalSizeY': 1/tilescan.scale[1],
    'PhysicalSizeYUnit': "um",
    'PhysicalSizeZ': 1/tilescan.scale[2],
    'PhysicalSizeZUnit': "um"
  }

  writer.write(new_image, metadata=meta, resolution=(tilescan.scale[0], tilescan.scale[1]))
  writer.close()

t.close()
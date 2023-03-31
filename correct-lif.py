# coding=utf-8

"""
Applies dark-/flat-field correction to the images in a LIF file

Usage:
  correct-lif.py <lif_path> <dark_tiff> (<channel> <channel_tiff>)...

Arguments:
  lif_path  Path to the .lif file
  dark_tiff  Path to the dark-field TIFF
  channel  The channel to correct. Can be 405, 488, 561, or 647
  channel_tiff  Path to the flat-field TIFF for each channel, in order

Options:
  -h --help  Show this screen.
  
Output:
  TIFFs corrected
"""

from pathlib import Path
from docopt import docopt
from tqdm import tqdm
import numpy as np
from skimage.exposure import rescale_intensity
from readlif.reader import LifFile
import tracemalloc
import cv2

from tifffile import TiffWriter, TiffFile

arguments = docopt(__doc__, version='1.0')

correct_lif = True

lif_path = Path(arguments['<lif_path>']).resolve()
if correct_lif:
  output_path = (lif_path / ('../corrected')).resolve()
else:
  output_path = (lif_path / ('../uncorrected')).resolve()
output_path.mkdir(exist_ok=True)

lif = LifFile(str(lif_path))

dark_field = (TiffFile(arguments['<dark_tiff>']).asarray()).astype(np.float64)

channel_fields = {}
avg_channel_gains = {}
channel_to_df_idx = {
  '647': 0,
  '561': 1,
  '488': 2,
  '405': 3
}

channels = arguments['<channel>']
for idx,channel_path in enumerate(arguments['<channel_tiff>']):
  channel = channels[idx]
  channel_fields[channel] = (TiffFile(channel_path).asarray()).astype(np.float64)-dark_field[channel_to_df_idx[channel]]
  avg_channel_gains[channel] = np.mean(channel_fields[channel], axis=(1,2))

tilescans = [i for i in lif.get_iter_image() if i.nz > 1]
max_ops = 0
for tilescan in tilescans:
  max_ops += tilescan.n_mosaic*tilescan.nz*tilescan.channels
t = tqdm(total=max_ops, unit="slice")
for tilescan in tilescans:
  # Register flat-field to current image
  tilescan.channel_as_second_dim = False
  ts_center = tilescan.nz//2
  for img_idx in range(tilescan.n_mosaic):
    writer = TiffWriter(output_path / (tilescan.name + "-" + str(img_idx) + ".tif"), imagej=True)
    new_image = np.empty(( 1, tilescan.nz, tilescan.channels, tilescan.dims[0], tilescan.dims[1] ), dtype=np.uint8)
    meta = {
      'axes': 'TZCYX',
      'PhysicalSizeX': 1/tilescan.scale[0],
      'PhysicalSizeXUnit': "um",
      'PhysicalSizeY': 1/tilescan.scale[1],
      'PhysicalSizeYUnit': "um",
      'PhysicalSizeZ': 1/tilescan.scale[2],
      'PhysicalSizeZUnit': "um"
    }
    for c_idx in range(tilescan.channels):
      channel = channels[c_idx]
      flat_center = channel_fields[channel].shape[0]//2
      flat_start = flat_center-ts_center
      for slice_idx in range(tilescan.nz):
        t.set_description('Processing %s, channel %s, tile %d, slice %d' % (tilescan.name, channels[c_idx], img_idx+1, slice_idx+1))
        this_slice = np.asarray(tilescan.get_frame(z=slice_idx, t=0, c=c_idx, m=img_idx), dtype=np.float64)
        if correct_lif:
          this_slice = this_slice-dark_field[channel_to_df_idx[channel]]
          this_slice[this_slice < 0] = 0
          this_slice /= channel_fields[channel][min((flat_start+slice_idx), channel_fields[channel].shape[0]-1)]
          this_slice *= avg_channel_gains[channel][min((flat_start+slice_idx), channel_fields[channel].shape[0]-1)]
          this_slice[this_slice > 255] = 255
        new_image[0, slice_idx, c_idx] = this_slice.astype(np.uint8)
        t.update(1)
    t.set_description('Writing file for %s, tile %d' % (tilescan.name, img_idx+1))
    writer.write(new_image, metadata=meta, resolution=(tilescan.scale[0], tilescan.scale[1]))
    writer.close()
t.close()

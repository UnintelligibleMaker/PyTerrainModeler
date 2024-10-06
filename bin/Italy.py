"""Italy.py
    This is an example of using the TerrainModeler class to generate a model of
    Italy.  If you were to print the lower layers in ocean blue and then a sandy
    and then a bit of green and then mountain brown.......
    __author__      = "Unintelligible Maker"
    __copyright__   = "Copyright 2024"
    __license__     = "MIT License"
    __version__     = "1.0"
    __maintainer__  = "Unintelligible Maker"
    __email__       = "maker@unintelligiblemaker.com"
    __project__     = "PyTerrainModeler"
"""

import logging
from argparse import ArgumentParser
import os
import sys

sys.path.insert(0, os.getcwd())
import pyterrainmodeler.terrain_modeler

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="TUrn on debug logging")
    parser.add_argument("-n", "--draft", action="store_true", help="TUrn on lower-res draft logging")
    args = parser.parse_args()
    if args.debug:
        logLevel = logging.DEBUG
    else:
        logLevel = logging.INFO

    size_x = 200
    size_y = 200
    if args.draft:
        x_steps = size_x
        y_steps = size_y
    else:
        x_steps = size_x * 5
        y_steps = size_y * 5

    logFormat = '%(asctime)s - %(filename)s.%(lineno)s - %(levelname)s -  %(process)d: %(message)s'
    logging.basicConfig(format=logFormat, level=logLevel)
    logging.debug(f"Args: {args}")

    logging.info(f"Initializing Class")
    terrain_modeler = pyterrainmodeler.terrain_modeler.TerrainModeler(latitude=36.206,  # Deg N/S
                                                                      longitude=11.811,  # Deg W/E
                                                                      longitude_size=(19.219267823041978 - 11.811),  # SE corner longitude - SW corner longitude
                                                                      size_x=size_x,  # 200 mm model, as my printer is 250x250 max
                                                                      size_y=size_y,  # 200 mm model, as my printer is 250x250 max
                                                                      steps_x=x_steps,  # 1 mm resolution Draft, 0.2 mm resolution Final
                                                                      steps_y=y_steps,  # 1 mm resolution Draft, 0.2 mm resolution Final
                                                                      scale_z=10.0,  # Make z features 10x the scale as x/y.  I like the look.
                                                                      offset_elevation=-300,  # If 0 is sea level then the water has no "base" and you print just the land.
                                                                      # By moving the water down -300 M you get the seafloor and/or some base.
                                                                      min_allowed_z=0.7,  # Force a min thickness of the base to be sea level to hide any sea floor and "add water".
                                                                      flatten_reference_elevation_meters=-20,  # This was a turning.
                                                                      # I wanted to put this right about at sea level but move it up/down till I got the best "water line"
                                                                      # where the land and water meet: I wanted it to LOOK like Italy.
                                                                      # I moved this until it did.
                                                                      flatten_factor=0.9,  # squish the mountains down a bit.
                                                                      flatten_mode=pyterrainmodeler.terrain_modeler.FlattenMode.BOTH,
                                                                      # I'm going to hide the sea floor any, so BOTH or POSITIVE both work. .....er TODO: is this the source of the -20 meters?
                                                                      geotiff_folder=os.path.join(os.getcwd(), "MapZen"))
    logging.info(f"Saving STL")
    stl_file_name = os.path.join(os.getcwd(), "terrain.stl")
    terrain_modeler.save_stl(filename=stl_file_name)
    logging.info(f"Done")
    exit(0)

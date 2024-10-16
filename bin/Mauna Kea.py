"""Mauna Kea.py
    This is an example of using the TerrainModeler class to generate a model of
    Mauna Kea.  If you were to print the lower layers in ocean blue and then a sandy
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

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pyterrainmodeler.terrain_modeler

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="Turn on debug logging")
    parser.add_argument("-n", "--draft", action="store_true", help="Turn on lower-res draft logging")
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
    terrain_modeler = pyterrainmodeler.terrain_modeler.TerrainModeler(latitude=18.700,  # Deg N/S for the SW corner
                                                                      longitude=-156.20,  # Deg W/E for the SW corner
                                                                      longitude_size=(156.20 - 154.50),  # SE corner longitude - SW corner longitude
                                                                      size_x=size_x,  # 200 mm model, as my printer is 250x250 max
                                                                      size_y=size_y,  # 200 mm model, as my printer is 250x250 max
                                                                      steps_x=x_steps,  # 1 mm resolution Draft, 0.2 mm resolution Final
                                                                      steps_y=y_steps,  # 1 mm resolution Draft, 0.2 mm resolution Final
                                                                      scale_z=4.0,  # Make z features 4x the scale as x/y for looks.
                                                                      # Comment out the next two lines if you want to see it without a base.
                                                                      offset_elevation=-50,  # Push the bottom of the model to -50m elevation
                                                                      min_allowed_z=0.22,  # Push the sea level back up to sea level by trial an error.
                                                                      # TODO add min_allowed_elevation
                                                                      geotiff_folder=os.path.join(os.getcwd(), "MapZen"))
    logging.info(f"Saving STL")
    stl_file_name = os.path.join(os.getcwd(), "terrain.stl")
    terrain_modeler.save_stl(filename=stl_file_name)
    logging.info(f"Done")
    exit(0)

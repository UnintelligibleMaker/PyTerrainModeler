"""Yosemite.py
    This is an example of using the TerrainModeler class to generate a model of
    Yosemite Valley in Yosemite National Park in California.  It includes El Cap
    and Half Dome.
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
    parser.add_argument("-d", "--debug", action="store_true", help="TUrn on debug logging")
    parser.add_argument("-n", "--draft", action="store_true", help="TUrn on lower-res draft logging")
    args = parser.parse_args()
    if args.debug:
        logLevel = logging.DEBUG
    else:
        logLevel = logging.INFO

    size_x = 200
    size_y = 150
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
    terrain_modeler = pyterrainmodeler.terrain_modeler.TerrainModeler(latitude=37.677360,  # Deg N/S for the SW corner
                                                                      longitude=-119.667382,  # Deg W/E for the SW corner
                                                                      longitude_size=0.205,  # Deg Wide W/E
                                                                      size_x=size_x,  # 200 mm model, as my printer is 250x250 max
                                                                      size_y=size_y,  # 200 mm model, as my printer is 250x250 max
                                                                      steps_x=x_steps,  # 200 steps (1 mm resolution draft)
                                                                      steps_y=y_steps,  # 1000 steps (0.2 mm resolution on Final)
                                                                      offset_elevation=1000,  # If 0 is sea level, the whole base gets kinda tall.  I want to push that down soo the base is not as tall.
                                                                      geotiff_folder=os.path.join(os.getcwd(), "MapZen"))
    logging.info(f"Saving STL")
    stl_file_name = os.path.join(os.getcwd(), "terrain.stl")
    terrain_modeler.save_stl(filename=stl_file_name)
    logging.info(f"Done")
    exit(0)

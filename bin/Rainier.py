"""Rainier.py

    This is an example of using the TerrainModeler class to generate a model of
    Lake Washington in Washington state.  The "cool" this able this is I use NOAA
    bathymetric .data to remove the water from the lake.  My intention here is to print the lake bed blue...to show depth
    but I'm not that far along in the project.  It's kina cool to see and maybe someone else will have a use for it too.
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

    if args.draft:
        x_y_steps = 200
    else:
        x_y_steps = 1000

    logFormat = '%(asctime)s - %(filename)s.%(lineno)s - %(levelname)s -  %(process)d: %(message)s'
    logging.basicConfig(format=logFormat, level=logLevel)
    logging.debug(f"Args: {args}")

    logging.info(f"Initializing Class")
    terrain_modeler = pyterrainmodeler.terrain_modeler.TerrainModeler(latitude=46.715750,  # Deg N/S
                                                                      longitude=-121.920366,  # Deg W/E
                                                                      longitude_size=0.384769,  # Deg Wide W/E
                                                                      size_x=200,  # 200 mm model, as my printer is 250x250 max
                                                                      size_y=200,  # 200 mm model, as my printer is 250x250 max
                                                                      steps_x=x_y_steps,  # 200 steps (200 steps or 1 mm resolution draft)
                                                                      steps_y=x_y_steps,  # 1000 steps (1000 steps or 0.2 mm resolution on full size)
                                                                      scale_z=1.25,  # Make z features 1.25x the scale as x/y, make it 25% taller because it looks better!
                                                                      offset_elevation=400,  # If 0 is sea level, the whole base gets kinda tall.  I want to push that down soo the base is not as tall.
                                                                      geotiff_folder=os.path.join(os.getcwd(), "MapZen"))
    logging.info(f"Saving STL")
    stl_file_name = os.path.join(os.getcwd(), "terrain.stl")
    terrain_modeler.save_stl(filename=stl_file_name)
    exit(0)

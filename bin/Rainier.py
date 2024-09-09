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
from terrain_modeler.terrain_modeler import TerrainModeler

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
    terrain_modeler = TerrainModeler(latitude=46.715750,
                                    longitude=-121.920366,
                                    longitude_size=0.384769,
                                    size_x=200,
                                    size_y=200,
                                    steps_x=x_y_steps,
                                    steps_y=x_y_steps,
                                    scale_z=1.25,
                                    offset_elevation=400,
                                    min_allowed_z=None,
                                    flatten_reference_elevation_meters=0,
                                    flatten_factor=1,
                                    flatten_mode=None,
                                    geotiff_folder=os.path.join(os.getcwd(), "MapZen"),
                                    max_processes=(os.cpu_count() * 2))
    logging.info(f"Saving STL")
    stl_file_name = os.path.join(os.getcwd(), "terrain.stl")
    terrain_modeler.save_stl(filename=stl_file_name)
    exit(0)

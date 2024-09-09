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
from terrain_modeler.terrain_modeler import TerrainModeler, FlattenMode

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
        x_steps = size_x * 4
        y_steps = size_y * 4

    logFormat = '%(asctime)s - %(filename)s.%(lineno)s - %(levelname)s -  %(process)d: %(message)s'
    logging.basicConfig(format=logFormat, level=logLevel)
    logging.debug(f"Args: {args}")

    logging.info(f"Initializing Class")
    terrain_modeler = TerrainModeler(latitude=36.206,
                                    longitude=11.811,
                                    longitude_size=(19.219267823041978 - 11.810939),
                                    size_x=size_x,
                                    size_y=size_y,
                                    steps_x=x_steps,
                                    steps_y=y_steps,
                                    scale_z=10.0,
                                    offset_elevation=-300,
                                    min_allowed_z=0.7,
                                    flatten_reference_elevation_meters=-20,
                                    flatten_factor=0.9,
                                    flatten_mode=FlattenMode.BOTH,
                                    geotiff_folder=os.path.join(os.getcwd(), "MapZen"),
                                    max_processes=(os.cpu_count() * 2))
    logging.info(f"Saving STL")
    stl_file_name = os.path.join(os.getcwd(), "terrain.stl")
    terrain_modeler.save_stl(filename=stl_file_name)
    logging.info(f"Done")
    exit(0)

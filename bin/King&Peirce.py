"""King&Peirce
    This is an example of using the TerrainModeler class to generate a model of
    King and Peirce counties here in Washington.
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

    if args.draft:
        x_y_steps = 200
    else:
        x_y_steps = 1000
        # Note this is 5x in the x and 5x in the y so this is ~25x as much processing as the draft.  There's a
        # reason draft mode exists.

    logFormat = '%(asctime)s - %(filename)s.%(lineno)s - %(levelname)s -  %(process)d: %(message)s'
    logging.basicConfig(format=logFormat, level=logLevel)
    logging.debug(f"Args: {args}")

    logging.info(f"Initializing Class")
    terrain_modeler = TerrainModeler(latitude=47.15,  # Deg N/S
                                    longitude=-123,  # Deg W/E
                                    longitude_size=1.213,  # Deg Wide W/E
                                    size_x=200,  # 200 mm model, as my printer is 250x250 max
                                    size_y=200,  # 200 mm model, as my printer is 250x250 max
                                    steps_x=x_y_steps,  # 200 steps (1/mm draft)
                                    steps_y=x_y_steps,  # 1000 steps (5/mm full size)
                                    scale_z=8,  # Make z features 8x the scale as x/y
                                    offset_elevation=-400,  # The shipping channel in the sounds is deep.  So lower the "zero"
                                    # offset_elevation=0,  # You can leave it and let the water be a hole.
                                    min_allowed_z=None,
                                    flatten_reference_elevation_meters=5,  # This is the height of Lake Washington.  I wanted
                                    # Mercer Island to "pop" ao I put this at the surface level of the lake.  The reality is
                                    # tuning these parameters is iterative and part of making a good model.  So use draft
                                    # mode and "play" until it looks good to you.
                                    flatten_factor=0.9,  # squish the mountains down a bit.
                                    flatten_mode=FlattenMode.POSITIVE,  # Only the mountains not the shipping channel.
                                    geotiff_folder=os.path.join(os.getcwd(), "MapZen"),
                                    max_processes=(os.cpu_count() * 2))  # Use them processors!
    logging.info(f"Saving STL")
    stl_file_name = os.path.join(os.getcwd(), "terrain.stl")
    terrain_modeler.save_stl(filename=stl_file_name)
    exit(0)

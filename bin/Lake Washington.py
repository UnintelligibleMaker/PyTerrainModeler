"""Lake Washington.py: A simple example of using the TerrainModeler class.

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

    size_x = 80
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
    xyz_folder = os.path.join(os.getcwd(), "example_xyz_files")

    # XYZ files from NOAA and others are is DEPTH, not elevation.
    # So you need to provide that for each file.
    # {surface elevation (in m): [file, file, file, ... ],
    #  surface elevation (in m): [file, file, file, ... ]}
    # First please know that the code for these is slow and not multiprocessor yet.
    # I only recently wrote it and it's subject to change (specifically I think I am
    # going to add a "tolerance" here for how close to surface level is "ok")
    # But I need to work on that code and thus far have never printed a model using it
    # I REALLY want to try and a lake depth print of something like Lake Tahoe.....but
    # SOOOO many projects and only one Unintelligible Maker.
    # Note: while EVERYTHING else is in meters: these files appear to all be in feet.
    # I need to make that a parameter per file......## TODO
    # but as before this is new in development code.  :)
    xyz_config = {5.7: [os.path.join(xyz_folder, "H11292.xyz"),
                        os.path.join(xyz_folder, "H11293.xyz"),
                        os.path.join(xyz_folder, "H11810.xyz"),
                        os.path.join(xyz_folder, "H11292a.xyz"),
                        os.path.join(xyz_folder, "H11293a.xyz"),
                        os.path.join(xyz_folder, "H11376.xyz"),
                        os.path.join(xyz_folder, "H11810a.xyz"),
                        os.path.join(xyz_folder, "H11377.xyz"), ]}
    logging.info(f"Initializing Class")
    terrain_modeler = pyterrainmodeler.terrain_modeler.TerrainModeler(
        latitude=47.483285,
        longitude=-122.3123689,
        longitude_size=(122.3123689 - 122.134938),
        size_x=size_x,
        size_y=size_y,
        steps_x=x_steps,
        steps_y=y_steps,
        scale_z=8,
        offset_elevation=-25,
        flatten_reference_elevation_meters=4.9,
        flatten_factor=1,
        flatten_mode=pyterrainmodeler.terrain_modeler.FlattenMode.POSITIVE,
        geotiff_folder=os.path.join(os.getcwd(), "MapZen"),
        xyz_config=xyz_config,  # Comment this line out to skip the xyz files and see both the
        # difference in model and processing time.
    )

    stl_file_name = "terrain.stl"
    logging.info(f"Saving STL file: {stl_file_name}")
    terrain_modeler.save_stl(filename=stl_file_name)
    exit(0)

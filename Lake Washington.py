import logging
from argparse import ArgumentParser
import os
from terrain_modeler.terrain_model import TerrainModler, FlattenMode

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
        x_steps = size_x * 4
        y_steps = size_y * 4

    logFormat = '%(asctime)s - %(filename)s.%(lineno)s - %(levelname)s -  %(process)d: %(message)s'
    logging.basicConfig(format=logFormat, level=logLevel)
    logging.debug(f"Args: {args}")
    xyz_folder = "/home/ken/Downloads/xyzs"

    # XYZ files from NOAA and others are is DEPTH, not elevation.
    # So you need to provide that for each file.
    # {surface elevation: [file, file, file, ... ],
    #  surface elevation: [file, file, file, ... ]}
    xyz_config = {5.7: [os.path.join(xyz_folder, "H11292.xyz"),
                        os.path.join(xyz_folder, "H11293.xyz"),
                        os.path.join(xyz_folder, "H11810.xyz"),
                        os.path.join(xyz_folder, "H11292a.xyz"),
                        os.path.join(xyz_folder, "H11293a.xyz"),
                        os.path.join(xyz_folder, "H11376.xyz"),
                        os.path.join(xyz_folder, "H11810a.xyz"),
                        os.path.join(xyz_folder, "H11377.xyz"),]}
                        # os.path.join(xyz_folder, "ktm.xyz"),]}
    logging.info(f"Initializing Class")
    terrain_modeler = TerrainModler(
                                    latitude=47.483285,
                                    # latitude=47.5100,
                                    # longitude=-122.2496,
                                    longitude=-122.3123689,
                                    longitude_size=(122.3123689 - 122.134938),
                                    # longitude_size=(122.2496 - 122.2100),
                                    size_x=size_x,
                                    size_y=size_y,
                                    steps_x=x_steps,
                                    steps_y=y_steps,
                                    scale_z=8,
                                    offset_elevation=0,
                                    min_allowed_z=0.30,
                                    flatten_reference_elevation_meters=4.9,
                                    flatten_factor=1,
                                    flatten_mode=FlattenMode.POSITIVE,
                                    geotiff_folder="/home/ken/Downloads/mapzen_geotiffs",
                                    # xyz_config=xyz_config,
                                    max_processes=(os.cpu_count() * 2))
    stl_file_name = "terrain.stl"
    logging.info(f"Saving STL file: {stl_file_name}")
    terrain_modeler.save_stl(filename=stl_file_name)
    exit(0)

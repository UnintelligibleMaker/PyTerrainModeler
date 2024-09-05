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

    if args.draft:
        x_y_steps = 4
    else:
        x_y_steps = 600

    logFormat = '%(asctime)s - %(filename)s.%(lineno)s - %(levelname)s -  %(process)d: %(message)s'
    logging.basicConfig(format=logFormat, level=logLevel)
    logging.debug(f"Args: {args}")

    logging.info(f"Initializing Class")
    terrain_modeler = TerrainModler(latitude=47.15,
                                    longitude=-123,
                                    longitude_size=1.213,
                                    size_x=200,
                                    size_y=200,
                                    steps_x=x_y_steps,
                                    steps_y=x_y_steps,
                                    scale_z=8,
                                    offset_elevation=1,
                                    min_allowed_z=None,
                                    flatten_reference_elevation_meters=5,
                                    flatten_factor=0.9,
                                    flatten_mode=FlattenMode.POSITIVE,
                                    geotiff_folder="/home/ken/Downloads/mapzen_geotiffs",
                                    # xyz_folder="/home/ken/Downloads/xyzs",
                                    max_processes=(os.cpu_count() * 2))
    logging.info(f"Saving STL")
    stl_file_name = os.path.join(os.getcwd(), "terrain.stl")
    terrain_modeler.save_stl(filename=stl_file_name)
    exit(0)

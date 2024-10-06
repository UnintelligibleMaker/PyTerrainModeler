"""elevation_manager.py:
    This defines the ElevationManager that is responsible for managing elevation data from GeoTIFF files and potentially
    other sources in the future. It uses a multiprocessing safe elevation cache however the GeoTiffs are not shared across
    processes.  This was both to simplify implementation as well as to allow very large maps to not have all GeoTiffs open
    at once.  Additionally it means that when the gridding processes die all the geotiffs go with them.
    __author__      = "Unintelligible Maker"
    __copyright__   = "Copyright 2024"
    __license__     = "MIT License"
    __version__     = "1.0"
    __maintainer__  = "Unintelligible Maker"
    __email__       = "maker@unintelligiblemaker.com"
    __project__     = "PyTerrainModeler"
"""

import logging
import os
import math
from geotiff import GeoTiff
from numpy import array as nparray
from multiprocessing import Manager


class ElevationManager(object):

    def __init__(self,
                 geotiff_folder=None,
                 resolution=4):
        """
        :param geotiff_folder: The folder where the geotiffs are stored
        :param resolution: The resolution (10 ^ -n) of the elevation data.
             Default is 4 or 0.0001 deg of lat/long which is like 10m or less
                        5 is 0.00001 deg of lat/long which is like 1m or less
                        6 is 0.000001 deg of lat/long which is like 11 cm or less
                        This is all probably more than the GeoTIFFs themselves.
        """
        self.geotiff_folder = geotiff_folder
        self.resolution = max(resolution, 4)

        self.elevation_cache = Manager().dict()

        self.open_geotiffs = {}

    def _increment_by_resolution(self, initial_value):
        """
        :param initial_value: The value to increment
        :return: The value incremented by the resolution
        """
        return self._increment_by_n_resolution(initial_value=initial_value, n=1)

    def _decrement_by_resolution(self, initial_value):
        """
        :param initial_value: The value to decrement
        :return: The value decremented by the resolution
        """
        return self._increment_by_n_resolution(initial_value=initial_value, n=-1)

    def _increment_by_n_resolution(self, initial_value, n):
        """
        :param initial_value: The value to increment
        :param n: The number of times to increment (or decrement if negative) the value by the resolution
        :return: The value incremented by the resolution * n
        """
        rounded_initial_value = round(initial_value, self.resolution)
        delta = round(pow(0.1, self.resolution), self.resolution)
        n_delta = n * delta
        final_value = rounded_initial_value + n_delta
        return round(final_value, self.resolution)

    def get_elevation_for_latitude_longitude(self, latitude, longitude):
        """
        :param latitude: The latitude to get the elevation for
        :param longitude: The longitude to get the elevation for
        :return: The elevation at the given latitude and longitude
        """
        rounded_latitude = round(latitude, self.resolution)
        rounded_longitude = round(longitude, self.resolution)
        logging.debug(f"rounded location: '{rounded_latitude}' & '{rounded_longitude}'")
        elevation_cache_key = f"({rounded_latitude},{rounded_longitude})"

        if elevation_cache_key in self.elevation_cache:
            return self.elevation_cache[elevation_cache_key]

        elevation = self._get_elevation_from_geotiff(latitude=rounded_latitude, longitude=rounded_longitude)
        if elevation is not None:
            self.elevation_cache[elevation_cache_key] = elevation
            return self.elevation_cache[elevation_cache_key]

        raise ValueError("Could not find a value for the elevation")

    def _get_elevation_from_geotiff(self, latitude, longitude):
        """
        :param latitude: The latitude to get the elevation for
        :param longitude: The longitude to get the elevation for
        :return: The elevation at the given latitude and longitude
        """
        geotiff_filename = self._get_geotiff_filename(latitude=latitude, longitude=longitude)
        if geotiff_filename not in self.open_geotiffs:
            geotiff_file = geotiff_filename
            logging.debug(f"Elevation GeoTiff for ({latitude},{longitude}) is not loaded.  Loading file {geotiff_file}")
            geotiff = GeoTiff(geotiff_file, 0)
            zarr_array = geotiff.read()
            array = nparray(zarr_array)
            self.open_geotiffs.update({geotiff_filename: (geotiff, array)})
        else:
            geotiff, array = self.open_geotiffs.get(geotiff_filename)
        x = geotiff._get_x_int(float(longitude))
        y = geotiff._get_y_int(float(latitude))
        elevation = float(array[y][x])
        if elevation is not None:
            logging.debug(f"Elevation GeoTiff Hit: ({latitude},{longitude}) = {elevation}m")
        else:
            logging.debug(f"Elevation GeoTiff Miss: ({latitude},{longitude})")
        return elevation

    def _get_geotiff_filename(self, latitude, longitude):
        """
        :param latitude: The latitude to get the geotiff filename for
        :param longitude: The longitude  to get the geotiff filename for
        :return: The geotiff filename for the given latitude and longitude
        """
        if latitude < 0.0:
            latitude_component = f"S{format(abs(math.floor(latitude)), '02d')}"
        else:
            latitude_component = f"N{format(math.floor(latitude), '02d')}"

        if longitude < 0.0:
            longitude_component = f"W{format(abs(math.floor(1.0 * longitude)), '03d')}"
        else:
            longitude_component = f"E{format(math.floor(longitude), '03d')}"

        geotiff_filename = os.path.join(self.geotiff_folder, latitude_component, f"{latitude_component}{longitude_component}.tiff")
        logging.debug(f"Geotiff Filename: {geotiff_filename}")
        return geotiff_filename

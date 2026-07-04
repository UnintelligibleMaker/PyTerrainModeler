"""elevation_manager.py:
    This defines the ElevationManager that is responsible for managing elevation data from HGT.GZ files and potentially
    other sources in the future. It uses a multiprocessing safe elevation cache however the HGT.GZ files are not shared across
    processes.  This was both to simplify implementation as well as to allow very large maps to not have all HGT.GZ files open
    at once.  Additionally it means that when the gridding processes die all the HGT.GZ files go with them.
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
import gzip
from typing import Any, Optional, Dict, Tuple
from numpy import array as nparray, frombuffer, ndarray
from multiprocessing import Manager


FEET_TO_METERS: float = 0.3048


class ElevationManager(object):

    def __init__(self,
                 hgt_gz_folder: Optional[str] = None,
                 geotiff_override: Optional[str] = None,
                 geotiff_units: str = 'meters',
                 resolution: int = 10):
        """
        :param hgt_gz_folder: The folder where the hgt.gz files are stored
        :param geotiff_override: Optional path to a single GeoTIFF used as the primary elevation source.
                Points inside the raster with valid data are taken from the GeoTIFF; everything else falls back to hgt.gz.
        :param geotiff_units: Vertical units of the GeoTIFF's pixel values.  'meters' (default) or 'feet'.
        :param resolution: The resolution (10 ^ -n) of the elevation data.
             Default is 4 or 0.0001 deg of lat/long which is like 10m or less
                        5 is 0.00001 deg of lat/long which is like 1m or less
                        6 is 0.000001 deg of lat/long which is like 11 cm or less
                        This is all probably more than the elevation data itself.
        """
        self.hgt_gz_folder: Optional[str] = hgt_gz_folder
        self.geotiff_override: Optional[str] = geotiff_override
        self.geotiff_units: str = geotiff_units
        self.resolution: int = max(resolution, 10)

        self.elevation_cache: Dict[str, float] = Manager().dict()

        self.open_files: Dict[str, Tuple[int, ndarray]] = {}
        self.open_geotiff: Dict[str, Tuple[Any, Any, ndarray, Optional[float], int, int]] = {}

    def _increment_by_resolution(self, initial_value: float) -> float:
        """
        :param initial_value: The value to increment
        :return: The value incremented by the resolution
        """
        return self._increment_by_n_resolution(initial_value=initial_value, n=1)

    def _decrement_by_resolution(self, initial_value: float) -> float:
        """
        :param initial_value: The value to decrement
        :return: The value decremented by the resolution
        """
        return self._increment_by_n_resolution(initial_value=initial_value, n=-1)

    def _increment_by_n_resolution(self, initial_value: float, n: int) -> float:
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

    def get_elevation_for_latitude_longitude(self, latitude: float, longitude: float) -> float:
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

        elevation = None
        if self.geotiff_override:
            elevation = self._get_elevation_from_geotiff(latitude=rounded_latitude, longitude=rounded_longitude)

        if elevation is None and self.hgt_gz_folder:
            elevation = self._get_elevation_from_hgt_gz(latitude=rounded_latitude, longitude=rounded_longitude)

        if elevation is not None:
            self.elevation_cache[elevation_cache_key] = elevation
            return self.elevation_cache[elevation_cache_key]

        raise ValueError("Could not find a value for the elevation")

    def _get_elevation_from_geotiff(self, latitude: float, longitude: float) -> Optional[float]:
        """
        :param latitude: The latitude to get the elevation for
        :param longitude: The longitude to get the elevation for
        :return: The elevation at the given latitude and longitude from the override GeoTIFF,
                 or None if the point is outside the raster bounds or the pixel is NoData.
        """
        if self.geotiff_override not in self.open_geotiff:
            import rasterio
            from pyproj import Transformer
            logging.info(f"Loading GeoTIFF override {self.geotiff_override}")
            with rasterio.open(self.geotiff_override) as dataset:
                if dataset.crs is None:
                    raise ValueError(f"GeoTIFF {self.geotiff_override} has no CRS; cannot transform lat/lon to its grid.")
                transformer = Transformer.from_crs("EPSG:4326", dataset.crs, always_xy=True)
                affine = dataset.transform
                array = dataset.read(1)
                nodata = dataset.nodata
                height, width = array.shape
            self.open_geotiff[self.geotiff_override] = (transformer, affine, array, nodata, width, height)

        transformer, affine, array, nodata, width, height = self.open_geotiff[self.geotiff_override]

        x, y = transformer.transform(longitude, latitude)
        col_f, row_f = ~affine * (x, y)
        col, row = int(col_f), int(row_f)

        if not (0 <= col < width and 0 <= row < height):
            logging.debug(f"GeoTIFF Miss (out of bounds): ({latitude},{longitude})")
            return None

        value = float(array[row, col])

        if value != value:  # NaN
            logging.debug(f"GeoTIFF Miss (NaN): ({latitude},{longitude})")
            return None
        if nodata is not None and value == float(nodata):
            logging.debug(f"GeoTIFF Miss (NoData): ({latitude},{longitude})")
            return None

        if self.geotiff_units == 'feet':
            value = value * FEET_TO_METERS

        logging.debug(f"GeoTIFF Hit: ({latitude},{longitude}) = {value}m")
        return value

    def _get_elevation_from_hgt_gz(self, latitude: float, longitude: float) -> Optional[float]:
        """
        :param latitude: The latitude to get the elevation for
        :param longitude: The longitude to get the elevation for
        :return: The elevation at the given latitude and longitude
        """
        hgt_gz_filename = self._get_hgt_gz_filename(latitude=latitude, longitude=longitude)
        if not os.path.exists(hgt_gz_filename):
            return None

        if hgt_gz_filename not in self.open_files:
            logging.debug(f"Elevation HGT.GZ for ({latitude},{longitude}) is not loaded. Loading file {hgt_gz_filename}")
            with gzip.open(hgt_gz_filename, 'rb') as f:
                data = f.read()
            dimension = int(math.sqrt(len(data) / 2))
            array = frombuffer(data, dtype='>i2').reshape((dimension, dimension))
            self.open_files.update({hgt_gz_filename: (dimension, array)})
        else:
            dimension, array = self.open_files.get(hgt_gz_filename)

        lat_frac = latitude - math.floor(latitude)
        lon_frac = longitude - math.floor(longitude)

        row = int((1.0 - lat_frac) * (dimension - 1))
        col = int(lon_frac * (dimension - 1))

        elevation = float(array[row, col])
        if elevation is not None:
            logging.debug(f"Elevation HGT.GZ Hit: ({latitude},{longitude}) = {elevation}m")
        else:
            logging.debug(f"Elevation HGT.GZ Miss: ({latitude},{longitude})")
        return elevation

    def _get_hgt_gz_filename(self, latitude: float, longitude: float) -> str:
        """
        :param latitude: The latitude to get the hgt.gz filename for
        :param longitude: The longitude to get the hgt.gz filename for
        :return: The hgt.gz filename for the given latitude and longitude
        """
        if latitude < 0.0:
            latitude_component = f"S{format(abs(math.floor(latitude)), '02d')}"
        else:
            latitude_component = f"N{format(math.floor(latitude), '02d')}"

        if longitude < 0.0:
            longitude_component = f"W{format(abs(math.floor(1.0 * longitude)), '03d')}"
        else:
            longitude_component = f"E{format(math.floor(longitude), '03d')}"

        hgt_gz_filename = os.path.join(self.hgt_gz_folder, latitude_component, f"{latitude_component}{longitude_component}.hgt.gz")
        logging.debug(f"HGT.GZ Filename: {hgt_gz_filename}")
        return hgt_gz_filename

import logging
import os
import math
from enum import Enum
from geotiff import GeoTiff
from numpy import array as nparray
from multiprocessing import Process, Manager, cpu_count
from geopy import Point, distance
from multiprocessing import Process, Manager, cpu_count, Pool, set_start_method, Queue, Pool


class XYZFileTypes(Enum):
    TYPE_A = 1
    TYPE_B = 2


ALLOWED_DELTA = 0.1
class ElevationManager(object):

    def __init__(self,
                 origin_point,
                 far_point,
                 geotiff_folder=None,
                 xyz_config=None,
                 resolution=4):
        self.geotiff_folder = geotiff_folder
        self.resolution = max(resolution, 4)

        # self.min_latitude = min(self._increment_by_n_resolution(initial_value=origin_point.latitude, n=-10),
        #                         self._increment_by_n_resolution(initial_value=far_point.latitude, n=-10))
        #
        # self.max_latitude = max(self._increment_by_n_resolution(initial_value=origin_point.latitude, n=10),
        #                         self._increment_by_n_resolution(initial_value=far_point.latitude, n=10))
        #
        # self.min_longitude = min(self._increment_by_n_resolution(initial_value=origin_point.longitude, n=-10),
        #                         self._increment_by_n_resolution(initial_value=far_point.longitude, n=-10))
        #
        # self.max_longitude = max(self._increment_by_n_resolution(initial_value=origin_point.longitude, n=10),
        #                         self._increment_by_n_resolution(initial_value=far_point.longitude, n=10))
        #
        self.elevation_cache = Manager().dict()
        # self.override_elevation_cache = {} # Manager().dict()

        self.open_geotiffs = {}
        # if xyz_config:
        #     for surface_elevation, files in xyz_config.items():
        #         logging.info(f"Processing surface_elevation {surface_elevation} files from {files}")
        #         self._process_xyz_surface_elevation(surface_elevation, files)
        # self.open_geotiffs = {}

    # def _process_xyz_surface_elevation(self, surface_elevation, files):
    #     points = []
    #     for xyz_file in files:
    #         with (open(xyz_file) as f):
    #             file_format = None
    #             for line in f.readlines():
    #                 if file_format is None:
    #                     if line.count(',') == 5 and line.count('\t') == 0:
    #                         file_format = XYZFileTypes.TYPE_A
    #                         logging.info(f"Fount TypeA File")
    #                     elif line.count(',') == 0 and line.count('\t') == 3:
    #                         file_format = XYZFileTypes.TYPE_B
    #                         logging.info(f"Fount TypeB File")
    #                     else:
    #                         raise TypeError(f"File type of {xyz_file} is unknown. Pattern is: {line.count(',')}-{line.count('\t')}")
    #                     continue
    #                 if file_format == XYZFileTypes.TYPE_A:
    #                     survey_id, latitude, longitude, depth, quality_code, active = line.split(',')
    #                 elif file_format == XYZFileTypes.TYPE_B:
    #                     survey_id, longitude, latitude, depth = line.split('\t')
    #                 rounded_latitude = round(float(latitude), self.resolution)
    #                 rounded_longitude = round(float(longitude), self.resolution)
    #                 depth = float(depth) / 3.28084  ## This is feet? ##TODO
    #                 current_point = Point(latitude=rounded_latitude, longitude=rounded_longitude)
    #                 elevation_cache_key = f"({rounded_latitude},{rounded_longitude})"
    #
    #                 if self._check_override_eligible(current_point, surface_elevation):
    #                     logging.debug(f"Eligible point: ({latitude},{longitude})")
    #                     if elevation_cache_key not in self.override_elevation_cache:
    #                         points.append((rounded_latitude, rounded_longitude, depth))
    #                         self.override_elevation_cache[elevation_cache_key] = -depth
    #                     elif self.override_elevation_cache[elevation_cache_key] != -depth:
    #                         logging.warning(f"Duplicate point for ({rounded_latitude}, {rounded_longitude}) : {-depth} vs {self.override_elevation_cache[elevation_cache_key]}")
    #                         if self.override_elevation_cache[elevation_cache_key] > -depth:
    #                             points.remove((rounded_latitude, rounded_longitude, -self.override_elevation_cache[elevation_cache_key]))
    #                             points.append((rounded_latitude, rounded_longitude, depth))
    #                             self.override_elevation_cache[elevation_cache_key] = -depth
    #     logging.debug(f"points: {len(points)}\t\toverrides: {len(self.override_elevation_cache)}")
    #     points_surface_elevation = [(surface_elevation, points)]
    #     with Pool(self.max_processes) as p:
    #         while points_surface_elevation:
    #             logging.info(f"points_surface_elevation: {len(points_surface_elevation)}\t\toverrides: {len(self.override_elevation_cache)}")
    #             points_surface_elevation = p.map(self._process_x_y_z_points, points_surface_elevation)

    # def _process_x_y_z_points(self, surface_elevation, points):
    #     return_points = []
    #     for latitude, longitude, depth in points:
    #         neighbors = [(self._decrement_by_resolution(latitude), self._decrement_by_resolution(longitude)),
    #                      (self._decrement_by_resolution(latitude), longitude),
    #                      (self._decrement_by_resolution(latitude), self._increment_by_resolution(longitude)),
    #                      (latitude, self._decrement_by_resolution(longitude)),
    #                      (latitude, self._increment_by_resolution(longitude)),
    #                      (self._increment_by_resolution(latitude), self._decrement_by_resolution(longitude)),
    #                      (self._increment_by_resolution(latitude), longitude),
    #                      (self._increment_by_resolution(latitude), self._increment_by_resolution(longitude))]
    #         for neighbor_latitude, neighbor_longitude in neighbors:
    #             if neighbor_latitude < self.min_latitude or neighbor_latitude > self.max_latitude or neighbor_longitude < self.min_longitude or neighbor_longitude > self.max_longitude:
    #                 continue
    #             else:
    #                 elevation_cache_key = f"({neighbor_latitude},{neighbor_longitude})"
    #                 if elevation_cache_key not in self.override_elevation_cache:
    #                     if self._check_override_eligible(Point(latitude=neighbor_latitude, longitude=neighbor_longitude), surface_elevation):
    #                         return_points.append((neighbor_latitude, neighbor_longitude, depth))
    #                         self.override_elevation_cache[elevation_cache_key] = -depth
    #     return (surface_elevation, return_points)
    def _increment_by_resolution(self, initial_value):
        return self._increment_by_n_resolution(initial_value=initial_value, n=1)

    def _decrement_by_resolution(self, initial_value):
        return self._increment_by_n_resolution(initial_value=initial_value, n=-1)
    def _increment_by_n_resolution(self, initial_value, n):
        rounded_initial_value = round(initial_value, self.resolution)
        delta = round(pow(0.1, self.resolution), self.resolution)
        n_delta = n * delta
        final_value = rounded_initial_value + n_delta
        return round(final_value, self.resolution)

        # overrides_added = True
        # radius = 0
        # while overrides_added:
        #     overrides_added = 0
        #     radius += 1
        #     for point in points:
        #         min_lattitude = point[0] - (radius * round(math.pow(0.1, self.resolution), self.resolution))
        #         max_lattitude = point[0] + (radius * round(math.pow(0.1, self.resolution), self.resolution))
        #         min_longitude = point[1] - (radius * round(math.pow(0.1, self.resolution), self.resolution))
        #         max_longitude = point[1] + (radius * round(math.pow(0.1, self.resolution), self.resolution))
        #         latitude = min_lattitude
        #         while latitude <= max_lattitude:
        #             current_point_a = Point(latitude=latitude, longitude=min_longitude)
        #             current_point_b = Point(latitude=latitude, longitude=max_longitude)
        #
        #             elevation_cache_key_a = f"({latitude},{min_longitude})"
        #             elevation_cache_key_b = f"({latitude},{max_longitude})"
        #
        #             if elevation_cache_key_a not in self.override_elevation_cache and self._check_override_eligible(current_point_a, surface_elevation):
        #                 self.override_elevation_cache[elevation_cache_key_a] = -point[2]
        #                 overrides_added += 1
        #
        #             if elevation_cache_key_b not in self.override_elevation_cache and self._check_override_eligible(current_point_b, surface_elevation):
        #                 self.override_elevation_cache[elevation_cache_key_b] = -point[2]
        #                 overrides_added += 1
        #
        #             latitude = round(latitude + round(math.pow(0.1, self.resolution), self.resolution), self.resolution)
        #
        #         longitude = min_longitude
        #         while longitude <= max_longitude:
        #             current_point_a = Point(latitude=min_lattitude, longitude=longitude)
        #             current_point_b = Point(latitude=max_lattitude, longitude=longitude)
        #
        #             elevation_cache_key_a = f"({min_lattitude},{longitude})"
        #             elevation_cache_key_b = f"({max_lattitude},{longitude})"
        #
        #             if elevation_cache_key_a not in self.override_elevation_cache and self._check_override_eligible(current_point_a, surface_elevation):
        #                 self.override_elevation_cache[elevation_cache_key_a] = -point[2]
        #                 overrides_added += 1
        #
        #             if elevation_cache_key_b not in self.override_elevation_cache and self._check_override_eligible(current_point_b, surface_elevation):
        #                 self.override_elevation_cache[elevation_cache_key_b] = -point[2]
        #                 overrides_added += 1
        #
        #             longitude = round(longitude + round(math.pow(0.1, self.resolution), self.resolution), self.resolution)
        #     logging.info(f"added {overrides_added} overrides.  override_elevation_cache len: {len(self.override_elevation_cache)}")

        # exit(1)
    #                 elevation = float(surface_elevation) - depth
    #                 logging.debug(f"{latitude}, {longitude} = {depth} = {elevation}")
    #     processes = []
    #     for xyz_filename in os.listdir(xyz_folder):
    #         xyz_file = os.path.join(xyz_folder, xyz_filename)
    #         process = Process(target=self._process_xyz_file, args=((xyz_file, )))
    #         process.start()
    #         processes.append(process)
    #     while processes:
    #         processes.pop().join()
    #     # for xyz_filename in os.listdir(xyz_folder):
    #     #     xyz_file = os.path.join(xyz_folder, xyz_filename)
    #     #     self._process_xyz_file(xyz_file)
    #
    # def _process_xyz_file(self, xyz_file, surface_elevation):
    #     impact_ratio = 0.1
    #
    #     if os.path.isfile(xyz_file):
    #         logging.info(f"Processing xyz file: {xyz_file}")
    #         with (open(xyz_file) as f):
    #             file_format = None
    #             for line in f.readlines():
    #                 if file_format is None:
    #                     if line.count(',') == 5 and line.count('\t') == 0:
    #                         file_format = XYZFileTypes.TYPE_A
    #                         logging.info(f"Fount TypeA File")
    #                     elif line.count(',') == 0 and line.count('\t') == 3:
    #                         file_format = XYZFileTypes.TYPE_B
    #                         logging.info(f"Fount TypeB File")
    #                     else:
    #                         raise TypeError(f"File type of {xyz_file} is unknown. Pattern is: {line.count(',')}-{line.count('\t')}")
    #                     continue
    #                 if file_format == XYZFileTypes.TYPE_A:
    #                     survey_id, latitude, longitude, depth, quality_code, active = line.split(',')
    #                 elif file_format == XYZFileTypes.TYPE_B:
    #                     survey_id, longitude, latitude, depth = line.split('\t')
    #                 latitude = float(latitude)
    #                 longitude = float(longitude)
    #                 depth = float(depth) / 3.28084  ## This is feet? ##TODO
    #                 elevation = float(surface_elevation) - depth
    #                 logging.debug(f"{latitude}, {longitude} = {depth} = {elevation}")
    #
    #                 measured_point = Point(latitude=latitude, longitude=longitude)
    #                 sw_from_measured_point = distance.distance(meters=10*depth).destination(distance.distance(meters=10*depth).destination(measured_point, bearing=270), bearing=180)
    #                 logging.debug(f"SW = {sw_from_measured_point.latitude} = {sw_from_measured_point.longitude}")
    #
    #                 ne_from_measured_point = distance.distance(meters=10*depth).destination(distance.distance(meters=10*depth).destination(measured_point, bearing=90), bearing=0)
    #                 logging.debug(f"NE = {ne_from_measured_point.latitude} = {ne_from_measured_point.longitude}")
    #
    #                 current_latitude = round(sw_from_measured_point.latitude, self.resolution)
    #                 while current_latitude <= round(ne_from_measured_point.latitude, self.resolution):
    #                     current_longitude = round(sw_from_measured_point.longitude, self.resolution)
    #                     while current_longitude <= round(ne_from_measured_point.longitude, self.resolution):
    #                         current_point = Point(latitude=current_latitude, longitude=current_longitude)
    #                         logging.debug(f"remote = {current_latitude} = {current_longitude}")
    #                         if self._check_override_eligible(current_point, surface_elevation):
    #                             logging.debug(f"Eligible point: ({latitude},{longitude})")
    #                             distance_to_measured = distance.geodesic(measured_point, current_point).m
    #                             impact = -depth # min(0, (distance_to_measured/impact_ratio) - depth)
    #                             if round(impact, self.resolution) != 0:
    #                                 elevation_cache_key = f"({current_latitude},{current_longitude})"
    #                                 if elevation_cache_key not in self.override_elevation_cache:
    #                                     self.override_elevation_cache[elevation_cache_key] = impact
    #                                 else:
    #                                     self.override_elevation_cache[elevation_cache_key] = min(self.override_elevation_cache[elevation_cache_key], impact)
    #                         else:
    #                             logging.debug(f"ineligible point: ({latitude},{longitude}): {self.get_elevation_for_latitude_longitude(current_latitude, current_longitude, True)} vs {surface_elevation}")
    #                         current_longitude = round(current_longitude + math.pow(0.1, self.resolution))
    #                         logging.debug(f"remote = {current_latitude} = {current_longitude}")
    #                     current_latitude = round(current_latitude + math.pow(0.1, self.resolution))
    #                     logging.debug(f"remote = {current_latitude} = {current_longitude}")

    def _check_override_eligible(self, point, eligible_elevation):
        eligible_radii = 2
        current_latitude = self._increment_by_n_resolution(point.latitude, -eligible_radii)
        while current_latitude <= self._increment_by_n_resolution(point.latitude, eligible_radii):
            current_longitude = self._increment_by_n_resolution(point.longitude, -eligible_radii)
            while current_longitude <= self._increment_by_n_resolution(point.longitude, eligible_radii):
                geotiff_elevation = self.get_elevation_for_latitude_longitude(current_latitude, current_longitude, True)
                if geotiff_elevation < (eligible_elevation - 0.1) or (eligible_elevation + 0.1) < geotiff_elevation:
                    logging.debug(f"Failed check: {eligible_elevation} vs {geotiff_elevation}")
                    return False
                current_longitude = self._increment_by_resolution(current_longitude)
            current_latitude = self._increment_by_resolution(current_latitude)
        return True

    def get_elevation_for_latitude_longitude(self, latitude, longitude, bypass_override_cache=False):

        rounded_latitude = round(latitude, self.resolution)
        rounded_longitude = round(longitude, self.resolution)
        logging.debug(f"rounded location: '{rounded_latitude}' & '{rounded_longitude}'")
        elevation_cache_key = f"({rounded_latitude},{rounded_longitude})"

        if elevation_cache_key in self.elevation_cache:
            # if bypass_override_cache or elevation_cache_key not in self.override_elevation_cache:
            return self.elevation_cache[elevation_cache_key]
            # else:
            #     logging.info(f"Returning {self.elevation_cache[elevation_cache_key] + self.override_elevation_cache[elevation_cache_key]} vs {self.elevation_cache[elevation_cache_key]} thanks to the override cache")
            #     return self.elevation_cache[elevation_cache_key] + self.override_elevation_cache[elevation_cache_key]

        elevation = self._get_elevation_from_geotiff(latitude=rounded_latitude, longitude=rounded_longitude)
        if elevation is not None:
            self.elevation_cache[elevation_cache_key] = elevation
            # if bypass_override_cache or elevation_cache_key not in self.override_elevation_cache:
            return self.elevation_cache[elevation_cache_key]
            # else:
            #     logging.info(f"Returning {self.elevation_cache[elevation_cache_key] + self.override_elevation_cache[elevation_cache_key]} vs {self.elevation_cache[elevation_cache_key]} thanks to the override cache")
            #     return self.elevation_cache[elevation_cache_key] + self.override_elevation_cache[elevation_cache_key]

        raise ValueError("Could not find a value for the elevation")

    def _get_elevation_from_geotiff(self, latitude, longitude):
        geotiff_filename = self._get_geotiff_filename(latitude=latitude, longitude=longitude)
        if geotiff_filename not in self.open_geotiffs:
            geotiff_file = os.path.join(self.geotiff_folder, geotiff_filename)
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

        if latitude < 0.0:
            raise NotImplemented("Sorry I haven't coded this for the southern hemisphere yet!")
        else:
            latitude_component = f"N{format(math.floor(latitude), '02d')}"

        if longitude < 0.0:
            longitude_component = f"W{format(math.ceil(-1.0 * longitude), '03d')}"
        else:
            raise NotImplemented("Sorry I haven't coded this for the Eastern hemisphere yet!")

        geotiff_filename = f"{latitude_component}{longitude_component}.tiff"
        logging.debug(f"Geotiff Filename: {geotiff_filename}")
        return geotiff_filename

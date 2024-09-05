"""
This is the terrain model builder.  It builds models of real words terrain in the stl format

"""
import logging
import os
import math
from multiprocessing import cpu_count
from geopy import Point, distance
from enum import Enum
from .elevation_manager import ElevationManager
from .modeler import Modeler, ModelPoint
from random import choice
from numpy import array as nparray
from stl.mesh import Mesh
from multiprocessing import Process, Manager, cpu_count, Pool, set_start_method, Queue, Pool


class FlattenMode(Enum):
    BOTH = 1
    POSITIVE = 2
    NEGATIVE = 3


class XYZFileTypes(Enum):
    TYPE_A = 1
    TYPE_B = 2


class TerrainModler:
    def __init__(self,
                 latitude,
                 longitude,
                 longitude_size,
                 size_x,
                 size_y,
                 steps_x,
                 steps_y,
                 scale_z=1,
                 offset_elevation=0,
                 min_allowed_z=0,
                 flatten_reference_elevation_meters=0,
                 flatten_factor=1,
                 flatten_mode=None,
                 geotiff_folder=None,
                 xyz_config=None,
                 max_processes=(os.cpu_count() * 2)):
        '''
            This is the terrain model builder.  It builds models of real words terrain in the stl format

        :param latitude: latitude of the South West of the map
        :param longitude: longitude of the South West of the map
        :param longitude_size: size of the map in longitude as a decimal
        :param size_x: size of the map in x.  Technically unitless but usually mm.
        :param size_y: size of the map in y.  Technically unitless but usually mm.
        :param steps_x: number of steps in x direction
        :param steps_y: number of steps in y direction
        :param scale_z: factor by which to increase the scale in the z direction.
        :param offset_elevation: offset of the elevation in the map.  If you map is a long way above sea level or extends below sealevel you might need this
        :param min_allowed_z: minimum allowed z.  forces z to be a minimum thickness.
        :param flatten_reference_elevation_meters: flatten reference elevation in meters For the exponential squich you need a referance elevation.
                Usually sealeve or the "floor" or the map but it doesn't have to be.  This is the elevation that's slightly exagerated
        :param flatten_factor: flatten factor Te logrythmic factor to flatten by.  0.7 - 0.98 ish
        :param flatten_mode: flatten mode - Can be None, FlattenMode.POSITIVE (above the referance), FlattenMode.NEGATIVE (below the referance) or FlattenMode.BOTH.
        :param geotiff_folder: geotiff folder The folder where the geotiffs are stored.  See README.
        :param xyz_config: xyz config = The XYZ Config for NOOA XYZ files.
                {surface elevation: [file, file, file, ... ],
                 surface elevation: [file, file, file, ... ]
                 ...}
        :param max_processes: max processes The maxiumim number of processes to have running at a time.
        '''
        self.longitude_delta =  longitude_size / steps_x
        logging.debug(f"{longitude_size}/{steps_x} = {self.longitude_delta}")

        self.longitude_delta =  longitude_size / steps_x
        logging.debug(f"{longitude_size}/{steps_x} = {self.longitude_delta}")

        order_of_magnitude = -4 # math.floor(math.log(longitude_delta, 10))
        logging.debug(f"Order Of Magnitude: {order_of_magnitude}")


        self.steps_x = steps_x
        self.steps_y = steps_y
        self.size_x = size_x
        self.size_y = size_y
        self.xyz_config = xyz_config
        self.map_origin = Point(latitude, longitude)
        logging.debug(f"map_origin: {self.map_origin}")

        x_meters = distance.distance((latitude, longitude), (latitude, longitude + longitude_size)).meters
        logging.debug(f"y_meters: {x_meters}")

        self.scale_z = scale_z
        logging.debug(f"scale_z: {self.scale_z}")

        self.offset_elevation = offset_elevation
        logging.debug(f"offset_elevation: {self.offset_elevation}")

        self.min_allowed_z = min_allowed_z
        logging.debug(f"min_allowed_z: {self.min_allowed_z}")

        self.flatten_reference_elevation_meters = flatten_reference_elevation_meters
        logging.debug(f"flatten_reference_elevation_meters: {self.flatten_reference_elevation_meters}")

        self.flatten_factor = flatten_factor
        logging.debug(f"flatten_factor: {self.flatten_factor}")

        self.flatten_mode = flatten_mode
        logging.debug(f"flatten_mode: {self.flatten_mode}")

        self.x_step_meters = x_meters / steps_x
        logging.debug(f"x_step_meters: {self.x_step_meters}")

        self.meters_model_ratio = x_meters / size_x
        logging.debug(f"meters:model ratio: {self.meters_model_ratio}:1")

        y_meters = self.meters_model_ratio * size_y
        logging.debug(f"y_meters: {y_meters}")

        self.y_step_meters = y_meters / steps_y
        logging.debug(f"y_step_meters: {self.y_step_meters}")

        self.max_processes = max_processes
        logging.debug(f"max_processes: {self.max_processes}")
        map_farpoint = distance.distance(meters=y_meters).destination(distance.distance(meters=x_meters).destination(self.map_origin, bearing=90), bearing=0)

        self.latitude_delta =  (map_farpoint.latitude - self.map_origin.latitude) / steps_y
        logging.debug(f"{longitude_size}/{steps_x} = {self.longitude_delta}")


        self.elevation_manager = ElevationManager(geotiff_folder=geotiff_folder,
                                                  resolution=-order_of_magnitude,
                                                  xyz_config=xyz_config,
                                                  origin_point=self.map_origin,
                                                  far_point=map_farpoint)
        self.z_cache = Manager().dict()
        self.modeler = None

    def save_stl(self, filename):
        grid = self._build_grid()

        self.modeler = Modeler(size_x=self.size_x,
                               size_y=self.size_y,
                               steps_x=self.steps_x,
                               steps_y=self.steps_y,
                               model_points=grid)

        logging.info(f"Building Triangles")
        self.modeler.generate_triangles(max_processes=self.max_processes)

        logging.info(f"Building Faces")
        self.modeler.generate_faces()

        logging.info(f"Building Mesh")
        self.modeler.generate_mesh()

        logging.info(f"Saving File")
        self.modeler.save_stl(filename)

        logging.info(f"5m in z: {self._get_z_for_elevation(elevation=0)}")
        logging.info(f"6m in z: {self._get_z_for_elevation(elevation=1)}")

    def _build_grid(self):
        logging.info(f"Building Model Grid")
        with Pool(self.max_processes) as p:
            map_grid = p.map(self._build_map_line, range(0, self.steps_x + 1))
        logging.debug(f"map_grid: {map_grid}")

        override_grid = [[None] * (self.steps_y + 1) for i in range(0, self.steps_x + 1)]
        if self.xyz_config:
            maximum_delta = math.sqrt((self.x_step_meters * self.x_step_meters) + (self.y_step_meters * self.y_step_meters)) * 0.7
            override_points_to_expand = []
            for surface_elevation, files in self.xyz_config.items():
                logging.info(f"Processing surface_elevation {surface_elevation} files from {files}")
                for xyz_file in files:
                    with (open(xyz_file) as f):
                        file_format = None
                        for line in f.readlines():
                            if file_format is None:
                                if line.count(',') == 5 and line.count('\t') == 0:
                                    file_format = XYZFileTypes.TYPE_A
                                    logging.info(f"Found TypeA File")
                                elif line.count(',') == 0 and line.count('\t') == 3:
                                    file_format = XYZFileTypes.TYPE_B
                                    logging.info(f"Found TypeB File")
                                else:
                                    raise TypeError(f"File type of {xyz_file} is unknown. Pattern is: {line.count(',')}-{line.count('\t')}")
                            else:
                                if file_format == XYZFileTypes.TYPE_A:
                                    survey_id, latitude, longitude, depth, quality_code, active = line.split(',')
                                elif file_format == XYZFileTypes.TYPE_B:
                                    survey_id, longitude, latitude, depth = line.split('\t')
                                latitude = float(latitude)
                                longitude = float(longitude)
                                depth_meters = float(depth) / 3.28084  ## This is feet? ##TODO Confirm this!
                                y_guess = math.floor((latitude - self.map_origin.latitude) / self.latitude_delta)
                                x_guess = math.floor((longitude - self.map_origin.longitude) / self.longitude_delta)
                                for x_step in range(x_guess - 2, x_guess + 2):
                                    for y_step in range(y_guess - 2, y_guess + 2):
                                        map_point = Point(latitude=map_grid[x_step][y_step].latitude, longitude=map_grid[x_step][y_step].longitude)
                                        map_elevation = map_grid[x_step][y_step].altitude * 1000
                                        if abs(surface_elevation-map_elevation) < 1:
                                            delta_distance =  distance.geodesic(map_point, Point(latitude=latitude, longitude=longitude)).m
                                            if delta_distance < maximum_delta:
                                                logging.debug(f"FOUND: [{x_step},{y_step}] vs [{x_guess},{y_guess}]")
                                                if override_grid[x_step][y_step] is None:
                                                    override_grid[x_step][y_step] = (-depth_meters, delta_distance)
                                                    override_points_to_expand.append((x_step, y_step, surface_elevation, depth_meters))
                                                elif delta_distance < override_grid[x_step][y_step][1]:
                                                    override_grid[x_step][y_step] = (-depth_meters, delta_distance)
                                                elif depth_meters > abs(override_grid[x_step][y_step][0]):
                                                    override_grid[x_step][y_step] = (-depth_meters, delta_distance)

            logging.debug(f"override_grid: {override_grid}")
            while override_points_to_expand:
                logging.debug(f"override_points_to_expand: {len(override_points_to_expand)}")
                x_step, y_step, surface_elevation, depth_meters = override_points_to_expand.pop()
                neighbors = [(x_step - 1, y_step),
                             (x_step + 1, y_step),
                             (x_step, y_step - 1),
                             (x_step, y_step + 1)]
                logging.debug(f"[{x_step},{y_step}] = {neighbors}")
                for neighbor_x, neighbor_y in neighbors:
                    if override_grid[neighbor_x][neighbor_y] is None:
                        neighbor_elevation = map_grid[neighbor_x][neighbor_y].altitude * 1000
                        if abs(surface_elevation - neighbor_elevation) < 1:
                            override_grid[neighbor_x][neighbor_y] = (-depth_meters, None)
                            override_points_to_expand.append((neighbor_x, neighbor_y, surface_elevation, depth_meters))

        grid = []
        for x_step in range(0, self.steps_x + 1):
            grid.append([])
            for y_step in range(0, self.steps_y + 1):
                x, y = Modeler.get_model_x_y_for_steps(size_x=self.size_x, size_y=self.size_y,
                                                       x_step=x_step, y_step=y_step,
                                                       steps_x=self.steps_x, steps_y=self.steps_y)
                if override_grid[x_step][y_step] is None:
                    z = self._get_z_for_altitude(altitude=map_grid[x_step][y_step].altitude)
                else:
                    z = self._get_z_for_elevation(elevation=(map_grid[x_step][y_step].altitude * 1000) + override_grid[x_step][y_step][0])
                    logging.debug(f"Moving {x},{y} from {self._get_z_for_altitude(altitude=map_grid[x_step][y_step].altitude)} to {z}")
                model_point = ModelPoint(x, y, z)
                grid[x_step].append(model_point)
        return grid

    def _build_map_line(self, x_step):
        x_points = []
        for y_step in range(0, self.steps_y + 1):
            x, y = Modeler.get_model_x_y_for_steps(size_x=self.size_x, size_y=self.size_y,
                                                   x_step=x_step, y_step=y_step,
                                                   steps_x=self.steps_x, steps_y=self.steps_y)
            map_point = self._get_point_from_xy_steps(x_step=x_step, y_step=y_step)
            # z = self._get_z_for_altitude(altitude=map_point.altitude)
            # logging.debug(f"(x, y, z) = ({x}, {y}, {z}) = ({map_point.format_decimal(altitude='m')}")
            # model_point = ModelPoint(x, y, z)
            x_points.append(map_point)
        return x_points
    def _build_model_line(self, x_step):
        x_points = []
        for y_step in range(0, self.steps_y + 1):
            x, y = Modeler.get_model_x_y_for_steps(size_x=self.size_x, size_y=self.size_y,
                                                   x_step=x_step, y_step=y_step,
                                                   steps_x=self.steps_x, steps_y=self.steps_y)
            map_point = self._get_point_from_xy_steps(x_step=x_step, y_step=y_step)
            z = self._get_z_for_altitude(altitude=map_point.altitude)
            logging.debug(f"(x, y, z) = ({x}, {y}, {z}) = ({map_point.format_decimal(altitude='m')}")
            model_point = ModelPoint(x, y, z)
            x_points.append(model_point)
        return x_points
    def _get_z_for_altitude(self, altitude):
        # I do elevation in m.  Geopy does altitude in km.
        elevation = round((altitude * 1000), 2)
        return self._get_z_for_elevation(elevation=elevation)

    def _get_z_for_elevation(self, elevation):
        round_elecation = round(elevation, 2)
        logging.debug(f"Elevation: {round_elecation}")
        if round_elecation in self.z_cache:
            return self.z_cache[round_elecation]

        if (round_elecation < self.flatten_reference_elevation_meters
                and self.flatten_mode in [FlattenMode.BOTH, FlattenMode.NEGATIVE]):
            elevation_delta = self.flatten_reference_elevation_meters - round_elecation
            flattened_elevation_delta = math.pow(abs(elevation_delta), self.flatten_factor)
            adjusted_elevation = (self.flatten_reference_elevation_meters
                                  - flattened_elevation_delta
                                  - self.offset_elevation)
            logging.debug(
                f"Flatten Negative: {round_elecation} --> {adjusted_elevation} on {self.flatten_reference_elevation_meters} "
                f"and {elevation_delta} and {flattened_elevation_delta}")
        elif (round_elecation > self.flatten_reference_elevation_meters
              and self.flatten_mode in [FlattenMode.BOTH, FlattenMode.POSITIVE]):
            elevation_delta = round_elecation - self.flatten_reference_elevation_meters
            flattened_elevation_delta = math.pow(abs(elevation_delta), self.flatten_factor)
            adjusted_elevation = ((self.flatten_reference_elevation_meters + flattened_elevation_delta)
                                  - self.offset_elevation)
            logging.debug(
                f"Flatten Positive: {round_elecation} --> {adjusted_elevation} on {self.flatten_reference_elevation_meters} "
                f"and {elevation_delta} and {flattened_elevation_delta}")
        else:
            adjusted_elevation = round_elecation - self.offset_elevation

        z = round((adjusted_elevation / self.meters_model_ratio) * self.scale_z, 2)
        if self.min_allowed_z and z < self.min_allowed_z:
            logging.warning(f"Your point's final {z} is less then the allowed {self.min_allowed_z}, moving it up.")
            z = self.min_allowed_z

        if z < 0:
            z = 0
        logging.debug(f"z: {z}")
        return z

    def _get_point_from_xy_steps(self, x_step, y_step):
        return self._get_point_from_xy_meters(x_meters=(x_step * self.x_step_meters),
                                              y_meters=(y_step * self.y_step_meters))

    def _get_point_from_xy_meters(self, x_meters, y_meters):
        """
        _get_point_from_xy_meters - Get the Point for the location on the map, including elevation.

        :param y_meters: the number of meters north to go on the map from the origin point
        :param y_meters: the number of meters east to go on the map from the origin point

        :return: Point with the final location and elevation
        """
        endpoint_sealevel = distance.distance(meters=y_meters).destination(distance.distance(meters=x_meters).destination(self.map_origin, bearing=90), bearing=0)
        elevation = self.elevation_manager.get_elevation_for_latitude_longitude(latitude=endpoint_sealevel.latitude,
                                                                                longitude=endpoint_sealevel.longitude)
        endpoint = Point(latitude=endpoint_sealevel.latitude,
                         longitude=endpoint_sealevel.longitude,
                         altitude=Point.parse_altitude(distance=elevation, unit='m'))
        logging.debug(f"endpoint: {endpoint.format_decimal(altitude='m')}")
        return endpoint

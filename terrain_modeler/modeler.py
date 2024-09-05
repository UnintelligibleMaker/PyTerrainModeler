import logging
from ctypes import c_bool
from math import sqrt
from multiprocessing import Process, Manager, Pool

from numpy import array as nparray
from stl.mesh import Mesh


class ModelPoint(object):
    '''
    
    '''
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f"ModelPoint({self.x}, {self.y}, {self.z})"

    def is_on_floor(self):
        return self.z == 0

    def get_floor_copy(self):
        return ModelPoint(self.x, self.y, 0)


class Triangle(object):
    def __init__(self, a: ModelPoint, b: ModelPoint, c: ModelPoint):
        self.a = a
        self.b = b
        self.c = c

    def __str__(self):
        return f"Triangle({self.a}, {self.b}, {self.c})"

    def get_normal(self):
        logging.debug(self)
        v1 = Vector(self.a.x - self.b.x, self.a.y - self.b.y, self.a.z - self.b.z)
        logging.debug(f"v1: {v1}")
        v2 = Vector(self.a.x - self.c.x, self.a.y - self.c.y, self.a.z - self.c.z)
        logging.debug(f"v2: {v2}")
        c = Vector.cross_product(v1, v2)
        logging.debug(f"c: {c} = {c.get_magnitude()}")
        n = c.get_normalized()
        logging.debug(f"n: {n} = {n.get_magnitude()}")
        return n

    def is_on_floor(self):
        return self.a.is_on_floor() and self.b.is_on_floor() and self.c.is_on_floor()

    def get_face(self):
        return ([0, 0, 0],
                [[self.a.x, self.a.y, self.a.z],
                 [self.b.x, self.b.y, self.b.z],
                 [self.c.x, self.c.y, self.c.z]],
                [0])

    def get_floor_copy(self):
        return Triangle(self.a.get_floor_copy(), self.b.get_floor_copy(), self.c.get_floor_copy())


class Vector(object):
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f"Vector({self.x}, {self.y}, {self.z})"

    def get_magnitude(self):
        return sqrt((self.x * self.x) + (self.y * self.y) + (self.z * self.z))

    def get_normalized(self):
        return Vector(
            (self.x / self.get_magnitude()),
            (self.y / self.get_magnitude()),
            (self.z / self.get_magnitude()))

    @staticmethod
    def cross_product(v1, v2):
        c = Vector(v1.y * v2.z - v1.z * v2.y,
                   v1.z * v2.x - v1.x * v2.z,
                   v1.x * v2.y - v1.y * v2.x)
        logging.debug(f"c: {c}")
        return c

    @staticmethod
    def dot_product(v1, v2):
        d = (v1.x * v2.x) + (v1.y * v2.y) + (v1.z * v2.z)
        logging.debug(f"d : {d}")
        return d


class Modeler(object):
    def __init__(self, size_x, size_y, steps_x, steps_y, model_points):
        self.model_points = model_points

        self.triangles = None
        self.faces = None
        self.mesh = None

        self.size_x = size_x
        self.size_y = size_y
        self.steps_x = steps_x
        self.steps_y = steps_y
        self.x_step_size = size_x / steps_x
        logging.debug(f"x_step_size: {self.x_step_size}")

        self.y_step_size = size_y / steps_y
        logging.debug(f"y_step_size: {self.y_step_size}")

    def get_model_x_y_for_steps(self, x_step, y_step):
        x = round((x_step * self.x_step_size), 3)
        y = round((y_step * self.y_step_size), 3)
        return x, y

    @staticmethod
    def get_model_x_y_for_steps(size_x, size_y, x_step, y_step, steps_x, steps_y):
        x = round((x_step * size_x / steps_x), 3)
        y = round((y_step * size_y / steps_y), 3)
        return x, y
    def generate_triangles(self, max_processes=1):
        with Pool(max_processes) as p:
            self.triangles = p.map(self._generate_triangles_for_, range(-1, self.steps_x))


    def save_stl(self, filename):
        if self.mesh is None:
            self.generate_mesh()
        self.mesh.save(filename)

    def _generate_triangles_for_(self, index):
        if index == -1:
            triangles = self._generate_triangles_for_front_and_rear()
            triangles.extend(self._generate_triangles_for_left_and_rright())
            return triangles
        else:
            return self._generate_triangles_for_top_and_bottom_strip_x(index)

    def _generate_triangles_for_top_and_bottom_strip_x(self, x_step):
        logging.debug(f"Starting Triangles for x_step: {x_step}")
        triangles = []
        for y_step in range(0, self.steps_y):
            # With 4 points I am making 2 triangles.
            #            A                              B
            #       x,y______x+1, y               x,y______x+1, y
            #          |\   |                         |   /|
            #          | \  |           OR            |  / |
            #          |  \ |                         | /  |
            #          |   \|                         |/   |
            #   x, y+1 ______x + 1, y + 1       x, y+1 ______x+1, y+1
            # A1: (x, y), (next_x, y), (next_x, next_y)
            # A2: (x, y), (x, next_y), (next_x, next_y)
            # B1: (x, y), (next_x, y), (x, next_y)
            # B2: (next_x, next_y), (x, next_y), (next_x, y)
            # I want to choose the set with the largest angle furthest from 180 between them
            # See maths below.

            triangle_a_1 = Triangle(self.model_points[x_step][y_step],
                                    self.model_points[x_step + 1][y_step],
                                    self.model_points[x_step + 1][y_step + 1])
            logging.debug(triangle_a_1)

            triangle_a_2 = Triangle(self.model_points[x_step][y_step],
                                    self.model_points[x_step + 1][y_step + 1],
                                    self.model_points[x_step][y_step + 1])
            logging.debug(triangle_a_2)

            triangle_b_1 = Triangle(self.model_points[x_step][y_step],
                                    self.model_points[x_step + 1][y_step],
                                    self.model_points[x_step][y_step + 1])
            logging.debug(triangle_b_1)

            triangle_b_2 = Triangle(self.model_points[x_step + 1][y_step],
                                    self.model_points[x_step + 1][y_step + 1],
                                    self.model_points[x_step][y_step + 1])
            logging.debug(triangle_b_2)

            normal_vector_a_1 = triangle_a_1.get_normal()
            logging.debug(normal_vector_a_1)

            normal_vector_a_2 = triangle_a_2.get_normal()
            logging.debug(normal_vector_a_2)

            normal_vector_b_1 = triangle_b_1.get_normal()
            logging.debug(normal_vector_b_1)

            normal_vector_b_2 = triangle_b_2.get_normal()
            logging.debug(normal_vector_b_2)

            cos_theta_a = Vector.dot_product(normal_vector_a_1, normal_vector_a_2)
            logging.debug(f"cos_theta_a = {cos_theta_a}")

            cos_theta_b = Vector.dot_product(normal_vector_b_1, normal_vector_b_2)
            logging.debug(f"cos_theta_b = {cos_theta_b}")

            ## TODO: Is the abs right?  WIth the bug on triangle direction (in vs out) fixed I think
            ## The abs is not wrong and we want the less without it, but I'm not sure.  I need to run
            ## The tests agin here and see what looks better across them
            if abs(cos_theta_a) < abs(cos_theta_b):
                if not triangle_a_1.is_on_floor():
                    triangles.append(triangle_a_1)
                    triangles.append(triangle_a_1.get_floor_copy())
                if not triangle_a_2.is_on_floor():
                    triangles.append(triangle_a_2)
                    triangles.append(triangle_a_2.get_floor_copy())
            else:
                if not triangle_b_1.is_on_floor():
                    triangles.append(triangle_b_1)
                    triangles.append(triangle_b_1.get_floor_copy())
                if not triangle_b_2.is_on_floor():
                    triangles.append(triangle_b_2)
                    triangles.append(triangle_b_2.get_floor_copy())
        # triangles.extend(triangel_cache)
        logging.debug(f"Ending Triangles for x_step: {x_step}")
        return triangles

    def _generate_triangles_for_front_and_rear(self):
        logging.debug(f"Adding Front and Rear Triangles.")
        triangles = []
        for x_step in range(0, self.steps_x):
            if not self.model_points[x_step][0].z == 0:
                triangle_front_1 = Triangle(self.model_points[x_step][0].get_floor_copy(),
                                        self.model_points[x_step][0],
                                        self.model_points[x_step + 1][0].get_floor_copy())
                logging.debug(f"triangle_front_1: {triangle_front_1}")
                triangles.append(triangle_front_1)

            if not self.model_points[x_step + 1][0].z == 0:
                triangle_front_2 = Triangle(self.model_points[x_step][0],
                                        self.model_points[x_step + 1][0],
                                        self.model_points[x_step + 1][0].get_floor_copy())
                logging.debug(f"triangle_front_2: {triangle_front_2}")
                triangles.append(triangle_front_2)

            if not self.model_points[x_step][self.steps_y].z == 0:
                triangle_rear_1 = Triangle(self.model_points[x_step][self.steps_y],
                                        self.model_points[x_step][self.steps_y].get_floor_copy(),
                                        self.model_points[x_step + 1][self.steps_y].get_floor_copy())
                logging.debug(f"triangle_rear_1: {triangle_rear_1}")
                triangles.append(triangle_rear_1)

            if not self.model_points[x_step + 1][self.steps_y].z == 0:
                triangle_rear_2 = Triangle(self.model_points[x_step][self.steps_y],
                                            self.model_points[x_step + 1][self.steps_y].get_floor_copy(),
                                            self.model_points[x_step + 1][self.steps_y])
                logging.debug(f"triangle_front_2: {triangle_rear_2}")
                triangles.append(triangle_rear_2)
        return triangles

    def _generate_triangles_for_left_and_rright(self):
        logging.debug(f"Adding Front and Rear Triangles.")
        triangles = []
        for y_step in range(0, self.steps_y):
            if not self.model_points[self.steps_x][y_step].z == 0:
                triangle_right_1 = Triangle(self.model_points[self.steps_x][y_step].get_floor_copy(),
                                        self.model_points[self.steps_x][y_step],
                                        self.model_points[self.steps_x][y_step + 1].get_floor_copy())
                logging.debug(f"triangle_right_1: {triangle_right_1}")
                triangles.append(triangle_right_1)

            if not self.model_points[self.steps_x][y_step + 1].z == 0:
                triangle_right_2 = Triangle(self.model_points[self.steps_x][y_step],
                                        self.model_points[self.steps_x][y_step + 1],
                                        self.model_points[self.steps_x][y_step + 1].get_floor_copy())
                logging.debug(f"triangle_front_2: {triangle_right_2}")
                triangles.append(triangle_right_2)

            if not self.model_points[0][y_step].z == 0:
                triangle_left_1 = Triangle(self.model_points[0][y_step],
                                        self.model_points[0][y_step].get_floor_copy(),
                                        self.model_points[0][y_step + 1].get_floor_copy())
                logging.debug(f"triangle_rear_1: {triangle_left_1}")
                triangles.append(triangle_left_1)

            if not self.model_points[0][y_step].z == 0:
                triangle_left_2 = Triangle(self.model_points[0][y_step],
                                            self.model_points[0][y_step + 1].get_floor_copy(),
                                            self.model_points[0][y_step + 1])
                logging.debug(f"triangle_front_2: {triangle_left_2}")
                triangles.append(triangle_left_2)
        return triangles

    def generate_faces(self, max_processes=1):
        logging.info(f"Generating faces")
        with Pool(max_processes) as p:
            faces_groups = p.map(self._generate_faces, self.triangles)
        self.faces = []
        for faces in faces_groups:
            self.faces.extend(faces)


    def _generate_faces(self, triangles):
        faces = []
        for triangle in triangles:
            faces.append(triangle.get_face())
        return faces
    def generate_mesh(self):
        if len(self.faces) == 0:
            self.generate_faces()
        logging.info(f"Meshing.")
        array = nparray(self.faces, dtype=Mesh.dtype)
        self.mesh = Mesh(array)

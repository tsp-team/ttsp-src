from panda3d.core import Vec3, Point3

from .Line import Line
from . import PlaneClassification
from .Plane import Plane

class Polygon:

    def __init__(self, vertices, plane):
        self.vertices = vertices
        self.plane = plane

    @staticmethod
    def fromVertices(vertices):
        poly = Polygon(vertices, Plane.fromVertices(vertices[0], vertices[1], vertices[2]))
        poly.simplify()
        return poly

    @staticmethod
    def fromPlaneAndRadius(plane, radius = 10000):
        norm = plane.getNormal()
        point = plane.getPoint()
        direction = plane.getClosestAxisToNormal()
        tempV = -Vec3.unitY() if direction == Vec3.unitZ() else -Vec3.unitZ()
        up = tempV.cross(norm).normalized()
        right = norm.cross(up).normalized()

        verts = [
            point + right + up, # top right
            point - right + up, # top left
            point - right - up, # bottom left
            point + right - up, # bottom right

        ]

        poly = Polygon(verts, plane)
        poly.expand(radius)

        return poly

    def isValid(self):
        for vert in self.vertices:
            if self.plane.onPlane(vert) != 0:
                # Vert doesn't lie within the plane.
                return False

        return True

    def simplify(self):
        # Remove colinear vertices
        i = 0
        while 1:
            numVerts = len(self.vertices) - 2
            if i >= numVerts:
                break

            v1 = self.vertices[i]
            v2 = self.vertices[i + 2]
            p = self.vertices[i + 1]
            line = Line(v1, v2)
            # If the midpoint is on the line, remove it
            if line.closestPoint(p).almostEqual(p):
                del self.vertices[i + 1]

            i += 1

    def xform(self, mat):
        for i in range(len(self.vertices)):
            self.vertices[i] = mat.xformPoint(self.vertices[i])

        self.plane = Plane.fromVertices(self.vertices[0], self.vertices[1], self.vertices[2])

    def isConvex(self, epsilon = 0.001):
        for i in range(len(self.vertices)):
            v1 = self.vertices[i]
            v2 = self.vertices[(i + 1) % len(self.vertices)]
            v3 = self.vertices[(i + 2) % len(self.vertices)]
            l1 = (v1 - v2).normalized()
            l2 = (v3 - v2).normalized()
            cross = l1.cross(l2)
            if abs(self.plane.distToPlane(v2 + cross)) > epsilon:
                return False

        return True

    def getOrigin(self):
        origin = Vec3(0)
        for i in range(len(self.vertices)):
            origin += self.vertices[i]
        origin /= len(self.vertices)
        return origin

    def expand(self, radius):
        origin = self.getOrigin()
        for i in range(len(self.vertices)):
            self.vertices[i] = (self.vertices[i] - origin).normalized() * radius + origin
        self.plane = Plane.fromVertices(self.vertices[0], self.vertices[1], self.vertices[2])

    def classifyAgainstPlane(self, plane):
        front = 0
        back = 0
        onplane = 0
        count = len(self.vertices)

        for i in range(count):
            test = plane.onPlane(self.vertices[i])
            if test <= 0:
                back += 1
            if test >= 0:
                front += 1
            if test == 0:
                onplane += 1

        if onplane == count:
            return PlaneClassification.OnPlane
        if front == count:
            return PlaneClassification.Front
        if back == count:
            return PlaneClassification.Back

        return PlaneClassification.Spanning

    def splitInPlace(self, clipPlane):
        ret, _, back, _, _ = self.split(clipPlane)
        if ret:
            self.vertices = list(back.vertices)
            self.plane = Plane(back.plane)
        return ret

    def split(self, clipPlane):
        front = back = cBack = cFront = None

        classify = self.classifyAgainstPlane(clipPlane)
        if classify != PlaneClassification.Spanning:
            if classify == PlaneClassification.Back:
                back = self
            elif classify == PlaneClassification.Front:
                front = self
            elif self.plane.getNormal().dot(clipPlane.getNormal()) > 0:
                cFront = self
            else:
                cBack = self
            return [False, front, back, cBack, cFront]

        # Get the new front and back vertices
        backVerts = []
        frontVerts = []
        prev = 0

        for i in range(len(self.vertices) + 1):
            end = self.vertices[i % len(self.vertices)]
            cls = clipPlane.onPlane(end)

            # Check plane crossing
            if i > 0 and cls != 0 and prev != 0 and prev != cls:
                # This line end point has crossed the plane
                # Add the line intersect to the
                start = self.vertices[i - 1]

                isect = clipPlane.getIntersectionPoint(start, end, True)
                assert isect is not None

                frontVerts.append(isect)
                backVerts.append(isect)

            # Add original points
            if i < len(self.vertices):
                # Points on plane get put in both polygons, doesn't generate split
                if cls >= 0:
                    frontVerts.append(end)
                if cls <= 0:
                    backVerts.append(end)

            prev = int(cls)

        back = Polygon.fromVertices(backVerts)
        front = Polygon.fromVertices(frontVerts)
        cBack = cFront = None

        return [True, front, back, cBack, cFront]

    def flip(self):
        self.vertices.reverse()
        self.plane.flip()

from panda3d.core import Point3, Vec3, Quat, LineSegs

def snapToGrid(gridSize, point):
    result = Point3(point)
    for i in range(3):
        increments = int(round(result[i] / gridSize))
        result[i] = increments * gridSize

    return result

def makeForwardAxis(vec, quat):
    invQuat = Quat()
    invQuat.invertFrom(quat)
    result = invQuat.xform(vec)
    result.setY(0.0)
    return result

def zeroParallelAxis(vec, quat):
    axis = Vec3(1, 0, 1)
    axis = quat.xform(axis)

    return Vec3(vec[0] * axis[0],
                vec[1] * axis[1],
                vec[2] * axis[2])

def makeCubeOutline(mins, maxs, color, thickness = 1.0):
    lines = LineSegs()
    lines.setColor(color)
    lines.setThickness(thickness)
    lines.move_to( mins )
    lines.draw_to( Point3( mins.get_x(), mins.get_y(), maxs.get_z() ) )
    lines.draw_to( Point3( mins.get_x(), maxs.get_y(), maxs.get_z() ) )
    lines.draw_to( Point3( mins.get_x(), maxs.get_y(), mins.get_z() ) )
    lines.draw_to( mins )
    lines.draw_to( Point3( maxs.get_x(), mins.get_y(), mins.get_z() ) )
    lines.draw_to( Point3( maxs.get_x(), mins.get_y(), maxs.get_z() ) )
    lines.draw_to( Point3( mins.get_x(), mins.get_y(), maxs.get_z() ) )
    lines.move_to( Point3( maxs.get_x(), mins.get_y(), maxs.get_z() ) )
    lines.draw_to( maxs )
    lines.draw_to( Point3( mins.get_x(), maxs.get_y(), maxs.get_z() ) )
    lines.move_to( maxs )
    lines.draw_to( Point3( maxs.get_x(), maxs.get_y(), mins.get_z() ) )
    lines.draw_to( Point3( mins.get_x(), maxs.get_y(), mins.get_z() ) )
    lines.move_to( Point3( maxs.get_x(), maxs.get_y(), mins.get_z() ) )
    lines.draw_to( Point3( maxs.get_x(), mins.get_y(), mins.get_z() ) )
    return lines.create()

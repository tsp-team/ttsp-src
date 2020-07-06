from panda3d.core import Point3, Vec3, Quat, LineSegs, CKeyValues, ButtonRegistry

from direct.showbase.PythonUtil import invertDict

from src.coginvasion.globals import CIGlobals

from PyQt5 import QtGui, QtCore

# Qt key codes -> Panda KeyboardButton names.
QtKeyToKeyboardButton = {
    QtCore.Qt.Key_Space: "space",
    QtCore.Qt.Key_Backspace: "backspace",
    QtCore.Qt.Key_Tab: "tab",
    QtCore.Qt.Key_Return: "enter",
    QtCore.Qt.Key_Escape: "escape",
    QtCore.Qt.Key_Delete: "delete",

    QtCore.Qt.Key_F1: "f1",
    QtCore.Qt.Key_F2: "f2",
    QtCore.Qt.Key_F3: "f3",
    QtCore.Qt.Key_F4: "f4",
    QtCore.Qt.Key_F5: "f5",
    QtCore.Qt.Key_F6: "f6",
    QtCore.Qt.Key_F7: "f7",
    QtCore.Qt.Key_F8: "f8",
    QtCore.Qt.Key_F9: "f9",
    QtCore.Qt.Key_F10: "f10",
    QtCore.Qt.Key_F11: "f11",
    QtCore.Qt.Key_F12: "f12",
    QtCore.Qt.Key_F13: "f13",
    QtCore.Qt.Key_F14: "f14",
    QtCore.Qt.Key_F15: "f15",
    QtCore.Qt.Key_F16: "f16",

    QtCore.Qt.Key_Left: "arrow_left",
    QtCore.Qt.Key_Right: "arrow_right",
    QtCore.Qt.Key_Up: "arrow_up",
    QtCore.Qt.Key_Down: "arrow_down",
    QtCore.Qt.Key_PageDown: "page_down",
    QtCore.Qt.Key_PageUp: "page_up",
    QtCore.Qt.Key_Home: "home",
    QtCore.Qt.Key_End: "end",
    QtCore.Qt.Key_Insert: "insert",
    QtCore.Qt.Key_Help: "help",

    QtCore.Qt.Key_Shift: "shift",
    QtCore.Qt.Key_Control: "control",
    QtCore.Qt.Key_Alt: "alt",
    QtCore.Qt.Key_Meta: "meta",
    QtCore.Qt.Key_CapsLock: "caps_lock",
    QtCore.Qt.Key_NumLock: "num_lock",
    QtCore.Qt.Key_ScrollLock: "scroll_lock",
    QtCore.Qt.Key_Pause: "pause",
    QtCore.Qt.Key_Menu: "menu",
}

KeyboardButtonToQtKey = invertDict(QtKeyToKeyboardButton)

def keyboardButtonFromQtKey(keycode):
    reg = ButtonRegistry.ptr()

    # First try the ascii value
    asciiValue = keycode
    if asciiValue < 256:
        button = reg.findAsciiButton(chr(asciiValue))
    else:
        # Don't have a valid ascii value for this key.
        # Look up the KeyboardButton name by the key code.
        buttonName = QtKeyToKeyboardButton.get(asciiValue)
        button = reg.findButton(buttonName)
    return button

def qtKeyFromKeyboardButton(name):
    if len(name) == 1:
        # A single character.. this must be an ascii key
        return ord(name)
    else:
        return KeyboardButtonToQtKey.get(name)

def strToQColor(colorStr, alpha = False):
    pcolor = CKeyValues.to4f(colorStr)
    return QtGui.QColor(int(pcolor.x), int(pcolor.y), int(pcolor.z), 255 if not alpha else int(pcolor.w))

def qColorToStr(qcolor):
    return "%i %i %i %i" % (qcolor.red(), qcolor.green(), qcolor.blue(), qcolor.alpha())

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

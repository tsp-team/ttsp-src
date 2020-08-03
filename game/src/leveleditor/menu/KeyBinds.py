from .KeyBindDef import KeyBindDef
from .KeyBind import KeyBind

KeyBinds = [
    KeyBindDef("Create a new map", KeyBind.FileNew, "ctrl+n"),
    KeyBindDef("Open a map", KeyBind.FileOpen, "ctrl+o"),
    KeyBindDef("Save the map", KeyBind.FileSave, "ctrl+s"),
    KeyBindDef("Save the map as", KeyBind.FileSaveAs, "ctrl+shift+s"),
    KeyBindDef("Close the map", KeyBind.FileClose, "ctrl+x"),

    KeyBindDef("Undo previous action", KeyBind.Undo, "ctrl+z"),
    KeyBindDef("Redo previous action", KeyBind.Redo, "ctrl+shift+z"),

    KeyBindDef("Delete object(s)", KeyBind.Delete, "delete"),
    KeyBindDef("Copy object(s)", KeyBind.Copy, "ctrl+c"),
    KeyBindDef("Paste object(s)", KeyBind.Paste, "ctrl+v"),
    KeyBindDef("Select object", KeyBind.Select, "mouse1"),
    KeyBindDef("Select multiple objects", KeyBind.SelectMultiple, "shift"),

    KeyBindDef("Increase grid size", KeyBind.IncGridSize, "]"),
    KeyBindDef("Decrease grid size", KeyBind.DecGridSize, "["),
    KeyBindDef("Toggle 2D grid", KeyBind.Toggle2DGrid, "shift+g"),
    KeyBindDef("Toggle 3D grid", KeyBind.Toggle3DGrid, "shift+h"),
    KeyBindDef("Toggle grid snap", KeyBind.ToggleGridSnap, "shift+j"),

    KeyBindDef("Switch to select tool", KeyBind.SelectTool, "shift+s"),
    KeyBindDef("Switch to move tool", KeyBind.MoveTool, "shift+m"),
    KeyBindDef("Switch to rotate tool", KeyBind.RotateTool, "shift+r"),
    KeyBindDef("Switch to scale tool", KeyBind.ScaleTool, "shift+q"),
    KeyBindDef("Switch to entity tool", KeyBind.EntityTool, "shift+e"),
    KeyBindDef("Switch to block tool", KeyBind.BlockTool, "shift+b"),
    KeyBindDef("Switch to clipping tool", KeyBind.ClipTool, "shift+x"),

    KeyBindDef("Select mode - groups", KeyBind.SelectGroups, "ctrl+shift+g"),
    KeyBindDef("Select mode - faces", KeyBind.SelectFaces, "ctrl+shift+f"),
    KeyBindDef("Select mode - objects", KeyBind.SelectObjects, "ctrl+shift+o"),
    KeyBindDef("Select mode - vertices", KeyBind.SelectVertices, "ctrl+shift+v"),

    KeyBindDef("Confirm action", KeyBind.ConfirmAction, "enter"),
    KeyBindDef("Cancel action", KeyBind.CancelAction, "escape"),

    KeyBindDef("Toggle 3D mouse look", KeyBind.FlyCam, "z"),

    KeyBindDef("2D view - pan camera", KeyBind.Pan2DView, "mouse2"),
    KeyBindDef("Zoom in", KeyBind.ZoomIn, "wheel_up"),
    KeyBindDef("Zoom out", KeyBind.ZoomOut, "wheel_down"),

    KeyBindDef("3D view - move forward", KeyBind.Forward3DView, "w"),
    KeyBindDef("3D view - move back", KeyBind.Back3DView, "s"),
    KeyBindDef("3D view - move left", KeyBind.Left3DView, "a"),
    KeyBindDef("3D view - move right", KeyBind.Right3DView, "d"),
    KeyBindDef("3D view - move up", KeyBind.Up3DView, "q"),
    KeyBindDef("3D view - move down", KeyBind.Down3DView, "e"),
    KeyBindDef("3D view - look up", KeyBind.LookUp3DView, "arrow_up"),
    KeyBindDef("3D view - look down", KeyBind.LookDown3DView, "arrow_down"),
    KeyBindDef("3D view - look left", KeyBind.LookLeft3DView, "arrow_left"),
    KeyBindDef("3D view - look right", KeyBind.LookRight3DView, "arrow_right"),

    KeyBindDef("Switch to next document", KeyBind.NextDocument, "tab"),
    KeyBindDef("Switch to previous document", KeyBind.PrevDocument, "shift+tab")
]

KeyBindsByID = {x.id: x for x in KeyBinds}

def getShortcut(id):
    return KeyBindsByID[id].shortcut

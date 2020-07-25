from .CreateEditDelete import CreateEditDelete

class Clip(CreateEditDelete):

    def __init__(self, solids, plane, keepFront, keepBack):
        CreateEditDelete.__init__(self)
        self.solids = solids
        self.plane = plane
        self.keepFront = keepFront
        self.keepBack = keepBack
        self.firstRun = True

    def cleanup(self):
        self.solids = None
        self.plane = None
        self.keepBack = None
        self.keepFront = None
        self.firstRun = None

    def do(self):
        if self.firstRun:
            self.firstRun = False

            for solid in self.solids:
                ret, back, front = solid.split(self.plane, base.document.idGenerator)
                if not ret:
                    continue
                if solid.selected:
                    base.selectionMgr.select(back)
                    base.selectionMgr.select(front)
                back.stash()
                front.stash()
                if self.keepBack:
                    self.create(back)
                if self.keepFront:
                    self.create(front)

                self.delete(solid)

        CreateEditDelete.do(self)

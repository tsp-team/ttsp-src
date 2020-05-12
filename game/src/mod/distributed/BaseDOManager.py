from panda3d.direct import DCFile
from panda3d.core import getModelPath, Filename

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DoInterestManager import DoInterestManager
from direct.distributed.DoCollectionManager import DoCollectionManager

import inspect

class BaseDOManager(DoInterestManager, DoCollectionManager):
    """
    Base class for anything that needs to use/manage DistributedObjects
    and read from DC files.
    """
    notify = directNotify.newCategory("BaseDOManager")

    def __init__(self, hasOwnerView = False):
        self._hasOwnerView = hasOwnerView
        self.dcFile = DCFile()
        self.dcSuffix = ''

        self.dclassesByName = None
        self.dclassesByNumber = None
        self.hashVal = None

        DoInterestManager.__init__(self)
        DoCollectionManager.__init__(self)

        self.uniqueId = hash(self)

    def uniqueName(self, idString):
        return ("%s-%s" % (idString, self.uniqueId))

    def hasOwnerView(self):
        return self._hasOwnerView

    def getDcFile(self):
        return self.dcFile

    def readDCFile(self, dcFileNames = None):
        """
        Reads in the dc files listed in dcFileNames, or if
        dcFileNames is None, reads in all of the dc files listed in
        the Config.prc file.
        """

        dcFile = self.getDcFile()
        dcFile.clear()
        self.dclassesByName = {}
        self.dclassesByNumber = {}
        self.hashVal = 0

        if isinstance(dcFileNames, str):
            # If we were given a single string, make it a list.
            dcFileNames = [dcFileNames]

        dcImports = {}
        if dcFileNames == None:
            readResult = dcFile.readAll()
            if not readResult:
                self.notify.error("Could not read dc file.")
        else:
            searchPath = getModelPath().getValue()
            for dcFileName in dcFileNames:
                pathname = Filename(dcFileName)
                vfs.resolveFilename(pathname, searchPath)
                readResult = dcFile.read(pathname)
                if not readResult:
                    self.notify.error("Could not read dc file: %s" % (pathname))

        self.hashVal = dcFile.getHash()

        # Now import all of the modules required by the DC file.
        for n in range(dcFile.getNumImportModules()):
            moduleName = dcFile.getImportModule(n)[:]

            # Maybe the module name is represented as "moduleName/AI".
            suffix = moduleName.split('/')
            moduleName = suffix[0]
            suffix=suffix[1:]
            if self.dcSuffix in suffix:
                moduleName += self.dcSuffix
            elif self.dcSuffix == 'UD' and 'AI' in suffix: #HACK:
                moduleName += 'AI'

            importSymbols = []
            for i in range(dcFile.getNumImportSymbols(n)):
                symbolName = dcFile.getImportSymbol(n, i)

                # Maybe the symbol name is represented as "symbolName/AI".
                suffix = symbolName.split('/')
                symbolName = suffix[0]
                suffix=suffix[1:]
                if self.dcSuffix in suffix:
                    symbolName += self.dcSuffix
                elif self.dcSuffix == 'UD' and 'AI' in suffix: #HACK:
                    symbolName += 'AI'

                importSymbols.append(symbolName)

            self.importModule(dcImports, moduleName, importSymbols)

        # Now get the class definition for the classes named in the DC
        # file.
        for i in range(dcFile.getNumClasses()):
            dclass = dcFile.getClass(i)
            number = dclass.getNumber()
            className = dclass.getName() + self.dcSuffix

            # Does the class have a definition defined in the newly
            # imported namespace?
            classDef = dcImports.get(className)
            if classDef is None and self.dcSuffix == 'UD': #HACK:
                className = dclass.getName() + 'AI'
                classDef = dcImports.get(className)

            # Also try it without the dcSuffix.
            if classDef == None:
                className = dclass.getName()
                classDef = dcImports.get(className)
            if classDef is None:
                self.notify.debug("No class definition for %s." % (className))
            else:
                if inspect.ismodule(classDef):
                    if not hasattr(classDef, className):
                        self.notify.warning("Module %s does not define class %s." % (className, className))
                        continue
                    classDef = getattr(classDef, className)

                if not inspect.isclass(classDef):
                    self.notify.error("Symbol %s is not a class name." % (className))
                else:
                    dclass.setClassDef(classDef)

            self.dclassesByName[className] = dclass
            if number >= 0:
                self.dclassesByNumber[number] = dclass

        # Owner Views
        if self.hasOwnerView():
            ownerDcSuffix = self.dcSuffix + 'OV'
            # dict of class names (without 'OV') that have owner views
            ownerImportSymbols = {}

            # Now import all of the modules required by the DC file.
            for n in range(dcFile.getNumImportModules()):
                moduleName = dcFile.getImportModule(n)

                # Maybe the module name is represented as "moduleName/AI".
                suffix = moduleName.split('/')
                moduleName = suffix[0]
                suffix=suffix[1:]
                if ownerDcSuffix in suffix:
                    moduleName = moduleName + ownerDcSuffix

                importSymbols = []
                for i in range(dcFile.getNumImportSymbols(n)):
                    symbolName = dcFile.getImportSymbol(n, i)

                    # Check for the OV suffix
                    suffix = symbolName.split('/')
                    symbolName = suffix[0]
                    suffix=suffix[1:]
                    if ownerDcSuffix in suffix:
                        symbolName += ownerDcSuffix
                    importSymbols.append(symbolName)
                    ownerImportSymbols[symbolName] = None

                self.importModule(dcImports, moduleName, importSymbols)

            # Now get the class definition for the owner classes named
            # in the DC file.
            for i in range(dcFile.getNumClasses()):
                dclass = dcFile.getClass(i)
                if ((dclass.getName()+ownerDcSuffix) in ownerImportSymbols):
                    number = dclass.getNumber()
                    className = dclass.getName() + ownerDcSuffix

                    # Does the class have a definition defined in the newly
                    # imported namespace?
                    classDef = dcImports.get(className)
                    if classDef is None:
                        self.notify.error("No class definition for %s." % className)
                    else:
                        if inspect.ismodule(classDef):
                            if not hasattr(classDef, className):
                                self.notify.error("Module %s does not define class %s." % (className, className))
                            classDef = getattr(classDef, className)
                        dclass.setOwnerClassDef(classDef)
                        self.dclassesByName[className] = dclass

    def importModule(self, dcImports, moduleName, importSymbols):
        """
        Imports the indicated moduleName and all of its symbols
        into the current namespace.  This more-or-less reimplements
        the Python import command.
        """
        module = __import__(moduleName, globals(), locals(), importSymbols)

        if importSymbols:
            # "from moduleName import symbolName, symbolName, ..."
            # Copy just the named symbols into the dictionary.
            if importSymbols == ['*']:
                # "from moduleName import *"
                if hasattr(module, "__all__"):
                    importSymbols = module.__all__
                else:
                    importSymbols = module.__dict__.keys()

            for symbolName in importSymbols:
                if hasattr(module, symbolName):
                    dcImports[symbolName] = getattr(module, symbolName)
                else:
                    raise Exception('Symbol %s not defined in module %s.' % (symbolName, moduleName))
        else:
            # "import moduleName"

            # Copy the root module name into the dictionary.

            # Follow the dotted chain down to the actual module.
            components = moduleName.split('.')
            dcImports[components[0]] = module

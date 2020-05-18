from direct.interval.IntervalGlobal import Sequence, SoundInterval

class VOX:

    def __init__(self):
        self.speechTrack = None

        # Name -> AudioSound
        self.words = {}

    def load(self, voxDir, extension = "wav"):
        wordList = vfs.scanDirectory(voxDir)
        if not wordList:
            print("VOX: No vox in", voxDir)
            return

        for vFile in wordList.getFiles():
            fn = vFile.getFilename()
            if fn.getExtension() == extension:
                self.words[fn.getBasenameWoExtension().lower()] = loader.loadSfx(fn.getFullpath())

    def stopSpeech(self):
        if self.speechTrack:
            self.speechTrack.finish()
        self.speechTrack = None

    def say(self, sentence, volume = 0.5):
        self.stopSpeech()

        words = sentence.split(" ")
        self.speechTrack = Sequence()
        for i in range(len(words)):
            word = words[i].lower()

            if word == ",":
                word = "_comma"
            elif word == ".":
                word = "_period"

            if word in self.words:
                self.speechTrack.append(SoundInterval(self.words[word], volume = volume))

        self.speechTrack.start()

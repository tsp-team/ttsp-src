from direct.directnotify.DirectNotifyGlobal import directNotify

from src.coginvasion.base import MusicCache

import random

class Jukebox:
    
    notify = directNotify.newCategory("Jukebox")
    
    def __init__(self):
        self.songList = []
        self.currentSong = 0
        self.currentSongDur = 0.0
        
    def hasNextSong(self):
        return self.currentSong < (len(self.songList) - 1)
        
    def shuffle(self):
        #self.songList = list(MusicCache.Cache.keys())
        self.songList = ["mod_cog_battle",
                         "mod_cog_hq_battle",
                         "mod_cog_bldg_indoor",
                         "mod_cog_bldg_final",
                         "mod_cog_lb_jury",
                         "mod_cog_bb_v1",
                         "mod_cog_bb_v2",
                         "mod_cog_boss"]
        self.currentSong = 0
        random.shuffle(self.songList)
        
        self.notify.info("Song list: {0}".format(self.songList))
        
    def fadeOut(self):
        base.fadeOutMusic()
        taskMgr.remove("Jukebox.playSongDone")
        
    def play(self):
        songName = self.songList[self.currentSong]
        song = base.playMusic(songName, False)
        self.currentSongDur = song.length()
        
        self.notify.info("Playing {0}".format(songName))
        
        taskMgr.doMethodLater(self.currentSongDur + 1.0, self.__playSongDone, "Jukebox.playSongDone")
        
    def __playSongDone(self, task):
        self.next()
        return task.done
        
    def next(self):
        if self.hasNextSong():
            self.currentSong += 1
            self.play()
        else:
            self.shuffle()
            self.play()

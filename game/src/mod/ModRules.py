from src.coginvasion.battle.GameRules import GameRules

class ModRules(GameRules):

    def useBackpack(self):
        return False
        
    def onPlayerDied(self):
        pass
        
    def onPlayerRespawn(self):
        base.beginGame()

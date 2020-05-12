from src.coginvasion.battle.GameRulesAI import GameRulesAI

class ModRulesAI(GameRulesAI):

    def useBackpack(self):
        return False
        
    def countsTowardsQuests(self):
        return False
        
    def givesExperience(self):
        return False
        
    def respawnPlayer(self, player):

        from src.coginvasion.attack.Attacks import ATTACK_HL2PISTOL, ATTACK_GUMBALLBLASTER, ATTACK_GAG_WHOLECREAMPIE, ATTACK_GAG_TNT, ATTACK_HL2PISTOL, ATTACK_HL2SHOTGUN, ATTACK_SOUND, ATTACK_GAG_FIREHOSE
        player.b_setAttackIds([ATTACK_GAG_TNT, ATTACK_GAG_WHOLECREAMPIE, ATTACK_GUMBALLBLASTER, ATTACK_HL2PISTOL, ATTACK_HL2SHOTGUN, ATTACK_SOUND, ATTACK_GAG_FIREHOSE])
        #player.b_setAttackIds([ATTACK_GAG_WHOLECREAMPIE])
        #from src.coginvasion.attack.Attacks import ATTACK_SLAP, ATTACK_SOUND
        #player.b_setAttackIds([ATTACK_SLAP])
        player.b_setMaxHealth(100)
        player.b_setHealth(100)
        #player.b_setAttackIds([])
        
        import random
        spawns = self.battleZone.bspLoader.findAllEntities("info_player_start")
        spawn = random.choice(spawns)
        spawn.putPlayerAtSpawn(player)
        
        self.battleZone.sendUpdateToAvatarId(player.doId, 'respawn', [])

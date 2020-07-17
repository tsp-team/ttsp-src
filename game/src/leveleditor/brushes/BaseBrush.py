class BaseBrush:
    Name = "Brush"
    CanRound = True

    def create(self, box, material, roundDecimals):
        raise NotImplementedError

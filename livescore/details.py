class Alliance:
    def __init__(self, score=None, teams=[]):
        self.score = score
        self.teams = teams


class OngoingMatchDetails:
    def __init__(self, match=None, time=None, red=Alliance(), blue=Alliance()):
        self.match = match
        self.time = time
        self.red = red
        self.blue = blue

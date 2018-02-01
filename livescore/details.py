class Alliance:
    def __init__(self, score=None, teams=[], fuel_score=None, fuel_count=None):
        self.teams = teams
        self.score = score
        self.fuel_score = fuel_score
        self.fuel_count = fuel_count


class OngoingMatchDetails:
    def __init__(self, match=None, time=None, red=Alliance(), blue=Alliance()):
        self.match = match
        self.time = time
        self.red = red
        self.blue = blue

class Alliance(object):
    def __init__(self, score=None, teams=[]):
        self.teams = teams
        self.score = score


class Alliance2017(Alliance):
    def __init__(self, score=None, teams=[], fuel_score=None, fuel_count=None, rotor_count=None, touchpad_count=None):
        super(Alliance2017, self).__init__(score=score, teams=teams)
        self.fuel_score = fuel_score
        self.fuel_count = fuel_count
        self.rotor_count = rotor_count
        self.touchpad_count = touchpad_count


class OngoingMatchDetails(object):
    def __init__(self, match=None, mode=None, time=None, red=Alliance(), blue=Alliance()):
        self.match = match
        self.mode = mode
        self.time = time
        self.red = red
        self.blue = blue

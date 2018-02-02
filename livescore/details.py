class Alliance:
    def __init__(self, score=None, teams=[], fuel_score=None, fuel_count=None, rotor_count=None, touchpad_count=None):
        self.teams = teams
        self.score = score
        self.fuel_score = fuel_score
        self.fuel_count = fuel_count
        self.rotor_count = rotor_count
        self.touchpad_count = touchpad_count


class OngoingMatchDetails:
    def __init__(self, match=None, mode=None, time=None, red=Alliance(), blue=Alliance()):
        self.match = match
        self.mode = mode
        self.time = time
        self.red = red
        self.blue = blue

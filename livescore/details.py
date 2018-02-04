class Alliance(object):
    def __init__(self, score=None, teams=[]):
        self.teams = teams
        self.score = score


class Alliance2017(Alliance):
    def __init__(
            self,
            score=None,
            teams=[],
            fuel_score=None,
            fuel_count=None,
            rotor_count=None,
            touchpad_count=None):
        super(Alliance2017, self).__init__(score=score, teams=teams)
        self.fuel_score = fuel_score
        self.fuel_count = fuel_count
        self.rotor_count = rotor_count
        self.touchpad_count = touchpad_count


class Alliance2018(Alliance):
    def __init__(
            self,
            score=None,
            teams=[],
            boost_count=None,
            boost_played=None,
            force_count=None,
            force_played=None,
            levitate_count=None,
            levitate_played=None,
            switch_owned=None,
            scale_owned=None,
            current_powerup=None,
            powerup_time_remaining=None,
        ):
        super(Alliance2018, self).__init__(score=score, teams=teams)
        self.boost_count = boost_count
        self.boost_played = boost_played
        self.force_count = force_count
        self.force_played = force_played
        self.levitate_count = levitate_count
        self.levitate_played = levitate_played
        self.switch_owned = switch_owned
        self.scale_owned = scale_owned
        self.current_powerup = current_powerup
        self.powerup_time_remaining = powerup_time_remaining

class OngoingMatchDetails(object):
    def __init__(self, match=None, mode=None, time=None, red=Alliance(), blue=Alliance()):
        self.match = match
        self.mode = mode
        self.time = time
        self.red = red
        self.blue = blue

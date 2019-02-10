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

    def getString(self, prefix):
        return (
            '{} score: {}\n'.format(prefix, self.score) + \
            '{} fuel_score: {}\n'.format(prefix, self.fuel_score) + \
            '{} fuel_count: {}\n'.format(prefix, self.fuel_count) + \
            '{} rotor_count: {}\n'.format(prefix, self.rotor_count) + \
            '{} touchpad_count: {}\n'.format(prefix, self.touchpad_count)
        )

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
            auto_quest=None,
            face_the_boss=None,
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
        self.auto_quest = auto_quest
        self.face_the_boss = face_the_boss

    def getString(self, prefix):
        return (
            '{} score: {}\n'.format(prefix, self.score) + \
            '{} force_count: {}\n'.format(prefix, self.force_count) + \
            '{} force_played: {}\n'.format(prefix, self.force_played) + \
            '{} levitate_count: {}\n'.format(prefix, self.levitate_count) + \
            '{} levitate_played: {}\n'.format(prefix, self.levitate_played) + \
            '{} boost_count: {}\n'.format(prefix, self.boost_count) + \
            '{} boost_played: {}\n'.format(prefix, self.boost_played) + \
            '{} switch_owned: {}\n'.format(prefix, self.switch_owned) + \
            '{} scale_owned: {}\n'.format(prefix, self.scale_owned) + \
            '{} current_powerup: {}\n'.format(prefix, self.current_powerup) + \
            '{} powerup_time_remaining: {}\n'.format(prefix, self.powerup_time_remaining) + \
            '{} auto_quest: {}\n'.format(prefix, self.auto_quest) + \
            '{} face_the_boss: {}\n'.format(prefix, self.face_the_boss)
        )

class Alliance2019(Alliance):
    def __init__(
            self,
            score=None,
            teams=[],
            robot1_starting_level=None,
            robot1_hab_line_cross=None,
            robot1_ending_level=None,
            robot2_starting_level=None,
            robot2_hab_line_cross=None,
            robot2_ending_level=None,
            robot3_starting_level=None,
            robot3_hab_line_cross=None,
            robot3_ending_level=None,
            cargo_ship_hatch_count=None,
            cargo_ship_cargo_count=None,
            rocket1_hatch_count=None,
            rocket1_cargo_count=None,
            rocket2_hatch_count=None,
            rocket2_cargo_count=None,
            rocket_rp=None,
            hab_rp=None,
        ):
        super(Alliance2019, self).__init__(score=score, teams=teams)
        self.robot1_starting_level = robot1_starting_level
        self.robot1_starting_level = robot1_starting_level
        self.robot1_hab_line_cross = robot1_hab_line_cross
        self.robot1_ending_level = robot1_ending_level
        self.robot2_starting_level = robot2_starting_level
        self.robot2_hab_line_cross = robot2_hab_line_cross
        self.robot2_ending_level = robot2_ending_level
        self.robot3_starting_level = robot3_starting_level
        self.robot3_hab_line_cross = robot3_hab_line_cross
        self.robot3_ending_level = robot3_ending_level
        self.cargo_ship_hatch_count = cargo_ship_hatch_count
        self.cargo_ship_cargo_count = cargo_ship_cargo_count
        self.rocket1_hatch_count = rocket1_hatch_count
        self.rocket1_cargo_count = rocket1_cargo_count
        self.rocket2_hatch_count = rocket2_hatch_count
        self.rocket2_cargo_count = rocket2_cargo_count
        self.rocket_rp = rocket_rp
        self.hab_rp = hab_rp

    def getString(self, prefix):
        return (
            '{} score: {}\n'.format(prefix, self.score) + \
            '{} robot1_starting_level: {}\n'.format(prefix, self.robot1_starting_level) + \
            '{} robot1_starting_level: {}\n'.format(prefix, self.robot1_starting_level) + \
            '{} robot1_hab_line_cross: {}\n'.format(prefix, self.robot1_hab_line_cross) + \
            '{} robot1_ending_level: {}\n'.format(prefix, self.robot1_ending_level) + \
            '{} robot2_starting_level: {}\n'.format(prefix, self.robot2_starting_level) + \
            '{} robot2_hab_line_cross: {}\n'.format(prefix, self.robot2_hab_line_cross) + \
            '{} robot2_ending_level: {}\n'.format(prefix, self.robot2_ending_level) + \
            '{} robot3_starting_level: {}\n'.format(prefix, self.robot3_starting_level) + \
            '{} robot3_hab_line_cross: {}\n'.format(prefix, self.robot3_hab_line_cross) + \
            '{} robot3_ending_level: {}\n'.format(prefix, self.robot3_ending_level) + \
            '{} cargo_ship_hatch_count: {}\n'.format(prefix, self.cargo_ship_hatch_count) + \
            '{} cargo_ship_cargo_count: {}\n'.format(prefix, self.cargo_ship_cargo_count) + \
            '{} rocket1_hatch_count: {}\n'.format(prefix, self.rocket1_hatch_count) + \
            '{} rocket1_cargo_count: {}\n'.format(prefix, self.rocket1_cargo_count) + \
            '{} rocket2_hatch_count: {}\n'.format(prefix, self.rocket2_hatch_count) + \
            '{} rocket2_cargo_count: {}\n'.format(prefix, self.rocket2_cargo_count) + \
            '{} rocket_rp: {}\n'.format(prefix, self.rocket_rp) + \
            '{} hab_rp: {}\n'.format(prefix, self.hab_rp)
        )

class OngoingMatchDetails(object):
    def __init__(self, match_key=None, match_name=None, mode=None, time=None, red=Alliance(), blue=Alliance()):
        self.match_key = match_key
        self.match_name = match_name
        self.mode = mode
        self.time = time
        self.red = red
        self.blue = blue

    def __str__(self):

        return 'Match Key: {}\nMatch Name: {}\nMode: {}\nTime remaining: {}\n{}{}'.format(
            self.match_key, self.match_name, self.mode, self.time, self.red.getString('Red'), self.blue.getString('Blue'))

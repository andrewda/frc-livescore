import colorsys
import cv2
import numpy as np
from PIL import Image
import pkg_resources
import pytesseract
import re

from LivescoreBase import LivescoreBase
from details import Alliance2018, OngoingMatchDetails


class Livescore2018(LivescoreBase):
    def __init__(self, **kwargs):
        super(Livescore2018, self).__init__(2018, **kwargs)
        self._match_name = None

        # Power up templates
        template_path = pkg_resources.resource_filename(__name__, 'templates')
        self._templates = {
            'boost': cv2.imread(template_path + '/2018_boost.png'),
            'force': cv2.imread(template_path + '/2018_force.png'),
            'levitate': cv2.imread(template_path + '/2018_levitate.png'),
        }

    def _getMatchName(self, img, debug_img):
        if self._match_name is None:
            tl = self._transformPoint((186, 164))
            br = self._transformPoint((622, 196))

            config = '--psm 7'
            long_match = pytesseract.image_to_string(
                Image.fromarray(self._getImgCropThresh(img, tl, br)), config=config).strip()

            m = re.search('([a-zA-z]+) ([1-9]+)( of ...?)?', long_match)
            if m is not None:
                self._match_name = m.group(1) + ' ' + m.group(2)

            if self._debug:
                box = self._cornersToBox(tl, br)
                self._drawBox(debug_img, box, (0, 255, 0))

        return self._match_name

    def _getTimeAndMode(self, img, debug_img):
        # Find time remaining
        tl = self._transformPoint((617, 21))
        br = self._transformPoint((667, 45))
        time_remaining = self._parseDigits(self._getImgCropThresh(img, tl, br))

        # Determine mode: 'pre_match', 'auto', 'teleop', or 'post_match'
        mode_point = self._transformPoint((497, 70))
        mode_point2 = self._transformPoint((581, 70))
        mode_sample = img[mode_point[1], mode_point[0], :]
        mode_sample2 = img[mode_point2[1], mode_point2[0], :]

        hsv = colorsys.rgb_to_hsv(float(mode_sample[2])/255, float(mode_sample[1])/255, float(mode_sample[0])/255)
        hsv2 = colorsys.rgb_to_hsv(float(mode_sample2[2])/255, float(mode_sample2[1])/255, float(mode_sample2[0])/255)

        if time_remaining is None:
            mode = None
        if time_remaining == 0:
            if hsv[1] > 0.6 and hsv2[1] > 0.6:  # Both saturated
                mode = 'post_match'
            elif hsv[1] > 0.6:  # First saturated
                mode = 'auto'  # End of auton
            else:
                mode = 'pre_match'
        elif time_remaining <= 15 and hsv2[1] < 0.6:
            mode = 'auto'
        else:
            mode = 'teleop'

        if self._debug:
            box = self._cornersToBox(tl, br)
            self._drawBox(debug_img, box, (0, 255, 0))
            cv2.circle(debug_img, mode_point, 2, (0, 255, 0), -1)
            cv2.circle(debug_img, mode_point2, 2, (0, 255, 0), -1)

        return time_remaining, mode

    def _getFlipped(self, img, debug_img):
        # Sample point to determine red/blue side
        color_point = self._transformPoint((518, 135))
        color_sample = img[color_point[1], color_point[0], :]
        is_flipped = color_sample[0] > color_sample[2]  # More blue than red

        if self._debug:
            cv2.circle(debug_img, color_point, 2, (0, 255, 0), -1)

        return is_flipped

    def _getScores(self, img, debug_img, is_flipped):
        # Left score limits
        left_tl = self._transformPoint((521, 70))
        left_br = self._transformPoint((623, 125))
        # Right score limits
        right_tl = self._transformPoint((670, 70))
        right_br = self._transformPoint((772, 125))

        left_score = self._parseDigits(self._getImgCropThresh(img, left_tl, left_br, white=True))
        right_score = self._parseDigits(self._getImgCropThresh(img, right_tl, right_br, white=True))

        if is_flipped:
            red_score = right_score
            blue_score = left_score
        else:
            red_score = left_score
            blue_score = right_score

        if self._debug:
            left_box = self._cornersToBox(left_tl, left_br)
            right_box = self._cornersToBox(right_tl, right_br)
            self._drawBox(debug_img, left_box, (255, 255, 0) if is_flipped else (255, 0, 255))
            self._drawBox(debug_img, right_box, (255, 0, 255) if is_flipped else (255, 255, 0))

        return red_score, blue_score

    def _getVaultInfo(self, img, debug_img, is_flipped):
        # Left powerups
        left_boost_tl = self._transformPoint((81, 107))
        left_boost_br = self._transformPoint((100, 131))
        left_boost_loc = self._transformPoint((39, 102))
        left_force_tl = self._transformPoint((151, 107))
        left_force_br = self._transformPoint((170, 131))
        left_force_loc = self._transformPoint((211, 102))
        left_levitate_tl = self._transformPoint((118, 78))
        left_levitate_br = self._transformPoint((131, 100))
        left_levitate_loc = self._transformPoint((100, 51))

        # Right powerups
        right_boost_tl = self._transformPoint((1109, 111))
        right_boost_br = self._transformPoint((1127, 133))
        right_boost_loc = self._transformPoint((1067, 104))
        right_force_tl = self._transformPoint((1181, 110))
        right_force_br = self._transformPoint((1199, 133))
        right_force_loc = self._transformPoint((1238, 104))
        right_levitate_tl = self._transformPoint((1145, 81))
        right_levitate_br = self._transformPoint((1162, 103))
        right_levitate_loc = self._transformPoint((1126, 51))

        # Counts
        left_boost_count = self._parseDigits(self._getImgCropThresh(img, left_boost_tl, left_boost_br))
        left_force_count = self._parseDigits(self._getImgCropThresh(img, left_force_tl, left_force_br))
        left_levitate_count = self._parseDigits(self._getImgCropThresh(img, left_levitate_tl, left_levitate_br))
        right_boost_count = self._parseDigits(self._getImgCropThresh(img, right_boost_tl, right_boost_br))
        right_force_count = self._parseDigits(self._getImgCropThresh(img, right_force_tl, right_force_br))
        right_levitate_count = self._parseDigits(self._getImgCropThresh(img, right_levitate_tl, right_levitate_br))

        # Played
        left_boost_played = self._checkSaturated(img, left_boost_loc)
        left_force_played = self._checkSaturated(img, left_force_loc)
        left_levitate_played = self._checkSaturated(img, left_levitate_loc)
        right_boost_played = self._checkSaturated(img, right_boost_loc)
        right_force_played = self._checkSaturated(img, right_force_loc)
        right_levitate_played = self._checkSaturated(img, right_levitate_loc)

        if is_flipped:
            red_boost_count = right_boost_count
            red_force_count = right_force_count
            red_levitate_count = right_levitate_count
            red_boost_played = right_boost_played
            red_force_played = right_force_played
            red_levitate_played = right_levitate_played
            blue_boost_count = left_boost_count
            blue_force_count = left_force_count
            blue_levitate_count = left_levitate_count
            blue_boost_played = left_boost_played
            blue_force_played = left_force_played
            blue_levitate_played = left_levitate_played
        else:
            red_boost_count = left_boost_count
            red_force_count = left_force_count
            red_levitate_count = left_levitate_count
            red_boost_played = left_boost_played
            red_force_played = left_force_played
            red_levitate_played = left_levitate_played
            blue_boost_count = right_boost_count
            blue_force_count = right_force_count
            blue_levitate_count = right_levitate_count
            blue_boost_played = right_boost_played
            blue_force_played = right_force_played
            blue_levitate_played = right_levitate_played

        if self._debug:
            left_color = (255, 255, 0) if is_flipped else (255, 0, 255)
            right_color = (255, 0, 255) if is_flipped else (255, 255, 0)
            left_boost_box = self._cornersToBox(left_boost_tl, left_boost_br)
            left_force_box = self._cornersToBox(left_force_tl, left_force_br)
            left_levitate_box = self._cornersToBox(left_levitate_tl, left_levitate_br)
            right_boost_box = self._cornersToBox(right_boost_tl, right_boost_br)
            right_force_box = self._cornersToBox(right_force_tl, right_force_br)
            right_levitate_box = self._cornersToBox(right_levitate_tl, right_levitate_br)
            self._drawBox(debug_img, left_boost_box, left_color)
            self._drawBox(debug_img, left_force_box, left_color)
            self._drawBox(debug_img, left_levitate_box, left_color)
            self._drawBox(debug_img, right_boost_box, right_color)
            self._drawBox(debug_img, right_force_box, right_color)
            self._drawBox(debug_img, right_levitate_box, right_color)
            cv2.circle(debug_img, left_boost_loc, 2, left_color, -1)
            cv2.circle(debug_img, left_force_loc, 2, left_color, -1)
            cv2.circle(debug_img, left_levitate_loc, 2, left_color, -1)
            cv2.circle(debug_img, right_boost_loc, 2, right_color, -1)
            cv2.circle(debug_img, right_force_loc, 2, right_color, -1)
            cv2.circle(debug_img, right_levitate_loc, 2, right_color, -1)

        return (
            red_boost_count, red_boost_played,
            red_force_count, red_force_played,
            red_levitate_count, red_levitate_played,
            blue_boost_count, blue_boost_played,
            blue_force_count, blue_force_played,
            blue_levitate_count, blue_levitate_played,
        )


    def _getSwitchScaleInfo(self, img, debug_img, is_flipped):
        left_switch_loc = self._transformPoint((272, 91))
        left_scale_loc = self._transformPoint((272, 67))
        right_switch_loc = self._transformPoint((1014,  91))
        right_scale_loc = self._transformPoint((1014, 67))

        left_switch_owned = self._checkSaturated(img, left_switch_loc)
        left_scale_owned = self._checkSaturated(img, left_scale_loc)
        right_switch_owned = self._checkSaturated(img, right_switch_loc)
        right_scale_owned = self._checkSaturated(img, right_scale_loc)

        if is_flipped:
            red_switch_owned = right_switch_owned
            red_scale_owned = right_scale_owned
            blue_switch_owned = left_switch_owned
            blue_scale_owned = left_scale_owned
        else:
            red_switch_owned = left_switch_owned
            red_scale_owned = left_scale_owned
            blue_switch_owned = right_switch_owned
            blue_scale_owned = right_scale_owned

        if self._debug:
            left_color = (255, 255, 0) if is_flipped else (255, 0, 255)
            right_color = (255, 0, 255) if is_flipped else (255, 255, 0)
            cv2.circle(debug_img, left_switch_loc, 2, left_color, -1)
            cv2.circle(debug_img, left_scale_loc, 2, left_color, -1)
            cv2.circle(debug_img, right_switch_loc, 2, right_color, -1)
            cv2.circle(debug_img, right_scale_loc, 2, right_color, -1)

        return (
            red_switch_owned, blue_switch_owned,
            red_scale_owned, blue_scale_owned,
        )

    def _getPowerupInfo(self, img, debug_img):
        # Who owns powerup
        color_point = self._transformPoint((644, 67))
        powerup_played = self._checkSaturated(img, color_point)
        if not powerup_played:
            return None, None, None, None
        color_sample = img[color_point[1], color_point[0], :]
        is_red_powerup = color_sample[0] < color_sample[2]  # More red than blue

        # How much time left
        time_tl = self._transformPoint((632, 68))
        time_br = self._transformPoint((659, 96))
        time = self._parseDigits(self._getImgCropThresh(img, time_tl, time_br, white=True))

        # Which powerup
        powerup_tl = self._transformPoint((630, 95))
        powerup_br = self._transformPoint((660, 125))
        powerup_img = img[powerup_tl[1]:powerup_br[1], powerup_tl[0]:powerup_br[0]]

        scale = self._transform['scale'] * self._TEMPLATE_SCALE
        best_max_val = 0
        current_powerup = None
        for key, template_img in self._templates.items():
            template_img = cv2.resize(template_img, (int(template_img.shape[0]*scale), int(template_img.shape[1]*scale)))
            res = cv2.matchTemplate(powerup_img, template_img, cv2.TM_CCOEFF)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val > best_max_val:
                best_max_val = max_val
                current_powerup = key

        if self._debug:
            time_box = self._cornersToBox(time_tl, time_br)
            self._drawBox(debug_img, time_box, (0, 255, 0))
            cv2.circle(debug_img, color_point, 2, (0, 255, 0), -1)
            powerup_box = self._cornersToBox(powerup_tl, powerup_br)
            self._drawBox(debug_img, powerup_box, (0, 255, 0))

        if is_red_powerup:
            return (current_powerup, None, time, None)
        else:
            return (None, current_powerup, None, time)

    def _getMatchDetails(self, img):
        debug_img = None
        if self._debug:
            debug_img = img.copy()

        time_remaining, mode = self._getTimeAndMode(img, debug_img)
        if mode in {'pre_match', 'post_match'}:
            self._match_name = None
        match = self._getMatchName(img, debug_img)
        is_flipped = self._getFlipped(img, debug_img)
        red_score, blue_score = self._getScores(img, debug_img, is_flipped)

        (
            red_boost_count, red_boost_played,
            red_force_count, red_force_played,
            red_levitate_count, red_levitate_played,
            blue_boost_count, blue_boost_played,
            blue_force_count, blue_force_played,
            blue_levitate_count, blue_levitate_played,
        ) = self._getVaultInfo(img, debug_img, is_flipped)
        (
            red_switch_owned, blue_switch_owned,
            red_scale_owned, blue_scale_owned,
        ) = self._getSwitchScaleInfo(img, debug_img, is_flipped)
        (
            red_current_powerup, blue_current_powerup,
            red_powerup_time_remaining, blue_powerup_time_remaining,
        ) = self._getPowerupInfo(img, debug_img)

        if self._debug:
            cv2.imshow("ROIs", debug_img)
            cv2.waitKey(1)

        if match is not None and red_score is not None \
                and blue_score is not None and time_remaining is not None:
            return OngoingMatchDetails(
                match=match,
                mode=mode,
                time=time_remaining,
                red=Alliance2018(
                    score=red_score,
                    boost_count=red_boost_count,
                    boost_played=red_boost_played,
                    force_count=red_force_count,
                    force_played=red_force_played,
                    levitate_count=red_levitate_count,
                    levitate_played=red_levitate_played,
                    switch_owned=red_switch_owned,
                    scale_owned=red_scale_owned,
                    current_powerup=red_current_powerup,
                    powerup_time_remaining=red_powerup_time_remaining,
                ),
                blue=Alliance2018(
                    score=blue_score,
                    boost_count=blue_boost_count,
                    boost_played=blue_boost_played,
                    force_count=blue_force_count,
                    force_played=blue_force_played,
                    levitate_count=blue_levitate_count,
                    levitate_played=blue_levitate_played,
                    switch_owned=blue_switch_owned,
                    scale_owned=blue_scale_owned,
                    current_powerup=blue_current_powerup,
                    powerup_time_remaining=blue_powerup_time_remaining,
                )
            )
        else:
            return None

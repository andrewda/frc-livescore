import colorsys
import cv2
from PIL import Image
import pkg_resources

from .LivescoreBase import LivescoreBase
from .details import Alliance2018, OngoingMatchDetails


class Livescore2018(LivescoreBase):
    def __init__(self, **kwargs):
        super(Livescore2018, self).__init__(2018, **kwargs)
        self._match_key = None
        self._match_name = None

        # Power up templates
        template_path = pkg_resources.resource_filename(__name__, 'templates')
        self._templates = {
            'boost': cv2.imread(template_path + '/2018_boost.png'),
            'force': cv2.imread(template_path + '/2018_force.png'),
            'levitate': cv2.imread(template_path + '/2018_levitate.png'),
        }

    def _getMatchKeyName(self, img, debug_img):
        if self._match_key is None:
            tl = self._transformPoint((159, 130))
            br = self._transformPoint((570, 162))

            raw_match_name = self._parseRawMatchName(self._getImgCropThresh(img, tl, br))
            self._match_key = self._getMatchKey(raw_match_name)
            if self._match_key:
                self._match_name = raw_match_name
            else:
                self._match_name = None

            if self._debug:
                box = self._cornersToBox(tl, br)
                self._drawBox(debug_img, box, (0, 255, 0))

        return self._match_key, self._match_name

    def _getTimeAndMode(self, img, debug_img):
        # Check for match under review
        review_point1 = self._transformPoint((624, 50))
        review_sample1 = img[review_point1[1], review_point1[0], :]
        hsvL = colorsys.rgb_to_hsv(float(review_sample1[2])/255, float(review_sample1[1])/255, float(review_sample1[0])/255)
        review_point2 = self._transformPoint((1279 - 624, 50))
        review_sample2 = img[review_point2[1], review_point2[0], :]
        hsvR = colorsys.rgb_to_hsv(float(review_sample2[2])/255, float(review_sample2[1])/255, float(review_sample2[0])/255)
        if hsvL[0] > 0.116 and hsvL[0] < 0.216 and hsvR[0] > 0.116 and hsvR[0] < 0.216:
            return 0, 'post_match'

        # Find time remaining
        tl = self._transformPoint((617, 14))
        br = self._transformPoint((665, 38))
        time_remaining = self._parseDigits(self._getImgCropThresh(img, tl, br))

        # Determine mode: 'pre_match', 'auto', 'teleop', or 'post_match'
        mode_point = self._transformPoint((497, 15))
        mode_point2 = self._transformPoint((581, 15))
        mode_sample = img[mode_point[1], mode_point[0], :]
        mode_sample2 = img[mode_point2[1], mode_point2[0], :]

        hsv1 = colorsys.rgb_to_hsv(float(mode_sample[2])/255, float(mode_sample[1])/255, float(mode_sample[0])/255)
        hsv2 = colorsys.rgb_to_hsv(float(mode_sample2[2])/255, float(mode_sample2[1])/255, float(mode_sample2[0])/255)

        if time_remaining is None:
            return None, None

        if time_remaining == 0:
            if hsv1[1] > 0.6 and hsv2[1] > 0.6:  # Both saturated
                mode = 'post_match'
            elif hsv1[1] > 0.6:  # First saturated
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
        color_point = self._transformPoint((496, 52))
        color_sample = img[color_point[1], color_point[0], :]
        is_flipped = color_sample[0] > color_sample[2]  # More blue than red

        if self._debug:
            cv2.circle(debug_img, color_point, 2, (0, 255, 0), -1)

        return is_flipped

    def _getScores(self, img, debug_img, is_flipped):
        # Left score limits
        left_tl = self._transformPoint((497, 61))
        left_br = self._transformPoint((618, 114))
        # Right score limits
        right_tl = self._transformPoint((661, 61))
        right_br = self._transformPoint((779, 114))

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
        left_force_tl = self._transformPoint((75, 83))
        left_force_br = self._transformPoint((93, 106))
        left_force_loc = self._transformPoint((40, 84))
        left_boost_tl = self._transformPoint((145, 83))
        left_boost_br = self._transformPoint((163, 106))
        left_boost_loc = self._transformPoint((198, 84))
        left_levitate_tl = self._transformPoint((110, 65))
        left_levitate_br = self._transformPoint((127, 86))
        left_levitate_loc = self._transformPoint((99, 44))

        # Right powerups
        right_force_tl = self._transformPoint((1279 - 163, 83))
        right_force_br = self._transformPoint((1279 - 145, 106))
        right_force_loc = self._transformPoint((1279 - 198, 84))
        right_boost_tl = self._transformPoint((1279 - 93, 83))
        right_boost_br = self._transformPoint((1279 - 75, 106))
        right_boost_loc = self._transformPoint((1279 - 40, 84))
        right_levitate_tl = self._transformPoint((1279 - 128, 65))
        right_levitate_br = self._transformPoint((1279 - 110, 86))
        right_levitate_loc = self._transformPoint((1279 - 99, 44))

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
        left_switch_loc = self._transformPoint((257, 76))
        left_scale_loc = self._transformPoint((257, 51))
        right_switch_loc = self._transformPoint((1279 - 257,  76))
        right_scale_loc = self._transformPoint((1279 - 257, 51))

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
        left_point = self._transformPoint((631, 107))
        right_point = self._transformPoint((1279 - 631, 107))
        # Which powerup
        powerup_tl = self._transformPoint((630, 80))
        powerup_br = self._transformPoint((1279 - 630, 105))
        # How much time left
        time_tl = self._transformPoint((624, 50))
        time_br = self._transformPoint((1279 - 624, 79))

        if self._debug:
            time_box = self._cornersToBox(time_tl, time_br)
            self._drawBox(debug_img, time_box, (0, 255, 0))
            cv2.circle(debug_img, left_point, 2, (0, 255, 0), -1)
            cv2.circle(debug_img, right_point, 2, (0, 255, 0), -1)
            powerup_box = self._cornersToBox(powerup_tl, powerup_br)
            self._drawBox(debug_img, powerup_box, (0, 255, 0))

        # Who owns powerup
        left_bgr = img[left_point[1], left_point[0], :]
        right_bgr = img[right_point[1], right_point[0], :]

        if not ((left_bgr[0] > left_bgr[2] and right_bgr[0] > right_bgr[2]) or
                (left_bgr[0] < left_bgr[2] and right_bgr[0] < right_bgr[2])):
            return None, None, None, None

        is_red_powerup = left_bgr[0] < left_bgr[2]  # More red than blue

        # How much time left
        time = self._parseDigits(self._getImgCropThresh(img, time_tl, time_br, white=True))

        # Which powerup
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

        if is_red_powerup:
            return (current_powerup, None, time, None)
        else:
            return (None, current_powerup, None, time)

    def _getAutoBoss(self, img, debug_img, is_flipped):
        left_auto_loc = self._transformPoint((550, 54))
        left_boss_loc = self._transformPoint((580, 54))
        right_auto_loc = self._transformPoint((700, 54))
        right_boss_loc = self._transformPoint((730, 54))

        left_auto_sample = img[left_auto_loc[1], left_auto_loc[0], :]
        left_boss_sample = img[left_boss_loc[1], left_boss_loc[0], :]
        right_auto_sample = img[right_auto_loc[1], right_auto_loc[0], :]
        right_boss_sample = img[right_boss_loc[1], right_boss_loc[0], :]

        left_auto_hsv = colorsys.rgb_to_hsv(float(left_auto_sample[2])/255, float(left_auto_sample[1])/255, float(left_auto_sample[0])/255)
        left_boss_hsv = colorsys.rgb_to_hsv(float(left_boss_sample[2])/255, float(left_boss_sample[1])/255, float(left_boss_sample[0])/255)
        right_auto_hsv = colorsys.rgb_to_hsv(float(right_auto_sample[2])/255, float(right_auto_sample[1])/255, float(right_auto_sample[0])/255)
        right_boss_hsv = colorsys.rgb_to_hsv(float(right_boss_sample[2])/255, float(right_boss_sample[1])/255, float(right_boss_sample[0])/255)

        left_auto_quest = left_auto_hsv[0] > 0.116 and left_auto_hsv[0] < 0.216
        left_face_the_boss = left_boss_hsv[0] > 0.116 and left_boss_hsv[0] < 0.216
        right_auto_quest = right_auto_hsv[0] > 0.116 and right_auto_hsv[0] < 0.216
        right_face_the_boss = right_boss_hsv[0] > 0.116 and right_boss_hsv[0] < 0.216

        if is_flipped:
            red_auto_quest = right_auto_quest
            red_face_the_boss = right_face_the_boss
            blue_auto_quest = left_auto_quest
            blue_face_the_boss = left_face_the_boss
        else:
            red_auto_quest = left_auto_quest
            red_face_the_boss = left_face_the_boss
            blue_auto_quest = right_auto_quest
            blue_face_the_boss = right_face_the_boss

        if self._debug:
            left_color = (255, 255, 0) if is_flipped else (255, 0, 255)
            right_color = (255, 0, 255) if is_flipped else (255, 255, 0)
            cv2.circle(debug_img, left_auto_loc, 2, left_color, -1)
            cv2.circle(debug_img, left_boss_loc, 2, left_color, -1)
            cv2.circle(debug_img, right_auto_loc, 2, right_color, -1)
            cv2.circle(debug_img, right_boss_loc, 2, right_color, -1)

        return (
            red_auto_quest, blue_auto_quest,
            red_face_the_boss, blue_face_the_boss,
        )

    def _getMatchDetails(self, img, force_find_overlay):
        debug_img = None
        if self._debug:
            debug_img = img.copy()

        time_remaining, mode = self._getTimeAndMode(img, debug_img)
        if self._is_new_overlay or force_find_overlay:
            self._match_key = None
        match_key, match_name = self._getMatchKeyName(img, debug_img)
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
        (
            red_auto_quest, blue_auto_quest,
            red_face_the_boss, blue_face_the_boss,
        ) = self._getAutoBoss(img, debug_img, is_flipped)

        if self._debug:
            cv2.imshow("ROIs", debug_img)
            cv2.waitKey(1)

        if match_key is not None and red_score is not None \
                and blue_score is not None and time_remaining is not None:
            return OngoingMatchDetails(
                match_key=match_key,
                match_name=match_name,
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
                    auto_quest=red_auto_quest,
                    face_the_boss=red_face_the_boss,
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
                    auto_quest=blue_auto_quest,
                    face_the_boss=blue_face_the_boss,
                )
            )
        else:
            return None

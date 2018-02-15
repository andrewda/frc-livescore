import colorsys
import cv2
from PIL import Image
import pkg_resources
import pytesseract

from LivescoreBase import LivescoreBase
from details import Alliance2017, OngoingMatchDetails


class Livescore2017(LivescoreBase):
    def __init__(self, **kwargs):
        super(Livescore2017, self).__init__(2017, **kwargs)
        self._match_key = None
        self._match_name = None

    def _getMatchKeyName(self, img, debug_img):
        if self._match_key is None:
            tl = self._transformPoint((155, 6))
            br = self._transformPoint((632, 43))

            config = '--psm 7'
            raw_match_name = pytesseract.image_to_string(
                Image.fromarray(self._getImgCropThresh(img, tl, br)), config=config).strip()
            self._match_key = self._getMatchKey(raw_match_name)

            if self._debug:
                box = self._cornersToBox(tl, br)
                self._drawBox(debug_img, box, (0, 255, 0))

        return self._match_key, self._match_name

    def _getTimeAndMode(self, img, debug_img):
        # Find time remaining
        tl = self._transformPoint((617, 55))
        br = self._transformPoint((667, 81))
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
        color_point = self._transformPoint((496, 95))
        color_sample = img[color_point[1], color_point[0], :]
        is_flipped = color_sample[0] > color_sample[2]  # More blue than red

        if self._debug:
            cv2.circle(debug_img, color_point, 2, (0, 255, 0), -1)

        return is_flipped

    def _getScores(self, img, debug_img, is_flipped):
        # Left score limits
        left_tl = self._transformPoint((496, 90))
        left_br = self._transformPoint((634, 152))
        # Right score limits
        right_tl = self._transformPoint((644, 90))
        right_br = self._transformPoint((784, 152))

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

    def _getFuelScores(self, img, debug_img, is_flipped):
        # Left fuel score
        left_tl = self._transformPoint((316, 123))
        left_br = self._transformPoint((362, 152))
        # Left fuel count
        left_fuel_locs = [
            self._transformPoint((355, 107)),
            self._transformPoint((348, 86)),
            self._transformPoint((332, 70)),
            self._transformPoint((312, 64)),
            self._transformPoint((289, 70)),
            self._transformPoint((273, 86)),
            self._transformPoint((264, 107)),
            self._transformPoint((272, 130)),
            self._transformPoint((289, 146)),
        ]
        # Right fuel score
        right_tl = self._transformPoint((916, 123))
        right_br = self._transformPoint((963, 152))
        # Right fuel count
        right_fuel_locs = [
            self._transformPoint((925, 107)),
            self._transformPoint((930, 86)),
            self._transformPoint((944, 70)),
            self._transformPoint((967, 64)),
            self._transformPoint((991, 70)),
            self._transformPoint((1007, 86)),
            self._transformPoint((1015, 107)),
            self._transformPoint((1007, 130)),
            self._transformPoint((991, 146)),
        ]

        left_fuel_score = self._parseDigits(self._getImgCropThresh(img, left_tl, left_br))
        right_fuel_score = self._parseDigits(self._getImgCropThresh(img, right_tl, right_br))

        left_fuel_count = 0
        for x, y in left_fuel_locs:
            bgr = img[y, x, :]
            hsv = colorsys.rgb_to_hsv(float(bgr[2])/255, float(bgr[1])/255, float(bgr[0])/255)
            if hsv[1] > 0.2:
                left_fuel_count += 1
            else:
                break

        right_fuel_count = 0
        for x, y in right_fuel_locs:
            bgr = img[y, x, :]
            hsv = colorsys.rgb_to_hsv(float(bgr[2])/255, float(bgr[1])/255, float(bgr[0])/255)
            if hsv[1] > 0.2:
                right_fuel_count += 1
            else:
                break

        if is_flipped:
            red_fuel_score = right_fuel_score
            red_fuel_count = right_fuel_count
            blue_fuel_score = left_fuel_score
            blue_fuel_count = left_fuel_count
        else:
            red_fuel_score = left_fuel_score
            red_fuel_count = left_fuel_count
            blue_fuel_score = right_fuel_score
            blue_fuel_count = right_fuel_count

        if self._debug:
            left_color = (255, 255, 0) if is_flipped else (255, 0, 255)
            right_color = (255, 0, 255) if is_flipped else (255, 255, 0)
            left_box = self._cornersToBox(left_tl, left_br)
            right_box = self._cornersToBox(right_tl, right_br)
            self._drawBox(debug_img, left_box, left_color)
            self._drawBox(debug_img, right_box, right_color)
            for point in left_fuel_locs:
                cv2.circle(debug_img, point, 2, left_color, -1)
            for point in right_fuel_locs:
                cv2.circle(debug_img, point, 2, right_color, -1)


        return red_fuel_score, red_fuel_count, blue_fuel_score, blue_fuel_count

    def _getRotors(self, img, debug_img, is_flipped):
        left_tl = self._transformPoint((210, 123))
        left_br = self._transformPoint((230, 148))
        right_tl = self._transformPoint((1048, 123))
        right_br = self._transformPoint((1068, 148))

        left_rotors = self._parseDigits(self._getImgCropThresh(img, left_tl, left_br))
        right_rotors = self._parseDigits(self._getImgCropThresh(img, right_tl, right_br))

        if is_flipped:
            red_rotors = right_rotors
            blue_rotors = left_rotors
        else:
            red_rotors = left_rotors
            blue_rotors = right_rotors

        if self._debug:
            left_color = (255, 255, 0) if is_flipped else (255, 0, 255)
            right_color = (255, 0, 255) if is_flipped else (255, 255, 0)
            left_box = self._cornersToBox(left_tl, left_br)
            right_box = self._cornersToBox(right_tl, right_br)
            self._drawBox(debug_img, left_box, left_color)
            self._drawBox(debug_img, right_box, right_color)

        return red_rotors, blue_rotors

    def _getTouchpads(self, img, debug_img, is_flipped):
        left_tl = self._transformPoint((100, 123))
        left_br = self._transformPoint((120, 148))
        right_tl = self._transformPoint((1158, 123))
        right_br = self._transformPoint((1178, 148))

        left_touchpads = self._parseDigits(self._getImgCropThresh(img, left_tl, left_br))
        right_touchpads = self._parseDigits(self._getImgCropThresh(img, right_tl, right_br))

        if is_flipped:
            red_touchpads = right_touchpads
            blue_touchpads = left_touchpads
        else:
            red_touchpads = left_touchpads
            blue_touchpads = right_touchpads

        if self._debug:
            left_color = (255, 255, 0) if is_flipped else (255, 0, 255)
            right_color = (255, 0, 255) if is_flipped else (255, 255, 0)
            left_box = self._cornersToBox(left_tl, left_br)
            right_box = self._cornersToBox(right_tl, right_br)
            self._drawBox(debug_img, left_box, left_color)
            self._drawBox(debug_img, right_box, right_color)

        return red_touchpads, blue_touchpads

    def _getMatchDetails(self, img):
        debug_img = None
        if self._debug:
            debug_img = img.copy()

        time_remaining, mode = self._getTimeAndMode(img, debug_img)
        if mode in {'pre_match', 'post_match'}:
            self._match_key = None
        match_key, match_name = self._getMatchKeyName(img, debug_img)

        is_flipped = self._getFlipped(img, debug_img)
        red_score, blue_score = self._getScores(img, debug_img, is_flipped)
        red_fuel_score, red_fuel_count, blue_fuel_score, blue_fuel_count = self._getFuelScores(img, debug_img, is_flipped)
        red_rotors, blue_rotors = self._getRotors(img, debug_img, is_flipped)
        red_touchpads, blue_touchpads = self._getTouchpads(img, debug_img, is_flipped)

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
                red=Alliance2017(
                    score=red_score,
                    fuel_score=red_fuel_score,
                    fuel_count=red_fuel_count,
                    rotor_count=red_rotors,
                    touchpad_count=red_touchpads
                ),
                blue=Alliance2017(
                    score=blue_score,
                    fuel_score=blue_fuel_score,
                    fuel_count=blue_fuel_count,
                    rotor_count=blue_rotors,
                    touchpad_count=blue_touchpads
                )
            )
        else:
            return None

import colorsys
import cv2
from PIL import Image
import pkg_resources
import pytesseract
import re

from LivescoreBase import LivescoreBase
from details import Alliance, OngoingMatchDetails


class Livescore2017(LivescoreBase):
    def __init__(self, debug=False):
        super(Livescore2017, self).__init__(2017, debug=debug)

    def _getMatchName(self, img, debug_img):
        tl = self._transformPoint((155, 6))
        br = self._transformPoint((632, 43))

        config = '--psm 7'
        long_match = pytesseract.image_to_string(
            Image.fromarray(self._getImgCropThresh(img, tl, br)), config=config).strip()

        match = None
        m = re.search('([a-zA-z]+) ([1-9]+)( of ...?)?', long_match)
        if m is not None:
            match = m.group(1) + ' ' + m.group(2)

        if self._debug:
            box = self._cornersToBox(tl, br)
            self._drawBox(debug_img, box, (0, 255, 0))

        return match

    def _getScores(self, img, debug_img):
        # Left score limits
        left_tl = self._transformPoint((496, 93))
        left_br = self._transformPoint((634, 155))
        # Right score limits
        right_tl = self._transformPoint((644, 93))
        right_br = self._transformPoint((784, 155))
        # Sample point to determine red/blue side
        color_point = self._transformPoint((496, 95))

        left_score = self._parseDigits(self._getImgCropThresh(img, left_tl, left_br, white=True), use_trained_font=False)
        right_score = self._parseDigits(self._getImgCropThresh(img, right_tl, right_br, white=True), use_trained_font=False)

        color_sample = img[color_point[1], color_point[0], :]
        is_flipped = color_sample[0] > color_sample[2]  # More blue than red

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
            cv2.circle(debug_img, color_point, 2, (0, 255, 0), -1)

        return red_score, blue_score, is_flipped

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

    def _getTimeRemaining(self, img, debug_img):
        tl = self._transformPoint((605, 56))
        br = self._transformPoint((672, 82))

        time_remaining = self._parseDigits(self._getImgCropThresh(img, tl, br))

        if self._debug:
            box = self._cornersToBox(tl, br)
            self._drawBox(debug_img, box, (0, 255, 0))

        return time_remaining

    def _getMatchDetails(self, img):
        debug_img = None
        if self._debug:
            debug_img = img.copy()

        match = self._getMatchName(img, debug_img)
        red_score, blue_score, is_flipped = self._getScores(img, debug_img)
        red_fuel_score, red_fuel_count, blue_fuel_score, blue_fuel_count = self._getFuelScores(img, debug_img, is_flipped)
        time_remaining = self._getTimeRemaining(img, debug_img)

        if self._debug:
            cv2.imshow("ROIs", debug_img)
            cv2.waitKey(1)

        if match is not None and red_score is not None \
                and blue_score is not None and time_remaining is not None:
            return OngoingMatchDetails(
                match=match,
                time=time_remaining,
                red=Alliance(score=red_score, fuel_score=red_fuel_score, fuel_count=red_fuel_count),
                blue=Alliance(score=blue_score, fuel_score=blue_fuel_score, fuel_count=blue_fuel_count))
        else:
            return None

    def read(self, img):
        img = cv2.resize(img, (1280, 720))

        if self._transform is None:
            self._findScoreOverlay(img)

        match_details = self._getMatchDetails(img)
        if match_details is None:
            self._findScoreOverlay(img)
            match_details = self._getMatchDetails(img)

        return match_details

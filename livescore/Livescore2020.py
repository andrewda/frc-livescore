import colorsys
import cv2
from PIL import Image
import pkg_resources

from .LivescoreBase import LivescoreBase
from .details import Alliance, OngoingMatchDetails


class Livescore2020(LivescoreBase):
    def __init__(self, **kwargs):
        super(Livescore2020, self).__init__(2020, **kwargs)
        self._match_key = None
        self._match_name = None

    def _getMatchKeyName(self, img, debug_img):
        if self._match_key is None:
            tl = self._transformPoint((220, 6))
            br = self._transformPoint((570, 43))

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
        review_point1 = self._transformPoint((624, 93))
        review_sample1 = img[review_point1[1], review_point1[0], :]
        hsvL = colorsys.rgb_to_hsv(float(review_sample1[2])/255, float(review_sample1[1])/255, float(review_sample1[0])/255)
        review_point2 = self._transformPoint((1279 - 624, 93))
        review_sample2 = img[review_point2[1], review_point2[0], :]
        hsvR = colorsys.rgb_to_hsv(float(review_sample2[2])/255, float(review_sample2[1])/255, float(review_sample2[0])/255)
        if hsvL[0] > 0.116 and hsvL[0] < 0.216 and hsvR[0] > 0.116 and hsvR[0] < 0.216:
            return 0, 'post_match'

        # Find time remaining
        horiz_center = self._TEMPLATE_SHAPE[0]/2
        tl = self._transformPoint((horiz_center-25, 56))
        br = self._transformPoint((horiz_center+25, 82))
        time_remaining = self._parseDigits(self._getImgCropThresh(img, tl, br))

        if self._debug:
            # draw a green box for time
            box = self._cornersToBox(tl, br)
            self._drawBox(debug_img, box, (0, 255, 0))

        # Determine mode: 'pre_match', 'auto', 'teleop', or 'post_match'
        mode_point = self._transformPoint((520, 70))
        mode_point2 = self._transformPoint((581, 70))
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
            cv2.circle(debug_img, review_point1, 2, (0, 255, 0), -1)
            cv2.circle(debug_img, review_point2, 2, (0, 255, 0), -1)
            cv2.circle(debug_img, mode_point, 2, (0, 255, 0), -1)
            cv2.circle(debug_img, mode_point2, 2, (0, 255, 0), -1)

        return time_remaining, mode

    def _getFlipped(self, img, debug_img):
        # Sample point to determine red/blue side
        color_point = self._transformPoint((520, 95))
        color_sample = img[color_point[1], color_point[0], :]
        is_flipped = color_sample[0] > color_sample[2]  # More blue than red

        if self._debug:
            cv2.circle(debug_img, color_point, 2, (0, 255, 0), -1)

        return is_flipped

    def _getScores(self, img, debug_img, is_flipped):
        # Left score limits
        left_tl = self._transformPoint((520, 110))
        left_br = self._transformPoint((634, 155))
        # Right score limits
        right_tl = self._transformPoint((644, 110))
        right_br = self._transformPoint((760, 155))

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

        box = self._cornersToBox(self._transformPoint((0,0)), self._transformPoint((1280, 170)))
        self._drawBox(debug_img, box, (255, 255, 0))

        if self._debug:
            cv2.imshow("ROIs", debug_img)
            cv2.waitKey(10000000)

        if match_key is not None and red_score is not None \
                and blue_score is not None and time_remaining is not None:
            return OngoingMatchDetails(
                match_key=match_key,
                match_name=match_name,
                mode=mode,
                time=time_remaining,
                red=Alliance(
                    score=red_score,
                ),
                blue=Alliance(
                    score=blue_score,
                )
            )
        else:
            return None

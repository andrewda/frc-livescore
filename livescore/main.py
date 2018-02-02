import colorsys
import cv2
import numpy as np
import pytesseract
import re
import pkg_resources
from PIL import Image

from details import Alliance, OngoingMatchDetails


class Livescore:
    def __init__(self, debug=False):
        local_path = pkg_resources.resource_filename(__name__, 'tessdata')
        template_path = pkg_resources.resource_filename(__name__, 'templates')

        self.WHITE_LOW = np.array([185, 185, 185])
        self.WHITE_HIGH = np.array([255, 255, 255])

        self.BLACK_LOW = np.array([0, 0, 0])
        self.BLACK_HIGH = np.array([135, 135, 155])

        self.local_path = local_path
        self._debug = debug

        self._transform = None  # scale, tx, ty

        # Setup feature detector and matcher
        self._detector = cv2.xfeatures2d.SURF_create()

        FLANN_INDEX_KDTREE = 0
        index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        search_params = dict(checks = 50)
        self._flann = cv2.FlannBasedMatcher(index_params, search_params)

        self.MIN_MATCH_COUNT = 10

        # Compute score overlay keypoints and descriptors
        self._TEMPLATE_SCALE = 0.5  # lower is faster
        template = cv2.imread(template_path + '/score_overlay_2017.png')
        shape = template.shape
        template = cv2.resize(template, (
            np.int32(np.round(shape[1] * self._TEMPLATE_SCALE)),
            np.int32(np.round(shape[0] * self._TEMPLATE_SCALE))
        ))
        self._kp1, self._des1 = self._detector.detectAndCompute(template, None)

    def _findScoreOverlay(self, img):
        # Finds and sets the 2d transform of the overlay in the image
        # Sets the transform to None if the overlay is not found

        kp2, des2 = self._detector.detectAndCompute(img, None)
        matches = self._flann.knnMatch(self._des1, des2, k=2)

        # Store all the good matches as per Lowe's ratio test
        good = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good.append(m)

        if len(good) > self.MIN_MATCH_COUNT:
            src_pts = np.float32([ self._kp1[m.queryIdx].pt for m in good ]).reshape(-1, 1, 2)
            dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1, 1, 2)

            t = cv2.estimateRigidTransform(src_pts, dst_pts, False)
            if t is not None:
                self._transform = {
                    'scale': t[0, 0],
                    'tx': t[0, 2],
                    'ty': t[1, 2],
                }
                return

        print("Not enough matches are found - {}/{}".format(len(good), self.MIN_MATCH_COUNT))
        self._transform = None

    def _transformPoint(self, point):
        # Transforms a point from template coordinates to image coordinates
        scale = self._transform['scale'] * self._TEMPLATE_SCALE
        tx = self._transform['tx']
        ty = self._transform['ty']
        return np.int32(np.round(point[0] * scale + tx)), np.int32(np.round(point[1] * scale + ty))

    def _cornersToBox(self, tl, br):
        return np.array([
            [tl[0], tl[1]],
            [br[0], tl[1]],
            [br[0], br[1]],
            [tl[0], br[1]]
        ])

    def _getImgCropThresh(self, img, tl, br, white=False):
        cropped = img[tl[1]:br[1], tl[0]:br[0]]
        if white:
            return cv2.inRange(cropped, self.WHITE_LOW, self.WHITE_HIGH)
        else:
            return cv2.inRange(cropped, self.BLACK_LOW, self.BLACK_HIGH)

    def _parseDigits(self, img):
        config = '--psm 8 -c tessedit_char_whitelist=1234567890 --tessdata-dir {}'.format(self.local_path.replace('\\', '/'))

        string = pytesseract.image_to_string(
            Image.fromarray(img),
            config=config).strip()
        if string and string.isdigit():
            return int(string)
        else:
            return None

    def _drawBox(self, img, box, color):
        cv2.polylines(img, [box], True, color, 2, cv2.LINE_AA)

    def _getMatch(self, img, debug_img):
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
        left_tl = self._transformPoint((491, 88))
        left_br = self._transformPoint((639, 160))
        # Right score limits
        right_tl = self._transformPoint((639, 88))
        right_br = self._transformPoint((789, 160))
        # Sample point to determine red/blue side
        color_point = self._transformPoint((496, 95))

        left_score = self._parseDigits(self._getImgCropThresh(img, left_tl, left_br, white=True))
        right_score = self._parseDigits(self._getImgCropThresh(img, right_tl, right_br, white=True))

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

        match = self._getMatch(img, debug_img)
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

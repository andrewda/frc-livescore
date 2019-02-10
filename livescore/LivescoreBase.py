import colorsys
import cv2
import numpy as np
import os
import pickle
import logging
from PIL import Image
import pkg_resources
import pytesseract
import regex

from .simpleocr_utils.segmentation import segments_to_numpy
from .simpleocr_utils.feature_extraction import SimpleFeatureExtractor

TESSDATA_DIR = os.path.dirname(os.path.realpath(__file__)) + '/tessdata'

class NoOverlayFoundException(Exception):
    pass


QF_BRACKET_ELIM_MAPPING = {
    1: (1, 1),  # (set, match)
    2: (2, 1),
    3: (3, 1),
    4: (4, 1),
    5: (1, 2),
    6: (2, 2),
    7: (3, 2),
    8: (4, 2),
}

SF_BRACKET_ELIM_MAPPING = {
    1: (1, 1),  # (set, match)
    2: (2, 1),
    3: (1, 2),
    4: (2, 2),
}


NUMBER_PATTERN = '0-9ZSO'  # Characters that might get recognized as numbers
def num_pat(r):
    return r.replace('@', NUMBER_PATTERN)


# Possible formats are like:
# Test Match
# Practice X of Y
# Qualification X of Y
# Octofinal X of Y
# Octofinal Tiebreaker X
# Quarterfinal X of Y
# Quarterfinal Tiebreaker X
# Semifinal X of Y
# Semifinal Tiebreaker X
# Final X
# Final Tiebreaker
# Einstein X of Y
# Einstein Final X
# Einstein Final Tiebreaker
MATCH_ID_FORMATS = [
    (regex.compile(num_pat('(Test\s+Match){e<=3}')), 'test', False),
    (regex.compile(num_pat('(Practice){e<=3}\s+([@]+)'), False), 'pm', False),
    (regex.compile(num_pat('(Qualification){e<=3}\s+([@]+)'), False), 'qm', False),
    (regex.compile(num_pat('(Octofinal){e<=3}\s+([@]+)'), False), 'ef', False),
    (regex.compile(num_pat('(Octofinal\s+Tiebreaker){e<=3}\s+([@]+)'), False), 'ef', True),
    (regex.compile(num_pat('(Quarterfinal){e<=3}\s+([@]+)'), False), 'qf', False),
    (regex.compile(num_pat('(Quarterfinal\s+Tiebreaker){e<=3}\s+([@]+)'), False), 'qf', True),
    (regex.compile(num_pat('(Semifinal){e<=3}\s+([@]+)'), False), 'sf', False),
    (regex.compile(num_pat('(Semifinal\s+Tiebreaker){e<=3}\s+([@]+)'), False), 'sf', True),
    (regex.compile(num_pat('(Final){e<=3}\s+([@]+)'), False), 'f', False),
    (regex.compile(num_pat('(Overtime){e<=3}\s+([@]+)'), False), 'overtimef', False),
    (regex.compile(num_pat('(Einstein){e<=3}\s+([@]+)'), False), 'sf', False),
    (regex.compile(num_pat('(Einstein\s+Final){e<=3}\s+([@]+)'), False), 'f', False),
    (regex.compile(num_pat('(Einstein\s+Final\s+Tiebreaker){e<=3}\s+([@]+)'), False), 'f', True),
]


def fix_digits(text):
    return int(text.replace('Z', '2').replace('S', '5').replace('O', '0'))


class LivescoreBase(object):
    def __init__(self, game_year, debug=False, save_training_data=False, training_data=None):
        self._debug = debug
        self._save_training_data = save_training_data
        self._is_new_overlay = False

        self._WHITE_LOW = np.array([120, 120, 120])
        self._WHITE_HIGH = np.array([255, 255, 255])

        self._BLACK_LOW = np.array([0, 0, 0])
        self._BLACK_HIGH = np.array([135, 135, 155])

        self._morph_kernel = np.ones((3, 3), np.uint8)

        self._OCR_HEIGHT = 64  # Do all OCR at this size

        self._transform = None  # scale, tx, ty

        # Setup feature detector and matcher
        self._detector = cv2.xfeatures2d.SURF_create()

        FLANN_INDEX_KDTREE = 0
        index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        search_params = dict(checks = 50)
        self._flann = cv2.FlannBasedMatcher(index_params, search_params)

        self._MIN_MATCH_COUNT = 9

        # Compute score overlay keypoints and descriptors
        self._TEMPLATE_SCALE = 0.5  # lower is faster
        template = cv2.imread(
            pkg_resources.resource_filename(__name__, 'templates') + \
            '/score_overlay_{}.png'.format(game_year))
        self._template = cv2.resize(template, (
            np.int32(np.round(template.shape[1] * self._TEMPLATE_SCALE)),
            np.int32(np.round(template.shape[0] * self._TEMPLATE_SCALE))
        ))
        self._kp1, self._des1 = self._detector.detectAndCompute(self._template, None)

        # For saving training data
        self._training_data = {
            'features': np.ndarray((0, 100)),
            'classes': np.ndarray((0, 1)),
        }

        # Train classifier
        if training_data is None:
            with open(pkg_resources.resource_filename(__name__, 'training_data') + '/digits.pkl', "rb") as f:
                training_data = pickle.load(f, encoding='latin1')
        else:
            with open(training_data, "rb") as f:
                training_data = pickle.load(f)
        self._knn = cv2.ml.KNearest_create()
        self._knn.train(training_data['features'].astype(np.float32), cv2.ml.ROW_SAMPLE, training_data['classes'].astype(np.float32))

    def _findScoreOverlay(self, img, force_find_overlay):
        # Does a quick check to see if overlay moved
        # If it has, finds and sets the 2d transform of the overlay in the image
        # Sets the transform to None if the overlay is not found

        if self._transform is not None and not force_find_overlay:
            y = self._transform['ty']
            x = self._transform['tx']
            scale = self._transform['scale']
            overlay = img[
                max(0, int(y)):min(int(y+self._template.shape[0]*scale), img.shape[0] - 1),
                max(0, int(x)):min(int(x+self._template.shape[1]*scale), img.shape[1] - 1),
            ]
            if overlay.shape[0] != 0 and overlay.shape[1] != 0:
                template_img = cv2.resize(self._template, (int(overlay.shape[1]), int(overlay.shape[0])))
                res = cv2.matchTemplate(overlay, template_img, cv2.TM_CCOEFF)
                min_val, _, _, _ = cv2.minMaxLoc(res)
                if min_val > 1000000000:
                    self._is_new_overlay = False
                    return

        kp2, des2 = self._detector.detectAndCompute(img, None)
        matches = self._flann.knnMatch(self._des1, des2, k=2)

        # Store all the good matches as per Lowe's ratio test
        good = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good.append(m)

        if len(good) >= self._MIN_MATCH_COUNT:
            src_pts = np.float32([ self._kp1[m.queryIdx].pt for m in good ]).reshape(-1, 1, 2)
            dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1, 1, 2)

            t = cv2.estimateRigidTransform(src_pts, dst_pts, False)
            if t is not None:
                self._transform = {
                    'scale': t[0, 0],
                    'tx': t[0, 2],
                    'ty': t[1, 2],
                }
                self._is_new_overlay = True
                return

        self._transform = None
        self._is_new_overlay = False
        raise NoOverlayFoundException("Not enough matches are found - {}/{}".format(len(good), self._MIN_MATCH_COUNT))

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
        # Crop
        img = img[tl[1]:br[1], tl[0]:br[0]]

        # Scale
        scale = float(self._OCR_HEIGHT) / img.shape[0]
        img = cv2.resize(img, (int(img.shape[1] * scale), int(img.shape[0] * scale)))

        # Threshold
        if white:
            return cv2.morphologyEx(cv2.inRange(img, self._WHITE_LOW, self._WHITE_HIGH), cv2.MORPH_OPEN, self._morph_kernel)
        else:
            return cv2.morphologyEx(cv2.inRange(img, self._BLACK_LOW, self._BLACK_HIGH), cv2.MORPH_OPEN, self._morph_kernel)

    def _parseRawMatchName(self, img):
        config = '--oem 1 --psm 7 --tessdata-dir {} -l eng'.format(TESSDATA_DIR.replace('\\', '/'))
        return pytesseract.image_to_string(255 - img, config=config).strip()

    def _parseDigits(self, img):
        # Crop height to digits
        _, contours, _ = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        top = img.shape[1]
        bottom = 0
        for cnt in contours:
            if cv2.contourArea(cnt) > 50:
                x, y, w, h = cv2.boundingRect(cnt)
                top = min(top, y)
                bottom = max(bottom, y + h)
        height = bottom - top
        if height <= 0:
            return None
        img = img[top:bottom, :]
        # Scale to uniform height
        scale = float(self._OCR_HEIGHT) / height
        img = cv2.resize(img, (int(img.shape[1] * scale), int(img.shape[0] * scale)))

        # Find bounds for each digit
        _, contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        digits = []
        for cnt in filter(lambda c: cv2.contourArea(c) > 100, contours):
            segments = segments_to_numpy([cv2.boundingRect(cnt)])
            extractor = SimpleFeatureExtractor(feature_size=10, stretch=False)
            features = extractor.extract(img, segments)
            x,y,w,h = cv2.boundingRect(cnt)

            if self._save_training_data:
                # Construct clean digit image
                if w > self._OCR_HEIGHT:  # Junk, or more than 1 digit
                    continue

                dim = self._OCR_HEIGHT + 5
                digit_img = np.zeros((dim, dim), np.uint8)
                x2 = dim/2 - w/2
                y2 = dim/2 - h/2
                digit_img[y2:y2+h, x2:x2+w] = 255 - img[y:y+h, x:x+w]

                config = '--oem 1 --psm 8 --tessdata-dir {} -l digits'.format(TESSDATA_DIR.replace('\\', '/'))
                string = pytesseract.image_to_string(
                    Image.fromarray(digit_img),
                    config=config).strip()
                if string and string.isdigit():
                    self._training_data['features'] = np.append(self._training_data['features'], features, axis=0)
                    self._training_data['classes'] = np.append(self._training_data['classes'], [[int(string)]], axis=0)
                return None
            else:
                # Perform classification
                if w > self._OCR_HEIGHT:  # More than 1 digit, fall back to Tesseract
                    logging.warning("Falling back to Tesseract!")
                    padded_img = 255 - cv2.copyMakeBorder(img[y:y+h, x:x+w], 5, 5, 5, 5, cv2.BORDER_CONSTANT, None, (0, 0, 0))
                    config = '--oem 1 --psm 8 --tessdata-dir {} -l digits'.format(TESSDATA_DIR.replace('\\', '/'))
                    string = pytesseract.image_to_string(
                        Image.fromarray(padded_img),
                        config=config).strip()

                    if string and string.isdigit():
                        digits.append((string, segments[0, 0]))
                    continue

                # Use KNN
                digit, _, _, _ = self._knn.findNearest(features, k=3)
                digits.append((int(digit), segments[0, 0]))

        fullNumber = ''
        for digit, _ in sorted(digits, key=lambda x: x[1]):
            fullNumber += str(digit)

        if fullNumber != '':
            return int(fullNumber)

    def _getMatchKey(self, raw_match_name):
        for reg, comp_level, tiebreaker in MATCH_ID_FORMATS:
            match = reg.match(raw_match_name)
            if match:
                # TODO: Make API call to TBA to figure out match key
                if comp_level == 'pm':
                    return 'pm{}'.format(fix_digits(match.group(2)))
                elif comp_level == 'qm':
                    return 'qm{}'.format(fix_digits(match.group(2)))
                elif comp_level == 'ef':
                    return 'ef{}'.format(fix_digits(match.group(2)))  # TODO: not correct
                elif comp_level == 'qf':
                    s, m = QF_BRACKET_ELIM_MAPPING[fix_digits(match.group(2))]
                    if tiebreaker:
                        m = 3
                    return 'qf{}m{}'.format(s, m)
                elif comp_level == 'sf':
                    s, m = SF_BRACKET_ELIM_MAPPING[fix_digits(match.group(2))]
                    if tiebreaker:
                        m = 3
                    return 'sf{}m{}'.format(s, m)
                elif comp_level == 'f':
                    return 'f1m{}'.format(fix_digits(match.group(2)))
                elif comp_level == 'overtimef':
                    return 'f1m{}'.format(3+fix_digits(match.group(2)))
                else:
                    return 'test'
        return None

    def _checkSaturated(self, img, point):
        bgr = img[point[1], point[0], :]
        hsv = colorsys.rgb_to_hsv(float(bgr[2])/255, float(bgr[1])/255, float(bgr[0])/255)
        return hsv[1] > 0.2

    def _matchTemplate(self, img, templates):
        scale = self._transform['scale'] * self._TEMPLATE_SCALE
        best_max_val = 0
        matched_key = None
        for key, template_img in templates.items():
            template_img = cv2.resize(template_img, (int(np.round(template_img.shape[1]*scale)), int(np.round(template_img.shape[0]*scale))))
            res = cv2.matchTemplate(img, template_img, cv2.TM_CCOEFF)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val > best_max_val:
                best_max_val = max_val
                matched_key = key
        return matched_key

    def _drawBox(self, img, box, color):
        cv2.polylines(img, [box], True, color, 2, cv2.LINE_AA)

    def read(self, img, force_find_overlay=False):
        img = cv2.resize(img, (1280, 720))
        self._findScoreOverlay(img, force_find_overlay)
        return self._getMatchDetails(img, force_find_overlay)

    def train(self, img, force_find_overlay=False):
        img = cv2.resize(img, (1280, 720))
        self._findScoreOverlay(img, force_find_overlay)
        self._getMatchDetails(img, force_find_overlay)

    def saveTrainingData(self):
        with open('training_data.pkl', 'wb') as output:
            pickle.dump(self._training_data, output, pickle.HIGHEST_PROTOCOL)

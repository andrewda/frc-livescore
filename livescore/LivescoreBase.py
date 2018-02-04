import colorsys
import cv2
import numpy as np
import cPickle as pickle
import logging
from PIL import Image
import pkg_resources
import pytesseract

from simpleocr_utils.segmentation import segments_to_numpy
from simpleocr_utils.feature_extraction import SimpleFeatureExtractor


class NoOverlayFoundException(Exception):
    pass


class LivescoreBase(object):
    def __init__(self, game_year, debug=False, save_training_data=False, training_data=None):
        self._debug = debug
        self._save_training_data = save_training_data

        self._WHITE_LOW = np.array([120, 120, 120])
        self._WHITE_HIGH = np.array([255, 255, 255])

        self._BLACK_LOW = np.array([0, 0, 0])
        self._BLACK_HIGH = np.array([135, 135, 155])

        self._OCR_HEIGHT = 64  # Do all OCR at this size

        self._transform = None  # scale, tx, ty

        # Setup feature detector and matcher
        self._detector = cv2.xfeatures2d.SURF_create()

        FLANN_INDEX_KDTREE = 0
        index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        search_params = dict(checks = 50)
        self._flann = cv2.FlannBasedMatcher(index_params, search_params)

        self._MIN_MATCH_COUNT = 10

        # Compute score overlay keypoints and descriptors
        self._TEMPLATE_SCALE = 0.5  # lower is faster
        template = cv2.imread(
            pkg_resources.resource_filename(__name__, 'templates') + \
            '/score_overlay_{}.png'.format(game_year))
        shape = template.shape
        template = cv2.resize(template, (
            np.int32(np.round(shape[1] * self._TEMPLATE_SCALE)),
            np.int32(np.round(shape[0] * self._TEMPLATE_SCALE))
        ))
        self._kp1, self._des1 = self._detector.detectAndCompute(template, None)

        # For saving training data
        self._training_data = {
            'features': np.ndarray((0, 100)),
            'classes': np.ndarray((0, 1)),
        }

        # Train classifier
        if training_data is None:
            with open(pkg_resources.resource_filename(__name__, 'training_data') + '/digits.pkl', "rb") as f:
                training_data = pickle.load(f)
        else:
            with open(training_data, "rb") as f:
                training_data = pickle.load(f)
        self._knn = cv2.ml.KNearest_create()
        self._knn.train(training_data['features'].astype(np.float32), cv2.ml.ROW_SAMPLE, training_data['classes'].astype(np.float32))

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

        if len(good) > self._MIN_MATCH_COUNT:
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

        self._transform = None
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
            return cv2.inRange(img, self._WHITE_LOW, self._WHITE_HIGH)
        else:
            return cv2.inRange(img, self._BLACK_LOW, self._BLACK_HIGH)

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
        for cnt in contours:
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
                digit_img[y2:y2+h, x2:x2+w] = img[y:y+h, x:x+w]

                config = '--psm 8 -c tessedit_char_whitelist=1234567890'
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
                    padded_img = cv2.copyMakeBorder(img[y:y+h, x:x+w], 5, 5, 5, 5, cv2.BORDER_CONSTANT, None, (0, 0, 0))
                    config = '--psm 8 -c tessedit_char_whitelist=1234567890'
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

    def _checkSaturated(self, img, point):
        bgr = img[point[1], point[0], :]
        hsv = colorsys.rgb_to_hsv(float(bgr[2])/255, float(bgr[1])/255, float(bgr[0])/255)
        return hsv[1] > 0.2

    def _drawBox(self, img, box, color):
        cv2.polylines(img, [box], True, color, 2, cv2.LINE_AA)

    def read(self, img):
        img = cv2.resize(img, (1280, 720))

        if self._transform is None:
            self._findScoreOverlay(img)

        match_details = self._getMatchDetails(img)
        if match_details is None:
            self._findScoreOverlay(img)
            match_details = self._getMatchDetails(img)

        return match_details

    def train(self, img):
        img = cv2.resize(img, (1280, 720))

        if self._transform is None:
            self._findScoreOverlay(img)

        self._getMatchDetails(img)

    def saveTrainingData(self):
        with open('training_data.pkl', 'wb') as output:
            pickle.dump(self._training_data, output, pickle.HIGHEST_PROTOCOL)

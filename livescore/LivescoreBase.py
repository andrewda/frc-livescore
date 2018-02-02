import cv2
import numpy as np
from PIL import Image
import pkg_resources
import pytesseract


class LivescoreBase(object):
    def __init__(self, game_year, debug=False):
        self._debug = debug
        self._local_path = pkg_resources.resource_filename(__name__, 'tessdata')

        self._WHITE_LOW = np.array([185, 185, 185])
        self._WHITE_HIGH = np.array([255, 255, 255])

        self._BLACK_LOW = np.array([0, 0, 0])
        self._BLACK_HIGH = np.array([135, 135, 155])

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

        print("Not enough matches are found - {}/{}".format(len(good), self._MIN_MATCH_COUNT))
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
            return cv2.inRange(cropped, self._WHITE_LOW, self._WHITE_HIGH)
        else:
            return cv2.inRange(cropped, self._BLACK_LOW, self._BLACK_HIGH)

    def _parseDigits(self, img, use_trained_font=True):
        config = '--psm 8 -c tessedit_char_whitelist=1234567890'
        if use_trained_font:
            config += ' --tessdata-dir {}'.format(self._local_path.replace('\\', '/'))
        string = pytesseract.image_to_string(
            Image.fromarray(img),
            config=config).strip()
        if string and string.isdigit():
            return int(string)
        else:
            return None

    def _drawBox(self, img, box, color):
        cv2.polylines(img, [box], True, color, 2, cv2.LINE_AA)

import cv2
import numpy as np
import pytesseract
import re
import imutils
import pkg_resources
from PIL import Image


class Livescore:
    def __init__(self, options={}):
        template_path = pkg_resources.resource_filename(__name__, 'templates')

        templates = {
            'scoreboard': template_path + '/scoreboard.png',
            'scores': template_path + '/scores.png',
            'time': template_path + '/time.png',
            'top': template_path + '/top.png'
        }

        if 'scoreboard' not in options:
            self.TEMPLATE_SCOREBOARD = cv2.imread(templates['scoreboard'], 0)
        else:
            self.TEMPLATE_SCOREBOARD = options['scoreboard']

        if 'scores' not in options:
            self.TEMPLATE_SCORES = cv2.imread(templates['scores'], 0)
        else:
            self.TEMPLATE_SCORES = options['scores']

        if 'time' not in options:
            self.TEMPLATE_TIME = cv2.imread(templates['time'], 0)
        else:
            self.TEMPLATE_TIME = options['time']

        if 'top' not in options:
            self.TEMPLATE_TOP = cv2.imread(templates['top'], 0)
        else:
            self.TEMPLATE_TOP = options['top']

        self.WHITE_LOW = np.array([200, 200, 200])
        self.WHITE_HIGH = np.array([255, 255, 255])

        self.BLACK_LOW = np.array([0, 0, 0])
        self.BLACK_HIGH = np.array([105, 105, 135])

    def matchTemplate(self, img, template):
        res = cv2.matchTemplate(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY),
                                template,
                                cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc
        bottom_right = (top_left[0] + template.shape[1],
                        top_left[1] + template.shape[0])

        return top_left, bottom_right

    def getScoreboard(self, img):
        template_width = self.TEMPLATE_SCOREBOARD.shape[1]
        img_width = img.shape[1]
        template = imutils.resize(self.TEMPLATE_SCOREBOARD,
                                  width=int(template_width/1280.0*img_width))
        top_left, bottom_right = self.matchTemplate(img, template)

        return img[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]

    def getTopBar(self, img):
        template_width = self.TEMPLATE_TOP.shape[1]
        img_width = img.shape[1]
        template = imutils.resize(self.TEMPLATE_TOP,
                                  width=int(template_width/1280.0*img_width))
        top_left, bottom_right = self.matchTemplate(img, template)

        return img[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]

    def getTimeArea(self, img):
        template_width = self.TEMPLATE_TIME.shape[1]
        img_width = img.shape[1]
        template = imutils.resize(self.TEMPLATE_TIME,
                                  width=int(template_width/1280.0*img_width))
        top_left, bottom_right = self.matchTemplate(img, template)

        located = img[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
        h, w = located.shape[:2]

        return located[int(h*0.16):int(h*0.84), int(w*0.42):int(w*0.58)]

    def getScoreArea(self, img):
        template_width = self.TEMPLATE_SCORES.shape[1]
        img_width = img.shape[1]
        template = imutils.resize(self.TEMPLATE_SCORES,
                                  width=int(template_width/1280.0*img_width))
        top_left, bottom_right = self.matchTemplate(img, template)

        return img[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]

    def getRedScoreArea(self, img):
        score_area = self.getScoreArea(img)
        return score_area[:, 0:score_area.shape[1]/2]

    def getBlueScoreArea(self, img):
        score_area = self.getScoreArea(img)
        return score_area[:, score_area.shape[1]/2:score_area.shape[1]]

    def read(self, img):
        scoreboard = self.getScoreboard(img)

        top_bar = self.getTopBar(scoreboard)
        long_match_string = pytesseract.image_to_string(
                                                Image.fromarray(top_bar),
                                                config='--psm 7').strip()
        m = re.search('([a-zA-z]+) ([1-9]+)( of ...?)?', long_match_string)
        if m is not None:
            match_string = m.group(1) + ' ' + m.group(2)
        else:
            match_string = ''

        time_remaining = self.getTimeArea(scoreboard)
        red_cropped = self.getRedScoreArea(scoreboard)
        blue_cropped = self.getBlueScoreArea(scoreboard)

        time_remaining = cv2.inRange(time_remaining,
                                     self.BLACK_LOW,
                                     self.BLACK_HIGH)
        blue_cropped = cv2.inRange(blue_cropped,
                                   self.WHITE_LOW,
                                   self.WHITE_HIGH)
        red_cropped = cv2.inRange(red_cropped,
                                  self.WHITE_LOW,
                                  self.WHITE_HIGH)

        time_remaining_string = pytesseract.image_to_string(
                                            Image.fromarray(time_remaining),
                                            config='--psm 8 digits').strip()
        blue_score_string = pytesseract.image_to_string(
                                            Image.fromarray(blue_cropped),
                                            config='--psm 8 digits').strip()
        red_score_string = pytesseract.image_to_string(
                                            Image.fromarray(red_cropped),
                                            config='--psm 8 digits').strip()

        return {
            'match': match_string,
            'time': int(time_remaining_string),
            'red': {
                'score': int(red_score_string)
            },
            'blue': {
                'score': int(blue_score_string)
            }
        }

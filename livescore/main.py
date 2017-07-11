import cv2
import numpy as np
import pytesseract
import re
import imutils
import pkg_resources
from PIL import Image

from details import Alliance, OngoingMatchDetails


class Livescore:
    def __init__(self, options={}):
        local_path = pkg_resources.resource_filename(__name__, 'tessdata')
        template_path = pkg_resources.resource_filename(__name__, 'templates')

        templates = {
            'scoreboard': template_path + '/scoreboard.png',
            'scores': template_path + '/scores.png',
            'time': template_path + '/time.png',
            'top': template_path + '/top.png',
            'red_teams': template_path + '/red_teams.png'
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

        if 'red_teams' not in options and 'blue_teams' not in options:
            self.TEMPLATE_RED_TEAMS = cv2.imread(templates['red_teams'], 0)
            self.TEMPLATE_BLUE_TEAMS = cv2.flip(self.TEMPLATE_RED_TEAMS, 1)
        elif 'blue_teams' not in options:  # 'red_teams' in options
            self.TEMPLATE_RED_TEAMS = options['red_teams']
            self.TEMPLATE_BLUE_TEAMS = cv2.flip(self.TEMPLATE_RED_TEAMS, 1)
        elif 'red_teams' not in options:  # 'blue_teams' in options
            self.TEMPLATE_BLUE_TEAMS = options['blue_teams']
            self.TEMPLATE_RED_TEAMS = cv2.flip(self.TEMPLATE_BLUE_TEAMS, 1)
        else: # both in options
            self.TEMPLATE_RED_TEAMS = options['red_teams']
            self.TEMPLATE_BLUE_TEAMS = options['blue_teams']

        self.WHITE_LOW = np.array([185, 185, 185])
        self.WHITE_HIGH = np.array([255, 255, 255])

        self.BLACK_LOW = np.array([0, 0, 0])
        self.BLACK_HIGH = np.array([135, 135, 155])

        self.local_path = local_path

    def matchTemplate(self, img, template):
        res = cv2.matchTemplate(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY),
                                template,
                                cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc
        bottom_right = (top_left[0] + template.shape[1],
                        top_left[1] + template.shape[0])

        return top_left, bottom_right

    def getArea(self, img, template_img):
        template_width = template_img.shape[1]
        img_width = img.shape[1]
        template = imutils.resize(template_img,
                                  width=int(template_width/1280.0*img_width))
        top_left, bottom_right = self.matchTemplate(img, template)

        return img[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]

    def getScoreboard(self, img):
        return self.getArea(img, self.TEMPLATE_SCOREBOARD)

    def getTopBar(self, img):
        located = self.getArea(img, self.TEMPLATE_TOP)
        h, w = located.shape[:2]

        return located[:, int(w*0.125):int(w*0.5)]

    def getTimeArea(self, img):
        located = self.getArea(img, self.TEMPLATE_TIME)
        h, w = located.shape[:2]

        return located[int(h*0.16):int(h*0.84), int(w*0.42):int(w*0.58)]

    def getScoreArea(self, img):
        return self.getArea(img, self.TEMPLATE_SCORES)

    def getRedScoreArea(self, img):
        score_area = self.getScoreArea(img)
        return score_area[:, int((score_area.shape[1]/2)*0.05):int((score_area.shape[1]/2)*0.95)]

    def getBlueScoreArea(self, img):
        score_area = self.getScoreArea(img)
        return score_area[:, int((score_area.shape[1]/2)*1.05):int(score_area.shape[1]*0.95)]

    def getRedTeamsArea(self, img):
        area = self.getArea(img, self.TEMPLATE_RED_TEAMS)
        team_height = int(area.shape[0] / 3)
        return [area[team_height * i:team_height * (i + 1), int(area.shape[1] * 0.2):int(area.shape[1] * 0.9)] for i in range(3)]

    def getBlueTeamsArea(self, img):
        area =  self.getArea(img, self.TEMPLATE_BLUE_TEAMS)
        team_height = int(area.shape[0] / 3)
        return [area[team_height * i:team_height * (i + 1), int(area.shape[1] * 0.1):int(area.shape[1] * 0.8)] for i in range(3)]

    def read(self, img):
        scoreboard = self.getScoreboard(img)

        top_cropped = self.getTopBar(scoreboard)
        time_cropped = self.getTimeArea(scoreboard)
        red_score_cropped = self.getRedScoreArea(scoreboard)
        blue_score_cropped = self.getBlueScoreArea(scoreboard)
        red_teams_cropped = self.getRedTeamsArea(scoreboard)
        blue_teams_cropped = self.getBlueTeamsArea(scoreboard)

        top_cropped = cv2.inRange(top_cropped,
                                  self.BLACK_LOW,
                                  self.BLACK_HIGH)
        time_cropped = cv2.inRange(time_cropped,
                                   self.BLACK_LOW,
                                   self.BLACK_HIGH)
        blue_score_cropped = cv2.inRange(blue_score_cropped,
                                         self.WHITE_LOW,
                                         self.WHITE_HIGH)
        red_score_cropped = cv2.inRange(red_score_cropped,
                                        self.WHITE_LOW,
                                        self.WHITE_HIGH)
        for i in range(3):
            blue_teams_cropped[i] = cv2.inRange(blue_teams_cropped[i],
                                                self.BLACK_LOW,
                                                self.BLACK_HIGH)

        for i in range(3):
            red_teams_cropped[i] = cv2.inRange(red_teams_cropped[i],
                                               self.BLACK_LOW,
                                               self.BLACK_HIGH)

        long_match = pytesseract.image_to_string(Image.fromarray(top_cropped),
                                                 config='--psm 7').strip()
        match = None
        m = re.search('([a-zA-z]+) ([1-9]+)( of ...?)?', long_match)
        if m is not None:
            match = m.group(1) + ' ' + m.group(2)

        config = '--psm 8 -l consolas --tessdata-dir {} \
                  -c tessedit_char_whitelist=1234567890 digits'.format(self.local_path)

        time_remaining = pytesseract.image_to_string(
                                            Image.fromarray(time_cropped),
                                            config=config).strip()

        blue_score = pytesseract.image_to_string(
                                            Image.fromarray(blue_score_cropped),
                                            config=config).strip()

        red_score = pytesseract.image_to_string(
                                            Image.fromarray(red_score_cropped),
                                            config=config).strip()

        blue_teams = [pytesseract.image_to_string(
                      Image.fromarray(team),
                      config=config).strip()
                      for team in blue_teams_cropped]

        red_teams = [pytesseract.image_to_string(
                     Image.fromarray(team),
                     config=config).strip()
                     for team in red_teams_cropped]


        return OngoingMatchDetails(match=match,
                                   time=time_remaining,
                                   red=Alliance(score=red_score, teams=red_teams),
                                   blue=Alliance(score=blue_score, teams=blue_teams))

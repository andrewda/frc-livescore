import os
import sys
import json
import cv2

from livescore import Livescore

# Initialize new Livescore instance
frc = Livescore()

error = False

with open('values.json') as data:
    values = json.load(data)

# Read all images from the ./images/ directory
for f in os.listdir('./images'):
    # Images named in format: `red_blue_time.png`
    expected_values = values[f]

    expected_red_score = expected_values['score']['red']
    expected_blue_score = expected_values['score']['blue']
    expected_red_teams = expected_values['teams']['red']
    expected_blue_teams = expected_values['teams']['blue']
    expected_time = expected_values['time']
    expected_match = expected_values['match']

    # Read the image with OpenCV
    image = cv2.imread('./images/' + f)

    # Get score data
    data = frc.read(image)

    if data.time == expected_time and \
       data.red.score == expected_red_score and \
       data.blue.score == expected_blue_score and \
       data.red.teams == expected_red_teams and \
       data.blue.teams == expected_blue_teams:
        print('{} processing success'.format(f))
    else:
        print('{} processing error'.format(f))
        print('\tExpected: {}'.format([expected_red_score,
                                       expected_blue_score,
                                       expected_red_teams,
                                       expected_blue_teams,
                                       expected_time,
                                       expected_match]))
        print('\tReceived: {}'.format([data.red.score,
                                       data.blue.score,
                                       data.red.teams,
                                       data.blue.teams,
                                       data.time,
                                       data.match]))
        error = True

if error:
    sys.exit(1)

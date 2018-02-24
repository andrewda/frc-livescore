import difflib
import os
import sys
import yaml
import cv2

from livescore import Livescore2017

# Initialize new Livescore instance
frc = Livescore2017()

error = False

with open('data/2017.yml') as data:
    values = yaml.load(data)

# Read all images from the ./images/2017 directory
for f in os.listdir('./images/2017'):
    # Images named in format: `red_blue_time.png`
    expected_value = values[f]

    # Read the image with OpenCV
    image = cv2.imread('./images/2017/' + f)

    # Get score data
    data = frc.read(image, force_find_overlay=True)

    if str(data) != expected_value:
        error = True

        d = difflib.Differ()
        diff = '\n'.join(d.compare(expected_value.splitlines(), str(data).splitlines()))
        print('[2017] Error Processing: {}\nDiff:\n{}'.format(f, diff))
    else:
        print('[2017] {} Passed'.format(f))

if error:
    sys.exit(1)

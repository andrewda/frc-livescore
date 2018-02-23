import os
import sys
import yaml
import cv2

from livescore import Livescore2018

# Initialize new Livescore instance
frc = Livescore2018()

error = False

with open('data/2018.yml') as data:
    values = yaml.load(data)

# Read all images from the ./images/2018 directory
for f in os.listdir('./images/2018'):
    # Images named in format: `red_blue_time.png`
    expected_value = values[f]

    # Read the image with OpenCV
    image = cv2.imread('./images/2018/' + f)

    # Get score data
    data = frc.read(image)

    if str(data) != expected_value:
        error = True
        print('Error processing {}\nExpected:\n{}\n\nReceived:\n{}'.format(f, expected_value, data))
    else:
        print('{} Passed'.format(f))

if error:
    sys.exit(1)

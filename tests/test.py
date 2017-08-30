from livescore import Livescore
import os
import sys
import cv2

# Initialize new Livescore instance
frc = Livescore()

error = False

# Read all images from the ./images/ directory
for f in os.listdir('./images'):
    # Images named in format: `red_blue_time.png`
    values = f.replace('.png', '').split('_')

    expected_red = int(values[0])
    expected_blue = int(values[1])
    expected_time = int(values[2])

    # Read the image with OpenCV
    image = cv2.imread('./images/' + f)

    # Get score data
    data = frc.read(image)

    if data.red.score == expected_red and data.blue.score == expected_blue and data.time == expected_time:
        print '{} processing success'.format(f)
    else:
        print 'File: {}'.format(f)
        print 'Expected: {}'.format([expected_red,
                                     expected_blue,
                                     expected_time])
        print 'Received: {}'.format([data.red.score,
                                     data.blue.score,
                                     data.time])
        error = True

if error:
    sys.exit(1)

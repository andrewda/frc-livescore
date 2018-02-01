from livescore import Livescore
import os
import cv2

# Initialize new Livescore instance
frc = Livescore(debug=True)

# Read all images from the ./scenes/ directory
for f in os.listdir('./scenes'):
    # Read the image with OpenCV
    image = cv2.imread('./scenes/' + f)

    # Get score data
    data = frc.read(image)

    print('{}: Match: {}, Time: {}, Red: {}, Blue: {}'.format(
        f, data.match, data.time, data.red.score, data.blue.score))

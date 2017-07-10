from livescore import Livescore
import os
import cv2

# Initialize new Livescore instance
frc = Livescore()

# Read all images from the ./scenes/ directory
for f in os.listdir('./scenes'):
    # Read the image with OpenCV
    image = cv2.imread('./scenes/' + f)

    # Get score data
    data = frc.read(image)

    print('Red {0} : {2} : {1} Blue'.format(data.red.score,
                                            data.blue.score,
                                            data.time))

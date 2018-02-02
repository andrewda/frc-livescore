from livescore import Livescore2017
import os
import cv2

# Initialize new Livescore instance
frc = Livescore2017(debug=True)

# Read all images from the ./scenes/ directory
for f in os.listdir('./scenes'):
    # Read the image with OpenCV
    image = cv2.imread('./scenes/' + f)

    # Get score data
    data = frc.read(image)

    print('{}: Match: {}, Time: {}, Red: {}, Blue: {}, Red Fuel: {} + {}/9, Blue Fuel: {} + {}/9'.format(
        f,
        data.match,
        data.time,
        data.red.score,
        data.blue.score,
        data.red.fuel_score,
        data.red.fuel_count,
        data.blue.fuel_score,
        data.blue.fuel_count,
    ))

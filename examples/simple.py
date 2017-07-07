from livescore import Livescore
import os
import cv2

frc = Livescore()

for f in os.listdir('./scenes'):
    image = cv2.imread('./scenes/' + f)
    data = frc.read(image)

    print('Red {0} : {2} : {1} Blue'.format(data['red']['score'],
                                            data['blue']['score'],
                                            data['time']))

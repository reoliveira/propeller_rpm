import numpy as np
import cv2
import argparse

def get_color_bounds():
    return ([10, 10, 100], [80, 80, 200])

def weigh_pixels(pixels) :
    totalx = 0
    totaly = 0
    count = 0

    if pixels.size <= 0: return (0,0)

    for pixel in np.nditer(pixels, flags = ['external_loop'], order = 'C'):
        totalx += pixel[0]
        totaly += pixel[1]
        count += 1

    return (totalx/count, totaly/count)

# retrieve arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help = "path to the video")
args = vars(ap.parse_args())

cap = cv2.VideoCapture(args["video"])

boundaries = get_color_bounds()
lower = np.array(boundaries[0], dtype = "uint8")
upper = np.array(boundaries[1], dtype = "uint8")

while(cap.isOpened()):
    ret, frame = cap.read()

    # split the target color from the rest of the image
    binary = cv2.inRange(frame, lower, upper)
    # locations of all target color pixels
    targets = np.transpose(np.where(binary>0))
    # "centre of mass" of the targets
    centre = weigh_pixels(targets)
    print centre

    cv2.imshow('frame', binary)
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

import numpy as np
import cv2
import argparse
np.set_printoptions(threshold=np.nan)

def get_color_bounds(color) :
    if color == "red":
        return ([17, 15, 100], [50, 56, 200])

# retrieve arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help = "path to the video")
ap.add_argument("-c", "--color", help = "the color to filter: red")
ap.add_argument("-o", "--original", help = "display original")
args = vars(ap.parse_args())

cap = cv2.VideoCapture(args["video"])

boundaries = get_color_bounds(args["color"])
lower = np.array(boundaries[0], dtype = "uint8")
upper = np.array(boundaries[1], dtype = "uint8")

while(cap.isOpened()):
    ret, frame = cap.read()

    binary = cv2.inRange(frame, lower, upper)

    if args["original"] == "true":
        cv2.imshow('frame', frame)
    else:
        cv2.imshow('frame', binary)
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

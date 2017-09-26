import numpy as np
import cv2
import argparse
from Queue import *

WINDOW_SIZE = 100
MARKER_SIZE = 5
MILESTONES = [.25, .5, .75, 1.0]

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

def calculate_origin(centre, past_centres):
    if past_centres.full():
        past_centres.get(False)
    past_centres.put(centre)

    totalx = 0
    totaly = 0
    count = 0
    for (x,y) in list(past_centres.queue):
        totalx += x
        totaly += y
        count += 1

    return (totalx/count, totaly/count)

def update_frame(frame, centre, origin):
    print_blob(frame, origin)
    print_blob(frame, centre)

def print_blob(frame, point):
    for x in range(point[0]-MARKER_SIZE, point[0]+MARKER_SIZE):
        if x >= 0 and x<width:
            for y in range(point[1]-MARKER_SIZE, point[1]+MARKER_SIZE):
                if y>=0 and y<height:
                    frame[x,y] = 100


# ------------------- MAIN -------------------
# retrieve arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help = "path to the video")
ap.add_argument("-f", "--fps", help = "fps of the video")
args = vars(ap.parse_args())

cap = cv2.VideoCapture(args["video"])

boundaries = get_color_bounds()
lower = np.array(boundaries[0], dtype = "uint8")
upper = np.array(boundaries[1], dtype = "uint8")

origin_q = Queue(maxsize=WINDOW_SIZE)

ret,frame = cap.read()
height, width, channels = frame.shape

num_milestones = 0
while(cap.isOpened()):
    next_milestone = MILESTONES[num_milestones % len(MILESTONES)]

    ret, frame = cap.read()
    # split the target color from the rest of the image
    binary = cv2.inRange(frame, lower, upper)
    # locations of all target color pixels
    targets = np.transpose(np.where(binary>0))
    # "centre of mass" of the targets
    centre = weigh_pixels(targets)
    # calculate an approximate origin using the last WINDOW_SIZE centre points
    origin = calculate_origin(centre, origin_q)

    # now use position and origin to guess angle
    # 1) calculate angle wrt origin
    # 2) see if it has passed the next "milestone" which is a portion of a turn
    # 3) use milestones to count turns and compare against fps for rpm

    # print the centre point and approximated origin on the frame
    update_frame(binary, centre, origin)
    cv2.imshow('frame', binary)
    if cv2.waitKey(15) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

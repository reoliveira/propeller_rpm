import numpy as np
import cv2
import argparse
from Queue import *

WINDOW_SIZE = 100
MARKER_SIZE = 5
MILESTONES = [.25, .5, .75, 1.0]

def get_color_bounds():
    # BGR order
    return ([10, 10, 100], [80, 80, 200])

def weigh_pixels(pixels) :
    row = 0
    col = 0
    count = 0

    if pixels.size <= 0: return (height/2,width/2) # (row, col): height = #rows, width = #cols

    for pixel in np.nditer(pixels, flags = ['external_loop'], order = 'C'):
        row += pixel[0]
        col += pixel[1]
        count += 1

    return (row/count, col/count)

def calculate_origin(centre, past_centres):
    if past_centres.full():
        past_centres.get(False)
    past_centres.put(centre)

    total_row = 0
    total_col = 0
    count = 0
    for (row,col) in list(past_centres.queue):
        total_row += row
        total_col += col
        count += 1

    return (total_row/count, total_col/count)

def update_frame(frame, centre, origin):
    print_blob(frame, origin)
    print_blob(frame, centre)

def print_blob(frame, point):
    for r in range(point[0]-MARKER_SIZE, point[0]+MARKER_SIZE):
        if r >= 0 and r < height:
            for c in range(point[1]-MARKER_SIZE, point[1]+MARKER_SIZE):
                if c >= 0 and c < width:
                    frame[r,c] = 100 # something weird is going on here


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

ret, frame = cap.read()
height, width, channels = frame.shape

origin_q = Queue(maxsize=WINDOW_SIZE)
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

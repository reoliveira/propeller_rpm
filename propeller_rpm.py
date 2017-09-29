import numpy as np
import cv2
import argparse
from Queue import *

WINDOW_SIZE = 100
MARKER_SIZE = 5

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
                    frame[r,c] = [0,255,0]

def check_quadrent(point):
    # point is (row,col) = (y,x)
    y = point[0]
    x = point[1]

    if x >= 0:
        if y >=0:
            return 1
        else:
            return 4
    else:
        if y >=0:
            return 2
        else:
            return 3


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
fps = int(args["fps"])

origin_q = Queue(maxsize=WINDOW_SIZE)
milestones = 0
frames = 0
while(cap.isOpened()):
    ret, frame = cap.read()
    # split out the target color
    binary = cv2.inRange(frame, lower, upper)
    targets = np.transpose(np.where(binary>0))
    # "centre of mass" the target color for tracking
    centre = weigh_pixels(targets)
    origin = calculate_origin(centre, origin_q)

    # now use position and origin to check quadrent, passing all 4 quadrents counts as one rotation
    vec = (centre[0] - origin[0], centre[1] - origin[1])
    quadrent = check_quadrent(vec)

    # this assumes we start in quadrent 1, or that the extra partial rotation until it "catches up" has little effect
    if quadrent != (milestones % 4)+1:
        milestones += 1
    frames += 1 # constraint here that sys.maxint / fps does not exceed the number of seconds in the video

    # calculation currently heavily affected if there are a bunch of frames without movement, as "frames" is
    # inc but "milestones" is not. Could do an impl where it only looks at the last x number
    # e.g. maybe a queue of milestones and their respective frame #?
    rpm = (float(milestones) / (4*frames)) * fps * 60 # int division problems happening here

    # print the centre point and approximated origin on the frame
    update_frame(frame, centre, origin)
    cv2.putText(frame,"rpm:%.2f" % rpm, (0,100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0))
    cv2.imshow('frame', frame)
    if cv2.waitKey(15) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

import numpy as np
import cv2
import argparse
from Queue import *

WINDOW_SIZE = 100 # num points to use to guess origin
MARKER_SIZE = 5 # size of point to plot on screen
AVG_WINDOW = 3 # the number of seconds to consider when determining instantaneous rpm
SEC_PER_MIN = 60

# output: BGR color bounds for the pixels of interest
def get_color_bounds():
    return ([50, 50, 100], [150, 150, 200])

# input: a set of pixel coordinates
# output: a point that is the average row and column of the input pixels
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

# input: a list of pixel locations
# output: an estimation of the origin of those pixels
# requires: the pixels are reasonably distributed around the origin
def calculate_origin(points):
    total_row = 0
    total_col = 0
    count = 0
    for (row,col) in list(points.queue):
        total_row += row
        total_col += col
        count += 1

    return (total_row/count, total_col/count)

# input: a current position and origin to plot and a frame to plot them on
# result: marks the two points given on the frame
def update_frame(frame, position, origin):
    print_point(frame, origin, [0,0,255])
    print_point(frame, position, [0,255,0])

# prints the point on the frame with the given color
def print_point(frame, point, color):
    for r in range(point[0]-MARKER_SIZE, point[0]+MARKER_SIZE):
        if r >= 0 and r < height:
            for c in range(point[1]-MARKER_SIZE, point[1]+MARKER_SIZE):
                if c >= 0 and c < width:
                    frame[r,c] = color

# input: point
# output: the quadrant of the point
def check_quadrant(point):
    # point is (row,col) = (y,x)
    y = point[0]
    x = point[1]

    if x >= 0:
        if y <=0: # y increases towards bottom
            return 1
        else:
            return 4
    else:
        if y <=0:
            return 2
        else:
            return 3

# sums the points in a queue
def sum_q(queue):
    sum = 0
    for val in list(queue.queue):
        sum += val

    return sum

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
rotations = 0
cur_quad = 0
frames = 0
frame_q = Queue(maxsize=fps * AVG_WINDOW) # use last 5 seconds to determine current rpm
max_rpm = 0

video_path = args["video"].split("/")
video_name = video_path[len(video_path) - 1].split(".")[0] + "_rpm.avi"
print(video_name)

out = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'XVID'), fps, (width,height))
while(cap.isOpened()):
    ret, frame = cap.read()
    if not ret: break

    frames += 1 # constraint here that sys.maxint / fps does not exceed the number of frames in the video
    if frame_q.full():
        frame_q.get(False)
    if origin_q.full():
        origin_q.get(False)

    # split out the target color
    binary = cv2.inRange(frame, lower, upper)
    targets = np.transpose(np.where(binary>0))
    avg_location = weigh_pixels(targets)

    origin_q.put(avg_location)
    origin = calculate_origin(origin_q)

    # now use position and origin to check quadrant, passing all 4 quadrants counts as one rotation
    vec = (avg_location[0] - origin[0], avg_location[1] - origin[1])
    quad = check_quadrant(vec)

    rotated = 0
    if quad == 1 :
        if cur_quad == 4:
            rotated = 1
    cur_quad = quad

    rotations += rotated
    frame_q.put(rotated)

    cur_rpm = (float(sum_q(frame_q)) / frame_q.qsize()) * fps * SEC_PER_MIN
    avg_rpm = (float(rotations) / frames) * fps * SEC_PER_MIN
    if cur_rpm > max_rpm:
        max_rpm = cur_rpm

    # print the centre point and approximated origin on the frame
    update_frame(frame, avg_location, origin)
    cv2.putText(frame,"avg rpm:%.2f" % avg_rpm, (0,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0))
    cv2.putText(frame,"max rpm:%.2f" % max_rpm, (0,100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255))
    cv2.putText(frame,"current rpm:%.2f" % cur_rpm, (0,150), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,0,0))
    cv2.imshow('frame', frame)
    out.write(frame)

    if cv2.waitKey(15) & 0xFF == ord('q'):
        break

print("frames read: %d" % frames)
cap.release()
out.release()
cv2.destroyAllWindows()

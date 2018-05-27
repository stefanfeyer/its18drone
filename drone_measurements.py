import math

# constants redundant... hmmm
W, H = 640, 360

# distance measurements:
# person (moritz) standing away from drone in different distances -> object height
# 5m: 0.39
# 7.5m: 0.49
# 10m: 0.7

# distance * object_height = F
# this F should be constant for constant real object height (~averaged human)
# we obtain 3.7 as average over these samples
F = 3.7

def distance(object_height):
    try:
        return F / object_height
    except ZeroDivisionError:
        return -1

FOV = 62
def sign(x):
    return -1.0 if x < 0 else 1.0
def angle(cx, object_distance):
    # width we can see at the object distance (in meters)
    fov_width = math.tan(math.radians(0.5 * FOV)) * 2*object_distance
    # distance of object center from screen center (in pixels)
    pixel_delta = cx - 0.5 * W
    # distance of object center from screen center (in [0;0.5] on both sides)
    rel_delta = abs(pixel_delta) / W
    movement_width = rel_delta * fov_width
    return math.degrees(math.atan(movement_width / object_distance)) * sign(pixel_delta)



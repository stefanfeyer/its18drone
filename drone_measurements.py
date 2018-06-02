import math

# constants redundant... hmmm
W, H = 640, 360

# distance measurements:
# person (moritz) standing away from drone in different distances -> relative object height on imag on image
#  5.0m: 0.39
#  7.5m: 0.49
# 10.0m: 0.70

# distance * object_height = F
# this F should be constant for a real object with a constant height (~averaged human)
# we obtain 3.7 as average over these samples
F = 3.7

def measure_distance(object_height):
    # returns the distance of an (human) object
    # object_height is relative height of object on image
    # return -1 if object_height zero is given

    try:
        return F / object_height
    except ZeroDivisionError:
        return -1

# horizontal field of view of camera (in degrees)
# measured manually
FOV = 62

def sign(x):
    return -1.0 if x < 0 else 1.0
def measure_angle(cx, object_distance):
    # returns the angle (in degrees) that an object (center x-coordinate on image, object distance) is from us
    # to the left are negative angles, to the right positive ones

    # width we can see at the object distance (in meters)
    fov_width = math.tan(math.radians(0.5 * FOV)) * 2*object_distance
    # distance of object center from screen center (in pixels)
    pixel_delta = cx - 0.5 * W
    # distance of object center from screen center (in [0;0.5] on both sides)
    rel_delta = abs(pixel_delta) / W
    movement_width = rel_delta * fov_width
    return math.degrees(math.atan(movement_width / object_distance)) * sign(pixel_delta)


import math
import pygame

# to control the drone with the API, we can set a vector that describes
# the drones movement along the different axes
# we call these vectors states here

# sometimes, entries are empty (None), that means that we don't want to
# set the movement along this axis because we are only interesting in one particular one

# indices of movement axes in state vectors
# first entry is boolean. True when moving, False when hovering
I_MOVE = 0
# others are floats from -1 to 1
# 1 is maximum speed move right, -1 maximum speed move left, 0 is no movement along this axis
I_MOVE_RIGHT = 1
I_MOVE_BACKWARD = 2
I_MOVE_UP = 3
I_TURN_RIGHT = 4

# keys to manually control the drone
MOVEMENT_KEYS = {
    pygame.K_w : (I_MOVE_BACKWARD, -1),
    pygame.K_s : (I_MOVE_BACKWARD, 1),
    pygame.K_a : (I_MOVE_RIGHT, -1),
    pygame.K_d : (I_MOVE_RIGHT, 1),
    pygame.K_UP : (I_MOVE_UP, 1),
    pygame.K_DOWN : (I_MOVE_UP, -1),
    pygame.K_LEFT : (I_TURN_RIGHT, -1),
    pygame.K_RIGHT : (I_TURN_RIGHT, 1),
}

# speeds for manual movement
MANUAL_SPEEDS = {
    I_TURN_RIGHT: 2,
    I_MOVE_UP: 2,
    I_MOVE_RIGHT: 3,
    I_MOVE_BACKWARD: 2
}

# names of movements along axes
MOVEMENT_NAMES = [
    ("", ""),
    ("right", "left"),
    ("backward", "forward"),
    ("up", "down"),
    ("turn right", "turn left")
]

def state_none():
    # completely empty state
    return [None] * 5

def state_hover(empty=False):
    # state for hovering
    if empty:
        return [False, None, None, None, None]
    return [False, 0, 0, 0, 0]

def state_move(empty=False):
    # state for movement
    if empty:
        return [True, None, None, None, None]
    return [True, 0, 0, 0, 0]

def join_states(state1, state2=state_hover()):
    # adds two states
    # prefers state2's entries if they are not None

    assert len(state1), len(state2) == (5, 5)
    state = [None] * 5
    for i, (e1, e2) in enumerate(zip(state1, state2)):
        state[i] = e2 if e2 is not None else e1
    return state

def apply_state(drone, state):
    # makes the drone fly according to given state
    drone.set_move(state)

def state_repr(state):
    # makes a nice textual representation out of state
    # like [True, 0, -1, 0, 1] -> 'forward, turn right'

    state_reprs = []
    for i, x in enumerate(state):
        if i == 0:
            continue
        if x > 0:
            state_reprs.append(MOVEMENT_NAMES[i][0])
        elif x < 0:
            state_reprs.append(MOVEMENT_NAMES[i][1])
    return ", ".join(state_reprs)

pressed_keys = list()
def get_current_manual_state(state=None):
    if state is None:
        state = state_move(empty=True)
    for key in pressed_keys:
        state_index, state_factor = MOVEMENT_KEYS.get(key, (None, None))
        if state_index is None:
            continue
        state_factor *= MANUAL_SPEEDS.get(state_index, 1)
        state[state_index] = state_factor * 0.1
    return state

def get_state_manual(event):
    # returns the flight state for manual flight
    # manual flying always overwrites automatic flying

    global pressed_keys
    def with_pressed(state):
        return get_current_manual_state(state)

    if event.type not in (pygame.KEYUP, pygame.KEYDOWN):
        return with_pressed(state_none())

    state_index, state_factor = MOVEMENT_KEYS.get(event.key, (None, None))
    if state_index is None:
        return with_pressed(state_none())

    # let's just use a move state as base here
    # states with all movements 0 will be converted to hover state automatically
    state = state_move(empty=True)

    if event.type == pygame.KEYUP:
        pressed_keys.remove(event.key)
        state[state_index] = 0
    elif event.type == pygame.KEYDOWN:
        pressed_keys.append(event.key)
    return with_pressed(state)

# parameters for autopilot

# for steering there is a window in the center where drone does not steer
# otherwise it attempts to correct by turning left / right
W, H = 640, 360
STEERING_WINDOW_RADIUS = 40
LEFT_TURN_THRESHOLD = int(0.5 * W - STEERING_WINDOW_RADIUS)
RIGHT_TURN_THRESHOLD = int(0.5 * W + STEERING_WINDOW_RADIUS)

# also there is min/max speed for turning depending how far to the side the person is in the picture
MAX_TURN_SPEED = 0.4
MIN_TURN_SPEED = 0.2

# for forward/backward movement we set a distance that the drone should keep to the person
MIN_DISTANCE = 6
# keep distance +/- 1 meter
DISTANCE_WINDOW_RADIUS = 1
# speed is defined in forward_speed function


def mix(alpha, a, b):
    return a * (1.0 - alpha) + b * alpha

def turn_speed(cx):
    # get where we are from threshold to edge of image, as 0 to 1, squared
    # then interpolate from min and max speed
    alpha = 0.0
    if cx > RIGHT_TURN_THRESHOLD:
        alpha = (cx - RIGHT_TURN_THRESHOLD) / float(LEFT_TURN_THRESHOLD)
    elif cx < LEFT_TURN_THRESHOLD:
        alpha = 1.0 - (cx / float(LEFT_TURN_THRESHOLD))
    else:
        return 0.0
    alpha = alpha ** 2
    speed = mix(alpha, MIN_TURN_SPEED, MAX_TURN_SPEED)
    return speed

def forward_speed(object_distance):
    # calculate distance from distance window center
    # the further away -> fly faster
    window_distance = abs(object_distance - MIN_DISTANCE)
    speed = 0.0
    if window_distance < DISTANCE_WINDOW_RADIUS / 2:
        speed = 0.05
    elif window_distance < DISTANCE_WINDOW_RADIUS:
        speed = 0.05
    elif window_distance < DISTANCE_WINDOW_RADIUS + 4:
        speed = 0.1
    else:
        speed = 0.2
    return speed

def get_state_following(last_state, rect, object_height, object_distance, bounds):
    if rect is None:
        # no movement if no person is tracked
        return state_hover()
    state = state_move(empty=True)

    x, y, w, h = rect
    # center of the rectangle
    cx, cy = x + 0.5 * w, y + 0.5 * h
    W, H = bounds

    # first: steering

    # check if we have to turn right
    if cx > RIGHT_TURN_THRESHOLD:
        state[I_TURN_RIGHT] = turn_speed(cx)
    # check if we have to turn left
    elif cx < LEFT_TURN_THRESHOLD:
        state[I_TURN_RIGHT] = -turn_speed(cx)
    # otherwise don't turn
    else:
        state[I_TURN_RIGHT] = 0

    # second: forward/backward

    invalid_distance = object_distance < 0
    before_window = object_distance < MIN_DISTANCE - DISTANCE_WINDOW_RADIUS and not invalid_distance
    behind_window = object_distance > MIN_DISTANCE + DISTANCE_WINDOW_RADIUS and not invalid_distance

    speed = forward_speed(object_distance)
    assert speed >= 0
    if behind_window:
        # move forward when behind window (= too far away from person)
        state[I_MOVE_BACKWARD] = -speed
    elif before_window:
        # move backward when before window (= too near to person)
        state[I_MOVE_BACKWARD] = speed
    elif not invalid_distance:
        # check what last state was
        if last_state[I_MOVE_BACKWARD] < 0:
            # when we were moving forward
            # stop if object_distance <= min_distance (flew far enough into the window)
            # else continue like that
            if object_distance <= MIN_DISTANCE:
                state[I_MOVE_BACKWARD] = 0
            else:
                state[I_MOVE_BACKWARD] = -speed
        if last_state[I_MOVE_BACKWARD] > 0:
            # when we were moving backward
            # stop if object_distance >= min_distance (flew far enough back into the window)
            # else continue like that
            if object_distance >= MIN_DISTANCE:
                state[I_MOVE_BACKWARD] = 0
            else:
                state[I_MOVE_BACKWARD] = speed
    return state


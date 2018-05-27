import math
import pygame

I_MOVE = 0
I_MOVE_RIGHT = 1
I_MOVE_BACKWARD = 2
I_MOVE_UP = 3
I_TURN_RIGHT = 4

MOVEMENTS = {
    pygame.K_w : (I_MOVE_BACKWARD, -1),
    pygame.K_s : (I_MOVE_BACKWARD, 1),
    pygame.K_a : (I_MOVE_RIGHT, -1),
    pygame.K_d : (I_MOVE_RIGHT, 1),
    pygame.K_UP : (I_MOVE_UP, 1),
    pygame.K_DOWN : (I_MOVE_UP, -1),
    pygame.K_LEFT : (I_TURN_RIGHT, -1),
    pygame.K_RIGHT : (I_TURN_RIGHT, 1),
}

MOVEMENT_NAMES = [
    ("", ""),
    ("right", "left"),
    ("backward", "forward"),
    ("up", "down"),
    ("turn right", "turn left")
]

def state_none():
    return [None] * 5

def state_hover(empty=False):
    if empty:
        return [False, None, None, None, None]
    return [False, 0, 0, 0, 0]

def state_move(empty=False):
    if empty:
        return [True, None, None, None, None]
    return [True, 0, 0, 0, 0]

# adds the two
# prefers state2's entries if they are not none
def join_states(state1, state2=state_hover()):
    assert len(state1), len(state2) == (5, 5)
    state = [None] * 5
    for i, (e1, e2) in enumerate(zip(state1, state2)):
        state[i] = e2 if e2 is not None else e1
    return state

def apply_state(drone, state):
    drone.set_move(state)

def state_repr(state):
    state_reprs = []
    for i, x in enumerate(state):
        if i == 0:
            continue
        if x > 0:
            state_reprs.append(MOVEMENT_NAMES[i][0])
        elif x < 0:
            state_reprs.append(MOVEMENT_NAMES[i][1])
    return ", ".join(state_reprs)

W, H = 640, 360
LEFT_RIGHT_THRESHOLD = 40
LEFT_TURN_THRESHOLD = int(0.5 * W - LEFT_RIGHT_THRESHOLD)
RIGHT_TURN_THRESHOLD = int(0.5 * W + LEFT_RIGHT_THRESHOLD)

MAX_TURN_SPEED = 0.4
MIN_TURN_SPEED = 0.2
MIN_FORWARD_SPEED = 0.1

MIN_DISTANCE = 6
# keep distance +/- 1 meter
DISTANCE_WINDOW = 1

def mix(alpha, a, b):
    return a * (1.0 - alpha) + b * alpha

def turn_speed(cx):
    alpha = 0.0
    if cx > RIGHT_TURN_THRESHOLD:
        alpha = (cx - RIGHT_TURN_THRESHOLD) / float(LEFT_TURN_THRESHOLD)
    elif cx < LEFT_TURN_THRESHOLD:
        alpha = 1.0 - (cx / float(LEFT_TURN_THRESHOLD))
    else:
        return 0.0
    #thresh = 0.1
    #if alpha < thresh:
    #    alpha = alpha / thresh
    #    #alpha = alpha ** 2
    #    speed = mix(alpha, 0.05, 0.15)
    #else:
    #    alpha = (alpha - thresh) / (1.0 - thresh)
    #    #alpha = alpha ** 0.5
    #    speed = mix(alpha, 0.15, 0.4)
    alpha = alpha ** 2
    #alpha = alpha ** 0.5
    speed = mix(alpha, MIN_TURN_SPEED, MAX_TURN_SPEED)
    return speed

def forward_speed(object_distance):
    window_distance = abs(object_distance - MIN_DISTANCE)
    speed = 0.0
    if window_distance < DISTANCE_WINDOW / 2:
        speed = 0.05
    elif window_distance < DISTANCE_WINDOW:
        speed = 0.05
    elif window_distance < DISTANCE_WINDOW + 4:
        speed = 0.1
    else:
        speed = 0.2
    return speed

SPEED = {
    I_TURN_RIGHT: 2,
    I_MOVE_UP: 2,
    I_MOVE_RIGHT: 3,
    I_MOVE_BACKWARD: 2
}

pressed_keys = list()
def get_current_manual_state(state=None):
    if state is None:
        state = state_move(empty=True)
    for key in pressed_keys:
        state_index, state_factor = MOVEMENTS.get(key, (None, None))
        if state_index is None:
            continue
        state_factor *= SPEED.get(state_index, 1)
        state[state_index] = state_factor * 0.1
    return state

def get_state_manual(event):
    global pressed_keys
    def with_pressed(state):
        return get_current_manual_state(state)

    if event.type not in (pygame.KEYUP, pygame.KEYDOWN):
        return with_pressed(state_none())

    state_index, state_factor = MOVEMENTS.get(event.key, (None, None))
    if state_index is None:
        return with_pressed(state_none())

    # let's just use a move state as base here
    # states with all movements 0 will be converted to hover state automatically
    state = state_move(empty=True)

    if event.type == pygame.KEYUP:
        #assert not pygame.key.get_pressed()[event.key]
        pressed_keys.remove(event.key)
        state[state_index] = 0
        #print "up:", pressed_keys
    elif event.type == pygame.KEYDOWN:
        #assert pygame.key.get_pressed()[event.key]
        pressed_keys.append(event.key)
        #print "down:", pressed_keys
    return with_pressed(state)

def get_state_following(last_state, rect, object_height, object_distance, bounds):
    if rect is None:
        return state_hover()
    state = state_move(empty=True)

    x, y, w, h = rect
    cx, cy = x + 0.5 * w, y + 0.5 * h
    W, H = bounds

    if cx > RIGHT_TURN_THRESHOLD:
        alpha = (cx - RIGHT_TURN_THRESHOLD) / float(LEFT_TURN_THRESHOLD)
        alpha = alpha ** 2
        speed = MIN_TURN_SPEED * (1.0 - alpha) + MAX_TURN_SPEED * alpha
        state[I_TURN_RIGHT] = speed
        #return ("turn_right", [speed])
    elif cx < LEFT_TURN_THRESHOLD:
        alpha = 1.0 - (cx / float(LEFT_TURN_THRESHOLD))
        alpha = alpha ** 2
        speed = MIN_TURN_SPEED * (1.0 - alpha) + MAX_TURN_SPEED * alpha
        state[I_TURN_RIGHT] = -speed
        #return ("turn_left", [speed])
    else:
        state[I_TURN_RIGHT] = 0

    invalid_distance = object_distance < 0
    before_window = object_distance < MIN_DISTANCE - DISTANCE_WINDOW and not invalid_distance
    behind_window = object_distance > MIN_DISTANCE + DISTANCE_WINDOW and not invalid_distance

    speed = forward_speed(object_distance)
    assert speed >= 0
    if behind_window:
        # move forward when behind window (= too far away from person)
        state[I_MOVE_BACKWARD] = -speed
        #return ("move_forward", [])
    elif before_window:
        # move backward when before window (= too near to person)
        state[I_MOVE_BACKWARD] = speed
        #return ("move_backward", [])
    elif not invalid_distance:
        # check what last state was
        if last_state[I_MOVE_BACKWARD] < 0:
            # when we were moving forward
            # stop if object_distance <= min_distance (flew far enough into the window)
            # else continue like that
            if object_distance <= MIN_DISTANCE:
                state[I_MOVE_BACKWARD] = 0
                #return ("hover", [])
            else:
                state[I_MOVE_BACKWARD] = -speed
                #return ("move_forward", [])
        if last_state[I_MOVE_BACKWARD] > 0:
            # when we were moving backward
            # stop if object_distance >= min_distance (flew far enough back into the window)
            # else continue like that
            if object_distance >= MIN_DISTANCE:
                state[I_MOVE_BACKWARD] = 0
                #return ("hover", [])
            else:
                state[I_MOVE_BACKWARD] = speed
                #return ("move_backward", [])
    else:
        print "Distance invalid!"

    
    return state



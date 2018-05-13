#!/usr/bin/env python2

# Copyright (c) 2011 Bastian Venthur
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


"""Demo app for the AR.Drone.

This simple application allows to control the drone and see the drone's video
stream.
"""


import pygame

import libardrone

import cv2
import numpy as np

FAKE_VIDEO = True
FAKE_VIDEO_PATH = "testVideoStefan.mp4"

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
    ("forward", "backward"),
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

W, H = 640, 360
LEFT_RIGHT_THRESHOLD = 40
LEFT_TURN_THRESHOLD = int(0.5 * W - LEFT_RIGHT_THRESHOLD)
RIGHT_TURN_THRESHOLD = int(0.5 * W + LEFT_RIGHT_THRESHOLD)

MAX_TURN_SPEED = 0.4
MIN_TURN_SPEED = 0.2
MIN_FORWARD_SPEED = 0.1

SPEED = {
    I_TURN_RIGHT: 2,
    I_MOVE_UP: 2,
    I_MOVE_RIGHT: 3,
    I_MOVE_BACKWARD: 2
}

# distance measurements:
# person (moritz) standing away from drone in different distances -> object height
# 5m: 0.39
# 7.5m: 0.49
# 10m: 0.7

# distance * object_height = F
# this F should be constant for constant real object height (~averaged human)
# we obtain 3.7 as average over these samples
F = 3.7

MIN_DISTANCE = 8
# keep distance +/- 1 meter
DISTANCE_WINDOW = 1

def distance(object_height):
    try:
        return F / object_height
    except ZeroDivisionError:
        return -1

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
    before_window = object_distance < MIN_DISTANCE - DISTANCE_WINDOW
    behind_window = object_distance > MIN_DISTANCE + DISTANCE_WINDOW

    if behind_window:
        # move forward when behind window (= too far away from person)
        state[I_MOVE_BACKWARD] = -MIN_FORWARD_SPEED
        #return ("move_forward", [])
    elif before_window:
        # move backward when before window (= too near to person)
        state[I_MOVE_BACKWARD] = MIN_FORWARD_SPEED
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
                state[I_MOVE_BACKWARD] = -MIN_FORWARD_SPEED
                #return ("move_forward", [])
        if last_state[I_MOVE_BACKWARD] > 0:
            # when we were moving backward
            # stop if object_distance >= min_distance (flew far enough back into the window)
            # else continue like that
            if object_distance >= MIN_DISTANCE:
                state[I_MOVE_BACKWARD] = 0
                #return ("hover", [])
            else:
                state[I_MOVE_BACKWARD] = MIN_FORWARD_SPEED
                #return ("move_backward", [])
    
    return state

def apply_state(drone, state):
    #states = {
    #    "hover" : drone.hover,
    #    "move_forward" : drone.move_forward,
    #    "move_backward" : drone.move_backward,
    #    "move_left" : drone.move_left,
    #    "move_right" : drone.move_right,
    #    "move_up" : drone.move_up,
    #    "move_down" : drone.move_down,
    #    "turn_left" : drone.turn_left,
    #    "turn_right" : drone.turn_right,
    #    "hold" : lambda: None,
    #}
    #f = states.get(state[0], None)
    #if f is None:
    #    print "### Warning: Unknown state '%s'" % str(state)
    #else:
    #    f(*state[1])

    drone.set_move(state)

class HumanDetector:
    def __init__(self, every_nth):
        self.every_nth = every_nth
        self.counter = 0

        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        self.rects = None
        self.weights = None
    
    def process(self, frame):
        self.counter = (self.counter + 1) % self.every_nth
        if self.counter != 0:
            return
        self.rects, self.weights = self.hog.detectMultiScale(frame, winStride=(8, 8), padding=(8,8), scale=1.2)

    def get_rect(self):
        if self.rects is None or len(self.rects) == 0:
            return None
        # or the one with highest weight?
        return self.rects[np.argmax(self.weights)]

    def render_rects(self, frame, object_height):
        if self.rects is None or len(self.rects) == 0:
            return frame

        max_weight_i = np.argmax(self.weights)
        for i, ((x, y, w, h), weight) in enumerate(zip(self.rects, self.weights)):
            #x *= 2
            #y *= 2
            #w *= 2
            #h *= 2

            color = (255, 255, 255) if i != max_weight_i else (255, 0, 0)
            frame = cv2.rectangle(frame, (x,y), (x+w, y+h), color)
            if i == max_weight_i:
                cx = int(x + 0.5 * w)
                cy = int(y + 0.5 * h)
                hhx = int(H * object_height / 2.0)
                frame = cv2.line(frame, (cx, cy-hhx), (cx, cy+hhx), color)
                frame = cv2.circle(frame, (cx, cy), 5, color, -1)

            font = cv2.FONT_HERSHEY_SIMPLEX
            frame = cv2.putText(frame, "%.04f" % weight, (x, y - 2), font, 0.5, color, 1, cv2.LINE_8, False)
        return frame

def main(drone, video):
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    detector = HumanDetector(9)
    following = False

    running = True
    last_state = state_hover()
    last_following_state = None
    last_object_heights = []
    last_object_heights_n = 6*3
    while running:
        manual_state = get_current_manual_state()
        for event in pygame.event.get():
            # events have to be joined together because keyup (setting speed in state to 0) appear only once
            manual_state = join_states(manual_state, get_state_manual(event))
            #if state is not None:
            #    print "Got manual state: %s" % str(state)
            if event.type == pygame.QUIT:
                running = False 
            #elif event.type == pygame.KEYUP:
            #    drone.hover()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    drone.reset()
                    running = False
                # takeoff / land
                elif event.key == pygame.K_RETURN:
                    drone.takeoff()
                elif event.key == pygame.K_SPACE:
                    drone.land()
                # emergency
                elif event.key == pygame.K_BACKSPACE:
                    drone.reset()
                # speed
                elif event.key == pygame.K_1:
                    drone.speed = 0.1
                elif event.key == pygame.K_2:
                    drone.speed = 0.2
                elif event.key == pygame.K_3:
                    drone.speed = 0.3
                elif event.key == pygame.K_4:
                    drone.speed = 0.4
                elif event.key == pygame.K_5:
                    drone.speed = 0.5
                elif event.key == pygame.K_6:
                    drone.speed = 0.6
                elif event.key == pygame.K_7:
                    drone.speed = 0.7
                elif event.key == pygame.K_8:
                    drone.speed = 0.8
                elif event.key == pygame.K_9:
                    drone.speed = 0.9
                elif event.key == pygame.K_0:
                    drone.speed = 1.0
                elif event.key == pygame.K_p:
                    pprint.pprint(drone.navdata.get(0, {}))
                    pprint.pprint(drone.navdata.get("drone_state", {}))
                elif event.key == pygame.K_f:
                    following = not following
                    last_following_state = state_none()

        ret, frame = video.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if FAKE_VIDEO:
            frame = cv2.resize(frame, (W, H))

        detector.process(frame)
        rect = detector.get_rect()
        object_height = 0.0
        if rect is not None:
            object_height = rect[3] / float(H)

            last_object_heights.append(object_height)
            if len(last_object_heights) > last_object_heights_n:
                last_object_heights.pop(0)
            object_height = sum(last_object_heights) / float(len(last_object_heights))

            # todo sometimes the average height is much smaller than detected rect
            # -> with some threshold just take rect, to prevent crash of drone
        else:
            last_object_heights = []
        object_distance = distance(object_height)

        following_state = state_none()
        if following:
            following_state = get_state_following(last_following_state, rect, object_height, object_distance, (W, H))
            last_following_state = following_state

        # last state + following_state + manual state
        state = join_states(following_state, manual_state)
        #state = manual_state
        state = join_states(state_hover(), state)
        #state = join_states(last_state, following_state)
        #state = join_states(state, manual_state)
        if all(map(lambda x: x == 0, state[1:])):
            #print "Converting state to hover"
            state = state_hover()

        if state != last_state:
            print "Applying state: %s" % str(state)
            apply_state(drone, state)
        last_state = state

        state_reprs = []
        for i, x in enumerate(state):
            if i == 0:
                continue
            if x > 0:
                state_reprs.append(MOVEMENT_NAMES[i][0])
            elif x < 0:
                state_reprs.append(MOVEMENT_NAMES[i][1])
        state_repr = ", ".join(state_reprs)

        frame = cv2.line(frame, (LEFT_TURN_THRESHOLD, 0), (LEFT_TURN_THRESHOLD, H), (0, 255, 0))
        frame = cv2.line(frame, (RIGHT_TURN_THRESHOLD, 0), (RIGHT_TURN_THRESHOLD, H), (0, 255, 0))
        frame = detector.render_rects(frame, object_height)
        surface = pygame.surfarray.make_surface(np.flip(np.rot90(frame), 0))
        # battery status
        hud_color = (255, 0, 0) if drone.navdata.get('drone_state', dict()).get('emergency_mask', 1) else (10, 10, 255)
        following_color = (0, 255, 0) if following else (255, 0, 0)
        bat = drone.navdata.get(0, dict()).get('battery', 0)
        f = pygame.font.Font(None, 20)
        battery_label = f.render('Battery: %i%%' % bat, True, hud_color)
        state_label = f.render(state_repr, True, (0, 255, 255))
        following_label = f.render("Following: %s" % following, True, following_color)
        object_label = f.render("Object height: %0.3f, distance: %2.2fm" % (object_height, object_distance), True, (255, 255, 255))
        screen.blit(surface, (0, 0))
        screen.blit(battery_label, (10, 10))
        screen.blit(state_label, (10, screen.get_height() - 10 - following_label.get_height() - state_label.get_height()))
        screen.blit(following_label, (10, screen.get_height() - 10 - following_label.get_height()))
        screen.blit(object_label, (screen.get_width() - 10 - object_label.get_width(), screen.get_height() - 10 - object_label.get_height()))

        pygame.display.flip()
        if FAKE_VIDEO:
            clock.tick(20)
        else:
            clock.tick(0)
        pygame.display.set_caption("FPS: %.2f" % clock.get_fps())

if __name__ == '__main__':
    print "Connecting to drone..."
    drone = libardrone.ARDrone()
    print "Connecting to video stream..."
    # video part of api doesn't work
    # but this works:
    video = None
    if not FAKE_VIDEO:
        video = cv2.VideoCapture("tcp://192.168.1.1:5555")
    else:
        video = cv2.VideoCapture(FAKE_VIDEO_PATH)
    print "Done."

    try:
        main(drone, video)
    finally:
        print "Shutting down..."
        drone.land()
        drone.halt()
        print "Ok."


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

FAKE_VIDEO = False

MANUAL_KEYS = [
    pygame.K_w,
    pygame.K_s,
    pygame.K_a,
    pygame.K_d,
    pygame.K_UP,
    pygame.K_DOWN,
    pygame.K_LEFT,
    pygame.K_RIGHT,
    pygame.K_h
]

W, H = 640, 360
LEFT_RIGHT_THRESHOLD = 40
LEFT_TURN_THRESHOLD = int(0.5 * W - LEFT_RIGHT_THRESHOLD)
RIGHT_TURN_THRESHOLD = int(0.5 * W + LEFT_RIGHT_THRESHOLD)

def is_manual_key_pressed():
    pressed = np.array(list(pygame.key.get_pressed()))
    pressed = pressed[MANUAL_KEYS]
    return np.any(pressed != 0)

def get_state_manual(event):
    if event.type == pygame.KEYUP and event.key in MANUAL_KEYS:
        return "hover"
    elif event.type == pygame.KEYDOWN:
        # forward / backward
        if event.key == pygame.K_w:
            return "move_forward"
        elif event.key == pygame.K_s:
            return "move_backward"
        # left / right
        elif event.key == pygame.K_a:
            return "move_left"
        elif event.key == pygame.K_d:
            return "move_right"
        # up / down
        elif event.key == pygame.K_UP:
            return "move_up"
        elif event.key == pygame.K_DOWN:
            return "move_down"
        # turn left / turn right
        elif event.key == pygame.K_LEFT:
            return "turn_left"
        elif event.key == pygame.K_RIGHT:
            return "turn_right"
        # hold drone position (holding also blocks following mode's decisions)
        elif event.key == pygame.K_h:
            return "hover"
    return None

def get_state_following(rect, bounds):
    if rect is None:
        return "hover"

    x, y, w, h = rect
    cx, cy = x + 0.5 * w, y + 0.5 * h
    W, H = bounds

    if cx > RIGHT_TURN_THRESHOLD:
        return "turn_right"
    if cx < LEFT_TURN_THRESHOLD:
        return "turn_left"

    return "hover"

def apply_state(drone, state):
    states = {
        "hover" : drone.hover,
        "move_forward" : drone.move_forward,
        "move_backward" : drone.move_backward,
        "move_left" : drone.move_left,
        "move_right" : drone.move_right,
        "move_up" : drone.move_up,
        "move_down" : drone.move_down,
        "turn_left" : lambda: drone.turn_left(0.2),
        "turn_right" : lambda: drone.turn_right(0.2),
        "hold" : lambda: None,
    }
    f = states.get(state, None)
    if f is None:
        print "### Warning: Unknown state '%s'" % state
    else:
        f()

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

    def render_rects(self, frame):
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
                frame = cv2.circle(frame, (int(x + 0.5 * w), int(y + 0.5 * h)), 5, color, -1)

            font = cv2.FONT_HERSHEY_SIMPLEX
            frame = cv2.putText(frame, "%.04f" % weight, (x, y - 2), font, 0.5, color, 1, cv2.LINE_8, False)
        return frame

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    print "Connecting to drone..."
    drone = libardrone.ARDrone()
    print "Connecting to video stream..."
    # video part of api doesn't work
    # but this works:
    video = None
    if not FAKE_VIDEO:
        video = cv2.VideoCapture("tcp://192.168.1.1:5555")
    else:
        video = cv2.VideoCapture("testVideoStefan.mp4")
    print "Done."
    clock = pygame.time.Clock()

    detector = HumanDetector(9)
    following = False

    running = True
    last_state = None
    while running:
        state = None
        for event in pygame.event.get():
            state = get_state_manual(event)
            if state is not None:
                print "Got manual state: %s" % state
            if event.type == pygame.QUIT:
                running = False 
            elif event.type == pygame.KEYUP:
                drone.hover()
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

        ret, frame = video.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if FAKE_VIDEO:
            frame = cv2.resize(frame, (W, H))

        detector.process(frame)
        rect = detector.get_rect()

        if state is None and is_manual_key_pressed():
            state = "hold"
        if state is None and following:
            state = get_state_following(rect, (W, H))
            if state is not None:
                print "Got following state: %s" % state
        if state is not None and state != last_state:
            print "Applying state: %s" % state
            apply_state(drone, state)
        last_state = state

        frame = cv2.line(frame, (LEFT_TURN_THRESHOLD, 0), (LEFT_TURN_THRESHOLD, H), (0, 255, 0))
        frame = cv2.line(frame, (RIGHT_TURN_THRESHOLD, 0), (RIGHT_TURN_THRESHOLD, H), (0, 255, 0))
        frame = detector.render_rects(frame)
        surface = pygame.surfarray.make_surface(np.flip(np.rot90(frame), 0))
        # battery status
        hud_color = (255, 0, 0) if drone.navdata.get('drone_state', dict()).get('emergency_mask', 1) else (10, 10, 255)
        following_color = (0, 255, 0) if following else (255, 0, 0)
        bat = drone.navdata.get(0, dict()).get('battery', 0)
        f = pygame.font.Font(None, 20)
        battery_label = f.render('Battery: %i%%' % bat, True, hud_color)
        following_label = f.render("Following: %s" % following, True, following_color)
        screen.blit(surface, (0, 0))
        screen.blit(battery_label, (10, 10))
        screen.blit(following_label, (10, screen.get_height() - 10 - following_label.get_height()))

        pygame.display.flip()
        clock.tick(50)
        pygame.display.set_caption("FPS: %.2f" % clock.get_fps())

    print "Shutting down...",
    drone.halt()
    print "Ok."

if __name__ == '__main__':
    main()

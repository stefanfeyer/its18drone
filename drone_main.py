#!/usr/bin/env python2

import argparse
import pygame
import sys
import datetime

import libardrone

import cv2
import numpy as np
import math

from drone_measurements import *
from drone_tracking import HumanDetector
from drone_flight import *

def main(args, drone, video, videoout, videoout_hud):
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    detector = HumanDetector(6)
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
                elif event.key == pygame.K_COMMA and args.fake_video:
                    frame_i = video.get(cv2.CAP_PROP_POS_FRAMES)
                    fps = video.get(cv2.CAP_PROP_FPS)
                    video.set(cv2.CAP_PROP_POS_FRAMES, frame_i - 3*fps)
                elif event.key == pygame.K_PERIOD and args.fake_video:
                    frame_i = video.get(cv2.CAP_PROP_POS_FRAMES)
                    fps = video.get(cv2.CAP_PROP_FPS)
                    video.set(cv2.CAP_PROP_POS_FRAMES, frame_i + 3*fps)

        ret, frame = video.read()
        if args.fake_video:
            frame = cv2.resize(frame, (W, H))
        if videoout:
            videoout.write(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        detector.process(frame)
        rect = detector.get_rect()
        object_height = 0.0
        object_distance = -1.0
        object_angle = 0.0
        threshold_angle = 0.0
        if rect is not None:
            object_height = rect[3] / float(H)

            last_object_heights.append(object_height)
            if len(last_object_heights) > last_object_heights_n:
                last_object_heights.pop(0)
            object_height = sum(last_object_heights) / float(len(last_object_heights))

            # todo sometimes the average height is much smaller than detected rect
            # -> with some threshold just take rect, to prevent crash of drone
            # later note: psssssh that was just a bug

            object_distance = measure_distance(object_height)
            cx = rect[0] + rect[2] * 0.5
            object_angle = measure_angle(cx, object_distance)
            threshold_angle = measure_angle(LEFT_TURN_THRESHOLD, object_distance)
        else:
            last_object_heights = []

        following_state = state_none()
        if following:
            following_state = get_state_following(last_following_state, rect, object_height, object_distance, (W, H))
            last_following_state = following_state

        state = join_states(following_state, manual_state)
        state = join_states(state_hover(), state)
        if all(map(lambda x: x == 0, state[1:])):
            state = state_hover()

        if state != last_state:
            print "Applying state: %s" % str(state)
            apply_state(drone, state)
        last_state = state

        frame = cv2.line(frame, (LEFT_TURN_THRESHOLD, 0), (LEFT_TURN_THRESHOLD, H), (0, 255, 0))
        frame = cv2.line(frame, (RIGHT_TURN_THRESHOLD, 0), (RIGHT_TURN_THRESHOLD, H), (0, 255, 0))

        # debug stuff: plot turn speeds
        #poly = []
        #for x in range(0, W):
        #    speed = turn_speed(x)
        #    poly.append([x, int(0.5 * H - speed / 0.4 * 50)])
        #frame = cv2.polylines(frame, [np.array(poly)], False, (0, 255, 0))
        
        # debug stuff: plot angles
        def draw_angle(a, length, color, frame=frame):
            actual_a = abs(a)
            p1 = (W / 2, H)
            dx = math.sin(math.radians(actual_a)) * length
            dy = math.sin(math.radians(90.0 - actual_a)) * length
            p2 = (int(p1[0] + sign(a) * dx), int(p1[1] - dy))
            frame = cv2.line(frame, p1, p2, color)
        #draw_angle(-FOV / 2.0, 200, (0, 0, 255))
        #draw_angle(FOV / 2.0, 200, (0, 0, 255))
        #draw_angle(-threshold_angle, 200, (0, 255, 0))
        #draw_angle(threshold_angle, 200, (0, 255, 0))
        #draw_angle(object_angle, 200, (0, 255, 255))

        frame = detector.render_rects(frame, object_height)
        surface = pygame.surfarray.make_surface(np.flip(np.rot90(frame), 0))
        hud_color = (255, 0, 0) if drone.navdata.get('drone_state', dict()).get('emergency_mask', 1) else (10, 10, 255)
        following_color = (0, 255, 0) if following else (255, 0, 0)
        bat = drone.navdata.get(0, dict()).get('battery', 0)
        f = pygame.font.Font(None, 20)
        battery_label = f.render('Battery: %i%%' % bat, True, hud_color)
        state_label = f.render(state_repr(state), True, (0, 255, 255))
        following_label = f.render("Following: %s" % following, True, following_color)

        angle_label = f.render("Angle: %2.2f" % object_angle, True, (255, 255, 0))

        window_distance = object_distance - MIN_DISTANCE
        window_color = (0, 255, 0)
        if window_distance < -DISTANCE_WINDOW_RADIUS:
            window_color = (255, 0, 0)
        elif window_distance > DISTANCE_WINDOW_RADIUS:
            window_color = (255, 255, 0)
        window_label = f.render("Window: %0.3f" % window_distance, True, window_color)

        object_label = f.render("Height: %0.3f, d: %2.2fm" % (object_height, object_distance), True, (255, 255, 255))

        screen.blit(surface, (0, 0))
        #screen.blit(battery_label, (10, 10))
        screen.blit(state_label, (10, screen.get_height() - 10 - following_label.get_height() - state_label.get_height()))
        screen.blit(following_label, (10, screen.get_height() - 10 - following_label.get_height()))
        if object_distance >= 0:
            screen.blit(angle_label, (screen.get_width() - 10 - angle_label.get_width(), screen.get_height() - 10 - angle_label.get_height() - window_label.get_height() - object_label.get_height()))
            screen.blit(window_label, (screen.get_width() - 10 - window_label.get_width(), screen.get_height() - 10 - window_label.get_height() - object_label.get_height()))
        screen.blit(object_label, (screen.get_width() - 10 - object_label.get_width(), screen.get_height() - 10 - object_label.get_height()))

        if videoout_hud:
            frame_hud = pygame.surfarray.array3d(screen)
            frame_hud = frame_hud.swapaxes(0, 1)
            frame_hud = cv2.cvtColor(frame_hud, cv2.COLOR_BGR2RGB)
            videoout_hud.write(frame_hud)

        pygame.display.flip()
        if args.fake_video:
            clock.tick(30)
        else:
            clock.tick(0)
        pygame.display.set_caption("FPS: %2.2f BAT: %i%%" % (clock.get_fps(), bat))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--fake-video", "-f", default=None, type=str)
    parser.add_argument("--record", default=False, action="store_true")
    parser.add_argument("--record-hud", default=False, action="store_true")

    args = parser.parse_args()

    print "Connecting to drone..."
    drone = libardrone.ARDrone()
    print "Connecting to video stream..."
    # video part of api doesn't work
    # but this works:
    video = None
    if not args.fake_video:
        video = cv2.VideoCapture("tcp://192.168.1.1:5555")
    else:
        video = cv2.VideoCapture(args.fake_video)
    print "Done."

    videoout, videoout_hud = None, None
    now = datetime.datetime.now()
    filename = now.strftime("video_%Y-%m-%d_%H_%M_%S.mp4")
    filename_hud = now.strftime("videohud_%Y-%m-%d_%H_%M_%S.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    if args.record:
        videoout = cv2.VideoWriter(filename, fourcc, 30, (W, H))
    if args.record_hud:
        videoout_hud = cv2.VideoWriter(filename_hud, fourcc, 30, (W, H))

    try:
        main(args, drone, video, videoout, videoout_hud)
    finally:
        print "Shutting down..."
        drone.land()
        drone.halt()
        print "Ok."

        if videoout:
            videoout.release()
            del videoout
        if videoout_hud:
            videoout_hud.release()
            del videoout_hud


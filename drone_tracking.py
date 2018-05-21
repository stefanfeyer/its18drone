import cv2
import numpy as np

class HumanDetector:
    def __init__(self, every_nth):
        self.every_nth = every_nth
        self.counter = 0
        self.tcounter = 0

        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        self.drects = None
        self.dweights = None

        self.tracker = None
        self.trect = None

    def init_tracker(self, frame, rect):
        self.tracker = cv2.TrackerKCF_create()
        self.tracker.init(frame, tuple(rect))

    def process(self, frame):
        self.tcounter = (self.tcounter + 1) % 3
        if self.tracker and self.tcounter == 0:
            found, rect = self.tracker.update(frame)
            if found:
                self.trect = tuple(map(int, rect))
            else:
                self.tracker = None
                self.trect = None

        self.counter = (self.counter + 1) % self.every_nth
        if self.counter != 0:
            return
        self.drects, self.dweights = self.hog.detectMultiScale(frame, winStride=(8, 8), padding=(8,8), scale=1.2)

        if len(self.drects) != 0:
            rect = self.drects[np.argmax(self.dweights)]
            self.init_tracker(frame, rect)

    def get_rect(self):
        if self.drects is None or len(self.drects) == 0:
            return self.trect
        return self.drects[np.argmax(self.dweights)]

    def render_rects(self, frame, object_height):
        if self.drects is None or len(self.drects) == 0:
            # TODO tracked rect
            if self.trect is None:
                return frame
            x, y, w, h = self.trect
            color = (0, 0, 255)
            frame = cv2.rectangle(frame, (x, y), (x+w, y+h), color)
        else:
            max_weight_i = np.argmax(self.dweights)
            for i, ((x, y, w, h), weight) in enumerate(zip(self.drects, self.dweights)):
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

import cv2
import numpy as np
from imutils.object_detection import non_max_suppression

# constants redundant... hmmm
W, H = 640, 360

class HumanDetector:
    def __init__(self, every_nth):
        self.every_nth = every_nth
        self.dcounter = 0
        self.tcounter = 0

        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        # outputs of people detector
        self.drects = None
        self.dweights = None

        self.tracker = None
        self.trect = None

        self.tracking = False
        self.tracking_black = False
        self.previous_hist = None

    def init_tracker(self, frame, rect):
        self.tracker = cv2.TrackerKCF_create()
        self.tracker.init(frame, tuple(rect))
        self.tracking = True

    def index_hist(self, hist):
        hist_indexed = np.zeros((len(hist), 2), np.float32)
        hist_indexed[:,0] = hist[:, 0]
        hist_indexed[:,1] = range(0,len(hist))
        return hist_indexed

    def extract_rect_info(self, frame, rect):
        x,y,w,h = rect
        roi_border_x = 15
        roi = frame[y+(h / 10):y+h-(h / 10), x+(w / 4):x+w-(w / 4)]
        xr, yr, wr, hr = x+(w / 4), y+(h / 10), x+w-(w / 4), y+h-(h / 10)
        color = (0, 255, 0)
        frame = cv2.rectangle(frame, (xr, yr), (wr, hr), color)
        roi = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
        avg_value = np.average(roi[:, :, 2])
        hist = cv2.calcHist([roi], [0], None, [180], [0,180])
        hist = cv2.normalize(hist, hist)

        # need to index hist for EMD
        return self.index_hist(hist), avg_value

    def find_right_person(self, frame):
        similarity_threshold = 5
        black_value_threshold = 110

        # if we have never tracked before (== previous_hist is None),
        # just return the object that is most likely to be a person
        if self.previous_hist is None: 
            rect = self.drects[np.argmax(self.dweights)]
            hist, avg_value = self.extract_rect_info(frame, rect)
            if avg_value < black_value_threshold:
                self.tracking_black = True
            return True, rect, hist

        closest_rect, closest_hist = None, None
        max_similarity = similarity_threshold
        for rect in self.drects:
            new_hist, avg_value = self.extract_rect_info(frame, rect)
            if not self.tracking_black:
                emd = cv2.EMD(new_hist, self.previous_hist, cv2.DIST_L1)
                if emd[0] < max_similarity and avg_value > black_value_threshold:
                    closest_rect = rect
                    max_similarity = emd[0]
                    closest_hist = new_hist
            else:
                if avg_value < black_value_threshold:
                    closest_rect = rect
                    max_similarity = 4
                    closest_hist = new_hist

        return (closest_rect is not None), closest_rect, closest_hist

    def process(self, frame):
        self.tcounter = (self.tcounter + 1) % (self.every_nth/2)
        self.dcounter = (self.dcounter + 1) % self.every_nth
        # early exit in case we don't want to update on this tick
        if self.dcounter != 0 and self.tcounter != 0:
            return

        # try updating tracker with new frame around person
        # useful because tracker does not change rect sizes when person moves closer/further away
        # re-detecting person updates frame size
        if self.dcounter == 0:
            if self.tracking: # only look in close proximity to currently tracked object
                x,y,w,h = self.trect
                roi_border = 100
                roi = frame[max(y-roi_border,0):min(y+h+roi_border, frame.shape[0]), max(x-roi_border, 0):min(x+w+roi_border, frame.shape[1])]
                self.drects, self.dweights = self.hog.detectMultiScale(roi, winStride=(8, 8), padding=(8, 8), scale=1.2)
                for i, rect in enumerate(self.drects):
                    rect[0] = rect[0] + max(x-roi_border, 0)
                    rect[1] = rect[1] + max(y-roi_border, 0)
            else:
                self.drects, self.dweights = self.hog.detectMultiScale(frame, winStride=(8, 8), padding=(8, 8), scale=1.2)
                self.drects = non_max_suppression(self.drects, probs=None, overlapThresh=0.65)

            if len(self.drects) != 0: # persons detected
                person_found, rect, hist = self.find_right_person(frame)
                self.previous_hist = hist
                if person_found: # refound our person
                    self.init_tracker(frame, tuple(rect))

        if self.tracking:
            self.tracking, rect = self.tracker.update(frame)
            if self.tracking:
                self.trect = tuple(map(int, rect))
            else:
                self.trect = None

    def get_rect(self):
        return self.trect

    def render_rects(self, frame, object_height):
        if self.trect is None:
            return frame
        x, y, w, h = self.trect
        color = (0, 0, 255)
        frame = cv2.rectangle(frame, (x, y), (x+w, y+h), color)
        return frame

import cv2
import numpy as np

#TODO (jh): remove before rollout
import pdb

# constants redundant... hmmm
W, H = 640, 360

class HumanDetector:
    def __init__(self, every_nth):
        self.every_nth = every_nth
        self.dcounter = 0
        self.tcounter = 0

        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

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

# every 3rd frame, update tracker
# every nth frame, refind person
# if person found:
#   update tracker with new person rect
# elif tracker is still tracking:
#   keep tracking
# else:
#   keep trying to refind person

    def index_hist(self, hist):
        hist_indexed = np.zeros((len(hist), 2), np.float32)
        hist_indexed[:,0] = hist[:, 0]
        hist_indexed[:,1] = range(0,len(hist))
        return hist_indexed

    def extract_rect_info(self, frame, rect):
        print rect
        x,y,w,h = rect
        roi_border_x = 15
        roi = frame[y+(h / 10):y+h-(h / 10), x+(w / 4):x+w-(w / 4)]
        xr, yr, wr, hr = x+(w / 4), y+(h / 10), x+w-(w / 4), y+h-(h / 10)
        print xr, yr, wr, hr
        print "rect drawn"
        color = (0, 255, 0)
        frame = cv2.rectangle(frame, (xr, yr), (wr, hr), color)
        roi = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
        avg_value = np.average(roi[:, :, 2])
        hist = cv2.calcHist([roi], [0], None, [180], [0,180])
        hist = cv2.normalize(hist, hist)

        # debuggin stuff
        if (hist == [0.0] * 180).all():
            pdb.set_trace()
        
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
            print "avg value:", avg_value
            print "tracking black:", self.tracking_black
            if not self.tracking_black:
                emd = cv2.EMD(new_hist, self.previous_hist, cv2.DIST_L1)
                print emd[0]
                if emd[0] < max_similarity and avg_value > black_value_threshold:
                    print "tracking not black?"
                    closest_rect = rect
                    max_similarity = emd[0]
                    closest_hist = new_hist
            else:
                if avg_value < black_value_threshold:
                    print "tracking black?"
                    closest_rect = rect
                    max_similarity = 4
                    closest_hist = new_hist

        print len(self.drects)
        print max_similarity, closest_rect, (closest_rect is not None)
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
                print "still tracking!"
                x,y,w,h = self.trect
                roi_border = 20
                roi = frame[max(y-roi_border,0):min(y+h+roi_border, frame.shape[0]), max(x-roi_border, 0):min(x+w+roi_border, frame.shape[1])]
                self.drects, self.dweights = self.hog.detectMultiScale(roi, winStride=(8, 8), padding=(8, 8), scale=1.2)
                print len(self.drects)
                for i, rect in enumerate(self.drects):
                    rect[0] = rect[0] + max(x-roi_border, 0)
                    rect[1] = rect[1] + max(y-roi_border, 0)
            else:
                self.drects, self.dweights = self.hog.detectMultiScale(frame, winStride=(8, 8), padding=(8, 8), scale=1.2)

            if len(self.drects) != 0: # persons detected
                person_found, rect, hist = self.find_right_person(frame)
                #if self.previous_hist is None:
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
        #if self.drects is None or len(self.drects) == 0:
        return self.trect
        #return self.drects[np.argmax(self.dweights)]

    def render_rects(self, frame, object_height):
        if self.trect is None:
            return frame
        x, y, w, h = self.trect
        color = (0, 0, 255)
        frame = cv2.rectangle(frame, (x, y), (x+w, y+h), color)
        #if self.drects is None or len(self.drects) == 0:
        #    # TODO tracked rect
        #    if self.trect is None:
        #        return frame
        #    x, y, w, h = self.trect
        #    color = (0, 0, 255)
        #    frame = cv2.rectangle(frame, (x, y), (x+w, y+h), color)
        #else:
        #    max_weight_i = np.argmax(self.dweights)
        #    for i, ((x, y, w, h), weight) in enumerate(zip(self.drects, self.dweights)):
                #x *= 2
                #y *= 2
                #w *= 2
                #h *= 2

        #        color = (255, 255, 255) if i != max_weight_i else (255, 0, 0)
        #        frame = cv2.rectangle(frame, (x,y), (x+w, y+h), color)
        #        if i == max_weight_i:
        #            cx = int(x + 0.5 * w)
        #            cy = int(y + 0.5 * h)
        #            hhx = int(H * object_height / 2.0)
        #            frame = cv2.line(frame, (cx, cy-hhx), (cx, cy+hhx), color)
        #            frame = cv2.circle(frame, (cx, cy), 5, color, -1)

        #        font = cv2.FONT_HERSHEY_SIMPLEX
        #        frame = cv2.putText(frame, "%.04f" % weight, (x, y - 2), font, 0.5, color, 1, cv2.LINE_8, False)
        return frame

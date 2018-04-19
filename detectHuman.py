#pip install imutils
#from https://www.pyimagesearch.com/2015/11/09/pedestrian-detection-opencv/
from __future__ import print_function
from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2
 
# initialize the HOG descriptor/person detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
videoPath = 'testVideoJogger.mp4'
cap = cv2.VideoCapture(videoPath)
# take only every ith frame
ithFrame = 2
i=0
while(cap.isOpened()):
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break  
    # Capture frame-by-frame
    ret,frame=cap.read()
    frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if i%ithFrame == 0:
        # detect people in the frame
        (rects, weights) = hog.detectMultiScale(frameGray, winStride=(4, 4), padding=(8, 8), scale=1.05)
     
        for (x,y,w,h) in rects:
            cv2.rectangle(frame, (x,y), (x+w, y+h), (255,255,255))
     
        # apply non-maxima suppression to the bounding boxes using a
        # fairly large overlap threshold to try to maintain overlapping
        # boxes that are still people
        rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
        pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)
     
        # draw the final bounding boxes
        for (xA, yA, xB, yB) in pick:
            cv2.rectangle(frame, (xA, yA), (xB, yB), (0, 0, 0), 2)
        
        cv2.imshow('frame',frame)
    i=i+1

cap.release()
cv2.waitKey(0)
cv2.destroyAllWindows()
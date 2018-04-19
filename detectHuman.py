#pip install imutils
#from https://www.pyimagesearch.com/2015/11/09/pedestrian-detection-opencv/
from __future__ import print_function
from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2

# initialise variables and parameters
hog = ''
hSpeed = 1
rotSpeed = 1
moveSpeed = 1
videoPath = ''
maxHeight = 1
maxSpeed = 1
ithFrame = 1
i=0

#init(1, 1, 1, 'testVideoStefan.mp4', 1, 1, 1)
initDetectPerson()
start()

# main Method
def start():
    cap = cv2.VideoCapture(videoPath)
    while(cap.isOpened()):
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break  
        # Capture frame-by-frame
        ret,frame=cap.read()
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if i%ithFrame == 0:
            rects = detectPerson(frameGray)
            frame = drawRectangles(rects, frame)        
            cv2.imshow('frame',frame)
            calcPersonCenter(rect, imageSize)
            positionDroneOnPersonCenter()
        i=i+1   
    cap.release()
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# if you want to have it nice take this method, else just ignore it and fill in the values in the top
def init(hSpeed, rotSpeed, moveSpeed, videoPath, maxHeight, maxSpeed, ithFrame):
    hSpeed = hSpeed
    rotSpeed = rotSpeed
    moveSpeed = moveSpeed
    videoPath = videoPath
    maxHeight = maxHeight
    maxSpeed = maxSpeed
    ithFrame = ithFrame
    return


# initialize the HOG descriptor/person detector
def initDetectPerson():
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    return

# detects the person and returns the x,y and width and height
def detectPerson():
    # uncomment for image resize
    #frameGray = imutils.resize(frameGray, width=min(500, frameGray.shape[1]))
    (rects, weights) = hog.detectMultiScale(frameGray, winStride=(8, 8), padding=(8,8), scale=1.2)
    return rects

# draws the rectangles on the original frame
def drawRectangles(rects, frame):
    for (x,y,w,h) in rects:
        frame = cv2.rectangle(frame, (x,y), (x+w, y+h), (255,255,255))
    return frame

# justus
def calcPersonCenter(rect, imageSize):
    
    return

# stefan
def positionDroneOnPersonCenter(center, imageSize):
    
    return


#moritz
def turnLeft():
    return
def turnRight():
    return
def forward():
    return
def backward():
    return
def up():
    return
def down():
    return
def land():
    return

#Disclaimer: For this to run, you need to install imutils from pip: $ pip install imutils 
#inspired by https://www.pyimagesearch.com/2015/11/09/pedestrian-detection-opencv/
from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2
from cmath import rect

# initialise variables and parameters
hog = None
hSpeed = 1
rotSpeed = 1
moveSpeed = 1
videoPath = ''
maxHeight = 1
maxSpeed = 1
ithFrame = 1
i=0
videoPath = 0 #"testVideoStefan.mp4"
heightThreshold = 50 # pixels
forwardBackwardThreshold = 50 # pixels
leftRightThreshold = 50 # pixels
baseDistance = 0.5 # keep this between 0.1 and 0.9 please!

# main Method
def main():
    global i
    cap = cv2.VideoCapture(videoPath)
    while(cap.isOpened()):
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break  
        # Capture frame-by-frame
        ret,frame=cap.read()
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # drone video is 360 * 640 in size (height, width)
        imageSize = frame.shape
        if i%ithFrame == 0:
            rects = detectPerson(frameGray)
            frame = drawRectangles(rects, frame)        
            cv2.imshow('frame',frame)
            if len(rects) > 0:
                positionDroneOnPersonCenter(rects[0], imageSize)
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
    global hog
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    return

# detects the person and returns the x,y and width and height
def detectPerson(frame):
    # uncomment for image resize
    #frameGray = imutils.resize(frameGray, width=min(500, frameGray.shape[1]))
    (rects, weights) = hog.detectMultiScale(frame, winStride=(8, 8), padding=(8,8), scale=1.2)
    return rects

# draws the rectangles on the original frame
def drawRectangles(rects, frame):
    for (x,y,w,h) in rects:
        frame = cv2.rectangle(frame, (x,y), (x+w, y+h), (255,255,255))
    return frame

# justus
def calcPersonCenter(rect):
    x, y, w, h = rect
    centerX = x + w / 2
    centerY = y + h / 2
    return centerX, centerY


# stefan
def positionDroneOnPersonCenter(rect, imageSize):
    x,y = calcPersonCenter(rect)
    if x < (imageSize[1]/2) - leftRightThreshold:
        turnLeft()
    elif x > (imageSize[1]/2) + leftRightThreshold:
        turnRight()
    if y < (imageSize[0]/2) - heightThreshold:
        up()
    elif y > (imageSize[0]/2) + heightThreshold:
        down()
    x, y, w, h = rect
    if h > (imageSize[0] * baseDistance) + forwardBackwardThreshold:
        backward()
    elif h < (imageSize[0] * baseDistance) - forwardBackwardThreshold:
        forward()
    return


#moritz
def turnLeft():
    print "turning left"
    return
def turnRight():
    print "turning right"
    return
def forward():
    print "moving forward"
    return
def backward():
    print "moving backwards"
    return
def up():
    print "moving up"
    return
def down():
    print "moving down"
    return
def land():
    print "landing"
    return


if __name__ == "__main__":

    #init(1, 1, 1, 'testVideoStefan.mp4', 1, 1, 1)
    initDetectPerson()
    main()

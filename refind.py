from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2
from cmath import rect
from cv2 import calcHist, compareHist, imread
from operator import add






#compare all the current rects with the base to detect which of them is the rect we are searching for
def refindPerson(baseFrame, baserect, frame, rects):
    print "entered refindPerson"
    x,y,w,h = baserect
    print "base_top coordinates are: y=" + str(y) + " bis y=" + str(y+h/2) + ", x=" + str(x) + " bis x: " + str(x+w/2)
    base_top = baseFrame[y:y+h/2, x:x+w/2]
    print "base_bottom coordinates are: y=" + str(y+h/2) + " bis y=" + str(y+h) + ", x=" + str(x+w/2) + " bis x: " + str(x+w)
    base_bottom = frame[y+h/2:y+h, x+w/2:x+w]
    basehist_top = calcHist(top)
    basehist_bottom = calcHist(bottom)
    hists_top = []
    hists_bottom = []
    histscores_top = []
    histscores_bottom = []
    for rect in rects:
        x,y,w,h = rect
        print "top coordinates are: y=" + str(y) + " bis y=" + str(y+h/2) + ", x=" + str(x) + " bis x: " + str(x+w/2)
        top = frame[y:y+h/2, x:x+w/2]
        print "bottom coordinates are: y=" + str(y+h/2) + " bis y=" + str(y+h) + ", x=" + str(x+w/2) + " bis x: " + str(x+w)
        bottom = frame[y+h/2:y+h, x+w/2:x+w]
        hist_top = calcHist(top)
        hist_bottom = calcHist(bottom)
        hists_top.append(hist_top)
        hists_bottom.append(hist_bottom)
    for hist_top in hists_top:
        histscores_top.append(compareHist(hist_top, basehist_top, 1))
    print "histscores_top: " + histscores_top
    for hist_bottom in hists_bottom:
        histscores_bottom.append(compareHist(hist_bottom, basehist_bottom, 1))
    print "histscores_bottom: " + histscores_bottom
    histscores = map(add, histscores_top, histscores_bottom)
    print "histscores total: " + histscores
    if (max(histscores < 0.9)):
        print "seems like no entry in histscores is above 0.9"
        return False
    else:
        print "there are entries above 0.9! returning tha rect with the highest score"
        return rects[histscores.index(max(histscores))]
    print "when you can read this, the world is destroyed"
    return False
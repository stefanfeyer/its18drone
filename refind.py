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
    base_top = baseFrame[y:y+h/2, x:x+w]
    base_bottom = frame[y+h/2:y+h, x:x+w]
    basehist_top = calcHist([base_top], [0], None, [256], [0, 256])
    basehist_bottom = calcHist([base_bottom], [0], None, [256], [0, 256])
    hists_top = []
    hists_bottom = []
    histscores_top = []
    histscores_bottom = []

    for rect in rects:
        x,y,w,h = rect
        top = frame[y:y+h/2, x:x+w]
        bottom = frame[y+h/2:y+h, x:x+w]
        hist_top = calcHist([top], [0], None, [256], [0, 256])
        hist_bottom = calcHist([bottom], [0], None, [256], [0, 256])
        hists_top.append(hist_top)
        hists_bottom.append(hist_bottom)

    for hist_top in hists_top:
        histscores_top.append(compareHist(hist_top, basehist_top, cv2.HISTCMP_BHATTACHARYYA))

    for hist_bottom in hists_bottom:
        histscores_bottom.append(compareHist(hist_bottom, basehist_bottom, cv2.HISTCMP_BHATTACHARYYA))

    histscores = [sum(x) for x in zip(histscores_top, histscores_bottom)]
    print histscores
    if histscores == [] or max(histscores) > 1.5:
        print "seems like no entry in histscores is above 0.9"
        return []
    else:
        print "there are entries above 0.9! returning tha rect with the highest score"
        print max(histscores)
        return rects[histscores.index(max(histscores))]
    print "when you can read this, the world is destroyed"
    return False
#hist3 = cv2.calcHist([image], [0], None, [256], [0,256])
#hist4 = cv2.calcHist([image], [1], None, [256], [0,256])
#hist5 = cv2.calcHist([image], [2], None, [256], [0,256])
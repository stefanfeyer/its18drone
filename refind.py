from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2
from cmath import rect
from cv2 import calcHist, compareHist
from operator import add




#compare all the current rects with the base to detect which of them is the rect we are searching for
def refindPerson(baseFrame, baserect, frame, rects):
    x,y,w,h = baserect
    base_top = baseFrame[y:y+h/2, x:x+w/2]
    base_bottom = frame[y+h/2:y+h/2, x+w/2:x+w/2]
    basehist_top = calcHist(top)
    basehist_bottom = calcHist(bottom)
    hists_top = []
    hists_bottom = []
    histscores_top = []
    histscores_bottom = []
    for rect in rects:
        x,y,w,h = rect
        top = frame[y:y+h/2, x:x+w/2]
        bottom = frame[y+h/2:y+h/2, x+w/2:x+w/2]
        hist_top = calcHist(top)
        hist_bottom = calcHist(bottom)
        hists_top.append(hist_top)
        hists_bottom.append(hist_bottom)
    for hist_top in hists_top:
        histscores_top.append(compareHist(hist_top, basehist_top, 1))
    for hist_bottom in hists_bottom:
        histscores_bottom.append(compareHist(hist_bottom, basehist_bottom, 1))
    histscores = map(add, histscores_top, histscores_bottom)
    return histscores.index(max(histscores))
from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2
from cmath import rect
from cv2 import calcHist, compareHist, imread, COLOR_RGB2HSV, COLOR_RGB2GRAY
from operator import add
import matplotlib.pyplot as plt


img1 = cv2.imread("testImages/51.jpg")
img2 = cv2.imread("testImages/101.jpg")
img1 = cv2.cvtColor(img1, COLOR_RGB2GRAY)
img2 = cv2.cvtColor(img2, COLOR_RGB2GRAY)


hist1 = cv2.calcHist([img1], [0], None, [255], [0,255])
hist2 = cv2.calcHist([img2], [0], None, [255], [0,255])
bhatta = compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
chi = compareHist(hist1, hist2, cv2.HISTCMP_CHISQR)
chi_alt = compareHist(hist1, hist2, cv2.HISTCMP_CHISQR_ALT)
correl = compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
hellinger = compareHist(hist1, hist2, cv2.HISTCMP_HELLINGER)
intersect = compareHist(hist1, hist2, cv2.HISTCMP_INTERSECT)
kl_div = compareHist(hist1, hist2, cv2.HISTCMP_KL_DIV)
emd = cv2.EMDHistogramCostExtractor(hist1, hist2, cv2.DIST_L1)
print emd
print chi, chi_alt, correl, hellinger, intersect, kl_div


plt.figure(0)
plt.title("no shadow")
plt.plot(hist1)
plt.figure(1)
plt.title("shadow")
plt.plot(hist2)
#plt.show()

#cv2.imshow("asd", img1)
cv2.waitKey(0) 
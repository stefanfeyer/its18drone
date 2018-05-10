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
from numpy import shape


img1 = cv2.imread("testImages/2.jpg")
img2 = cv2.imread("testImages/3.jpg")
img1 = cv2.cvtColor(img1, COLOR_RGB2HSV)
img2 = cv2.cvtColor(img2, COLOR_RGB2HSV)


hist1 = cv2.calcHist([img1], [0], None, [180], [0,180])
hist2 = cv2.calcHist([img2], [0], None, [180], [0,180])
# normalize
bhatta = compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
chi = compareHist(hist1, hist2, cv2.HISTCMP_CHISQR)
chi_alt = compareHist(hist1, hist2, cv2.HISTCMP_CHISQR_ALT)
correl = compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
hellinger = compareHist(hist1, hist2, cv2.HISTCMP_HELLINGER)
intersect = compareHist(hist1, hist2, cv2.HISTCMP_INTERSECT)
kl_div = compareHist(hist1, hist2, cv2.HISTCMP_KL_DIV)
#print chi, chi_alt, correl, hellinger, intersect, kl_div
#print hist1.__class__
#print hist1.shape
hist1_indexed = np.zeros((len(hist1), 2), np.float32)
hist1_indexed[:,0] = hist1[:, 0]
hist1_indexed[:,1] = range(0,len(hist1))

hist2_indexed = np.zeros((len(hist2), 2), np.float32)
hist2_indexed[:,0] = hist2[:, 0]
hist2_indexed[:,1] = range(0,len(hist2))

#hist1.resize((len(hist1), 2))
#hist1 = np.resize(hist1, (len(hist1), 2))
#print hist1
#newHist1 = np.zeros((len(hist1), 2))
#newHist1[:,0] = hist1[0]
#print newHist1

emd = cv2.EMD(hist1_indexed, hist2_indexed, cv2.DIST_L1)
print emd



plt.figure(0)
plt.title("no shadow")
plt.plot(hist1)
plt.figure(1)
plt.title("shadow")
plt.plot(hist2)
#plt.show()

#cv2.imshow("asd", img1)
cv2.waitKey(0) 
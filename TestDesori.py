import numpy as np
import cv2, os, time, glob

with np.load('picamCalibration.npz') as data:
    mtx = data['mtx']
    dist = data['dist']
    img = cv2.imread('test.jpg')
    h, w = img.shape[:2]
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))

    dst = cv2.undistort(img,mtx,dist,None,newcameramtx)
    x,y,w,h = roi
    dst = dst[y:y+h, x:x+w]
    cv2.imwrite('result.jpg',dst)

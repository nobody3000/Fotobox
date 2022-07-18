import numpy as np
import cv2, os, time, glob

POINTS_X = 6
POINTS_Y = 9

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

#prepare object points
objp = np.zeros((POINTS_X*POINTS_Y,3),np.float32)
objp[:,:2] = np.mgrid[0:POINTS_Y,0:POINTS_X].T.reshape(-1,2)

#Arrays to store object points and image points
objpoints = []
imgpoints = []

images = glob.glob('CalibrationImages/*.jpg')

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    ret, corners = cv2.findChessboardCorners(gray, (POINTS_Y, POINTS_X), None)
    
    if ret == True:
        objpoints.append(objp)
        
        cv2.cornerSubPix(gray, corners,(11,11),(-1,-1),criteria)
        imgpoints.append(corners)
        
        #Draw and display the corners
        cv2.drawChessboardCorners(img, (POINTS_Y, POINTS_X), corners, ret)
        img1 = cv2.resize(img, (1024,768))
        cv2.imshow('img',img1)
        cv2.waitKey(500)
        
cv2.destroyAllWindows()

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

np.savez('picamCalibration.npz', mtx=mtx, dist=dist) 
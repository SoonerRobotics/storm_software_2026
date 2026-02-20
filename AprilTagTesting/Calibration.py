import numpy as np
import cv2 as cv
import glob
import os

#Ignore this file, I'm trying to use this to get better camera calibration
#but we'll see if it works 
#(WIP)
#
#



# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((6*9,3), np.float32)
objp[:,:2] = np.mgrid[0:9,0:6].T.reshape(-1,2) * 0.01746

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

script_dir = os.path.dirname(os.path.abspath(__file__))
pattern = os.path.join(script_dir, '*.jpg')   # or use a subfolder if images are there
images = glob.glob(pattern)

#images = glob.glob('*.jpg')

for fname in images:
    
    img = cv.imread(fname)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # Find the chess board corners
    ret, corners = cv.findChessboardCorners(gray, (9,6), None)

    # If found, add object points, image points (after refining them)
    if ret == True:
        objpoints.append(objp)

        corners2 = cv.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
        imgpoints.append(corners2)

        # Draw and display the corners
        cv.drawChessboardCorners(img, (9,6), corners2, ret)
        cv.imshow('img', img)
        ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

        img = cv.imread(fname)
        h,  w = img.shape[:2]
        newcameramtx, roi = cv.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
        np.savetxt('calibration_matrix.txt', mtx)
        np.savetxt('distortion_coefficients.txt', dist)

        # undistort
        dst = cv.undistort(img, mtx, dist, None, newcameramtx)
        

        # crop the image
        x, y, w, h = roi
        dst = dst[y:y+h, x:x+w]
        cv.imwrite('calibresult.png', dst)
        cv.waitKey(500)

cv.destroyAllWindows()


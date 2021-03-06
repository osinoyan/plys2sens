# -*- coding: utf-8 -*-
"""JOINT CALIBRATION

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wWbWXBZdy7s66PBYdsrcmSeQ2G1XOXVN
"""

import numpy as np
import cv2
import glob
from google.colab.patches import cv2_imshow


CHECKERBOARD = (4, 3)
# Defining the world coordinates for 3D points
objp = np.zeros((1, CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[0,:,:2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
# Arrays to store object points and image points from all the images.
imgpoints = [] # 2d points in image plane.
images = glob.glob('*.png')
# images = glob.glob('color_out_RS01.png')
# images = glob.glob('rs_color_out_RS01F.png')


# Creating vector to store vectors of 3D points for each checkerboard image
objpoints = []

matched = []

for fname in images:
    print(fname)
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    ret = False
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD)
    # print(ret)
    # print(corners)
    # If found, add object points, image points (after refining them)
    if ret == True:
        objpoints.append(objp)

        cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
        imgpoints.append(corners)


        matched.append(corners)
        # Draw and display the corners
        cv2.drawChessboardCorners(img, CHECKERBOARD, corners, ret)
        cv2_imshow(img)
        # cv2.waitKey(0)

cv2.destroyAllWindows()

print(matched)
matched[0] = np.reshape(matched[0], (-1, 2))
matched[1] = np.reshape(matched[1], (-1, 2))
print(matched[0].tolist())
print(matched[1].tolist())


# # input()
# # homography_cal(matched[0], matched[1])
# h, status = cv2.findHomography(matched[1], matched[0])
# print(h)
# print(status)

# """
# Performing camera calibration by 
# passing the value of known 3D points (objpoints)
# and corresponding pixel coordinates of the 
# detected corners (imgpoints)
# """
# ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)




print("\n\n")
dist [0][0]= 0
dist [0][1]= 0
dist [0][2]= 0
dist [0][3]= 0
dist [0][4]= 0
mtx = np.array([[500.,   0., 255.],
                [  0., 500., 175.],
                [  0.,   0.,   1.]
])
x = 0.0285
objp = np.array([
    [0, 0, 0], [0, x, 0],  [0, 2*x, 0],  [0, 3*x, 0],
    [x, 0, 0], [x, x, 0],  [x, 2*x, 0],  [x, 3*x, 0],
    [2*x, 0, 0], [2*x, x, 0],  [2*x, 2*x, 0],  [2*x, 3*x, 0]
], dtype='float32')

success, rvecs, tvecs, inlier = cv2.solvePnPRansac(objp, matched[0], mtx, dist)
print(success)
print(inlier)
print("rvecs :")
rmat = cv2.Rodrigues(rvecs)
print(rmat[0])
print("tvecs :")
print(tvecs)

RM = rmat[0]
TM = np.reshape(tvecs, (3))


success, rvecs, tvecs, inlier = cv2.solvePnPRansac(objp, matched[1], mtx, dist)
print(success)
print(inlier)
print("rvecs :")
rmat = cv2.Rodrigues(rvecs)
print(rmat[0])
print("tvecs :")
print(tvecs)

RR = rmat[0]
TR = np.reshape(tvecs, (3))



from numpy.linalg import inv
def threetofour(R, t):
    M = np.empty((4, 4))
    M[:3, :3] = R
    M[:3, 3] = t
    M[3, :] = [0, 0, 0, 1]
    return M
# POSE OF PMD ############################################
# rvecs :
# R=[[ 0.81058894 ,-0.03710603,  0.5844388 ],
#  [-0.03573947, -0.99926483, -0.01387439],
#  [ 0.58452396, -0.0096411 , -0.81131916]]
# # tvecs :
# t= [-0.08648946, 0.02283948, 0.33278516]
PR = threetofour(RR, TR)
# POSE OF RS ############################################
# rvecs :
# R = [[ 0.7278396 ,  0.04546999,  0.68423826],
#  [-0.03906095, -0.99343022 , 0.10756687],
#  [ 0.68463403 ,-0.10501842, -0.72128176]]
# # tvecs :
# t = [-0.1688793 , 0.02660257, 0.42485092]
PM = threetofour(RM, TM)

####
# iPR = inv(PR)
iPM = inv(PM)
# print(iPR)
print("\n")
P = PM@iPR

#################
np. set_printoptions(suppress=True)
print(P)

K = [[500,    0.         ,255],
        [  0.  ,       500 ,175],
        [  0.    ,       0.     ,      1.        ]]
K = threetofour(K, np.array([0, 0, 0]))
# a = np.array([ 56.290905, 206.05853, 1 ])
a = np.array([ 0, 0, 0 , 1])
# b = K@PR@a
# b = b[:-1]
# b = b/b[-1]
# print(b)
# print(PR@a)

for row in P:
    for e in row:
        print("{}, ".format(e), end='')
    print("")
print("\n")

from numpy.linalg import inv
def threetofour(R, t):
    M = np.empty((4, 4))
    M[:3, :3] = R
    M[:3, 3] = t
    M[3, :] = [0, 0, 0, 1]
    return M
# POSE OF PMD ############################################
# rvecs :
R=[[ 0.81058894 ,-0.03710603,  0.5844388 ],
 [-0.03573947, -0.99926483, -0.01387439],
 [ 0.58452396, -0.0096411 , -0.81131916]]
# tvecs :
t= [-0.08648946, 0.02283948, 0.33278516]
PR = threetofour(R, t)
# POSE OF RS ############################################
# rvecs :
R = [[ 0.7278396 ,  0.04546999,  0.68423826],
 [-0.03906095, -0.99343022 , 0.10756687],
 [ 0.68463403 ,-0.10501842, -0.72128176]]
# tvecs :
t = [-0.1688793 , 0.02660257, 0.42485092]
PM = threetofour(R, t)

####
iPR = inv(PR)
iPM = inv(PM)
print(iPR)
print("\n")
P = PM@iPR

#################
np. set_printoptions(suppress=True)
print(P)

K = [[500,    0.         ,255],
        [  0.  ,       500 ,175],
        [  0.    ,       0.     ,      1.        ]]
K = threetofour(K, np.array([0, 0, 0]))
# a = np.array([ 56.290905, 206.05853, 1 ])
a = np.array([ 0, 0, 0 , 1])
# b = K@PR@a
# b = b[:-1]
# b = b/b[-1]
# print(b)
# print(PR@a)

# from numpy.linalg import inv
# def threetofour(R, t):
#     M = np.empty((4, 4))
#     M[:3, :3] = R
#     M[:3, 3] = t
#     M[3, :] = [0, 0, 0, 1]
#     return M

# ##########################################
# KR = [[255.4643902,    0.         ,235.69261037],
#  [  0.  ,       274.73770083 ,194.39360203],
#  [  0.    ,       0.     ,      1.        ]]

# KR = threetofour(KR, np.array([0, 0, 0]))
# iKR = inv(KR)
# # print(KR)
# ###################################################
# R = np.array([[-0.04366289,  0.89736843, -0.43911668],
#  [-0.99746305, -0.06389254, -0.03138808],
#  [-0.05622295,  0.43663217,  0.89788158]])
# t = np.array([-2.77663589, 0.36072555, 6.26437664])
# TR = threetofour(R, t)
# iTR = inv(TR)
# # print(TR)
# #####################################################
# KM = np.array([[437.50401934 ,  0.     ,    211.83712482],
#  [  0.      ,   505.75218751, 186.37457331],
#  [  0.      ,     0.       ,    1.        ]])
# KM = threetofour(KM, np.array([0, 0, 0]))
# ###################################################
# R = np.array([[ 0.07289346 , 0.75267504, -0.65434458],
#  [-0.97914655 ,-0.07073661, -0.19044257],
#  [-0.18962749,  0.65458125,  0.73182293]])
# t = np.array([-4.7580272 ,0.64940414,16.38550343])
# TM = threetofour(R, t)
# ###################################################
# KMP = [[500,    0.         ,255],
#  [  0.  ,       500 ,175],
#  [  0.    ,       0.     ,      1.        ]]
# KMP = threetofour(KMP, np.array([0, 0, 0]))
# iKMP = inv(KMP)
# ###################################################

# T = iKMP@KM@TM@iTR@iKR@KMP
# # T = KM@TM@iTR@iKR
# np. set_printoptions(suppress=True)
# print(T)


###################################################
###################################################
###################################################
###################################################


# TR = np.empty((4, 4))
# R = np.array([[-0.04366289,  0.89736843, -0.43911668],
#  [-0.99746305, -0.06389254, -0.03138808],
#  [-0.05622295,  0.43663217,  0.89788158]])
# t = np.array([-2.77663589, 0.36072555, 6.26437664])
# TR[:3, :3] = R
# TR[:3, 3] = t
# TR[3, :] = [0, 0, 0, 1]
# print(TR)

import scipy.io
mat = scipy.io.loadmat('scene_000_depth.mat')
print(mat['depth_GT_radial'][200])
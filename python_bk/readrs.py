#####################################################################
# read .dmp files + .bag file and warp .bag into .dmp depth map     #
# 2021.07.22                                                        #
#####################################################################


# First import library
import pyrealsense2 as rs
# Import Numpy for easy array manipulation
import numpy as np
# Import OpenCV for easy image rendering
import cv2
# Import argparse for command-line options
import argparse
# Import os.path for file path manipulation
import os.path
from PIL import Image
import os
import struct


def readDmp(file, depthShift):
    # input:  [string] file name
    # output: list of {( [array of np.array(int)] 2D depth map , [array of np.array([int, int, int])] ) 2D color map}
    f = open(file, 'rb')

    flag = f.read(10).decode('ascii')[:9]
    print(flag)
    n_frame = struct.unpack('I', f.read(4))[0]
    print(n_frame)
    width = struct.unpack('I', f.read(4))[0]
    print(width)
    height = struct.unpack('I', f.read(4))[0]
    print(height)

    if flag != '_dmp_yee_':
        print('flag error.')
        exit(1)


    mapLen = width*height
    data = []
    max_dep = 0
    for frame in range(n_frame):
        print('processing frame [{:03d}] ...'.format(frame), end="\r")
        depthMap = struct.unpack('f'*mapLen, f.read(4*mapLen))
        colorMap = struct.unpack('B'*mapLen, f.read(mapLen))

        dep_array = np.zeros((height, width, 1), dtype=np.float32)
        rgb_array = np.zeros((height, width, 3), dtype=np.float32)
        # nearst neighbor
        for ih in range(height):
            for iw in range(width):
                dep = depthMap[ih*width + iw] / depthShift
                if dep > max_dep:
                    max_dep = dep
                red = float(colorMap[ih*width + iw]) / 255.0
                dep_array[ih][iw] = dep
                rgb_array[ih][iw] = np.array([red, red, red])
        data.append((dep_array, rgb_array))
    print('\nmax_dep: {}'.format(max_dep))

    header = (n_frame, width, height, max_dep)
    return header, data


def homography_cal():
    points1 = np.array([
                    [242, 336],
                    [242, 354],
                    [242, 373],
                    [242, 390],
                    [260, 330],
                    [260, 348],
                    [260, 367],
                    [259, 385],
                    [258, 403],
                    [322, 314],
                    [322, 330],
                    [320, 348],
                    [320, 363],
                    [302, 212],
                    [352, 212],
                    [482, 23],
                    [417, 35],
                    [266, 98],
                    ])
    points1 = np.column_stack((points1,np.ones(points1.shape[0]))).T

    # H = np.array([
    #         [1,0,0],
    #         [0,1,0],
    #         [0,0,1]
    #         ])


    # points2 = H@points1
    # print(points2)
    points2 = np.array([
                    [204, 290],
                    [204, 304],
                    [204, 321],
                    [204, 335],
                    [218, 285],
                    [218, 301],
                    [218, 315],
                    [218, 330],
                    [218, 346],
                    [266, 271],
                    [266, 285],
                    [266, 300],
                    [266, 313],
                    [243, 193],
                    [283, 192],
                    [379, 44],
                    [324, 52],
                    [209, 108],
                    ])

    p1 = points1[:-1,:].T
    # p2 = points2[:-1,:].T
    p2 = points2[:,:]

    # H = H.reshape((-1,1))

    A_up = np.column_stack((p1,np.ones(p1.shape[0]),np.zeros((p1.shape[0],3)),-p1[:,0]*p2[:,0],-p1[:,1]*p2[:,0],-p2[:,0]))
    A_below = np.column_stack((np.zeros((p1.shape[0],3)),p1,np.ones(p1.shape[0]),-p1[:,0]*p2[:,1],-p1[:,1]*p2[:,1],-p2[:,1]))

    A = np.vstack((A_up,A_below))

    result = np.linalg.svd(A)[-1][-1]
    result = result/result[-1]
    result = result.reshape((p1.shape[1]+1,-1))
    print("The homography matrix calculated by the DLT algorithm is: \n",result)
    # print("The true value is: \ n",H.reshape((p1.shape[1]+1,-1)))
    return result


#####################################################################################

# Create object for parsing command-line options
parser = argparse.ArgumentParser(description="Read recorded bag file and display depth stream in jet colormap.\
                                Remember to change the stream fps and format to match the recorded.")
# Add argument which takes path to a bag file as an input

parser.add_argument('dmp', metavar='DIR', help='path to dataset')
parser.add_argument("bag", metavar='DIR', help="Path to the bag file")


if __name__ == "__main__":

    ##### ARGS #######################################
    # Parse the command line arguments to an object
    args = parser.parse_args()
    # Check if the given file have bag extension
    if os.path.splitext(args.bag)[1] != ".bag":
        print("The given file is not of correct file format.")
        print("Only .bag files are accepted")
        exit()
    
    ######### HOMOGRAPHY ################################
    H = homography_cal()

    ######### READ DMP ##################################
    # header, pmd_data = readDmp(args.dmp, 0.001) # convert m to mm
    # pmd_depth, pmd_color = pmd_data[0]
    # pmd_color = pmd_color*255
    # color_png = Image.fromarray(pmd_color.astype(np.uint8))
    # color_png = color_png.convert("RGB")
    # color_png.save('color_out.png')
    # print('output: color_out.png')
    # input()
    

    # pmd_depth_map = [frame[0] for frame in data]
    # print("pmd_depth: \n{}", pmd_depth_map)
    # input()

    ######### READ BAG ################################
    try:

        # Create pipeline
        pipeline = rs.pipeline()

        # Create a config object
        config = rs.config()

        # Tell config that we will use a recorded device from file to be used by the pipeline through playback.
        rs.config.enable_device_from_file(config, args.bag)

        # Configure the pipeline to stream the depth stream
        # Change this parameters according to the recorded bag file resolution
        config.enable_stream(rs.stream.depth, rs.format.z16, 15)

        # Start streaming from file
        pipeline.start(config)

        # Create colorizer object
        colorizer = rs.colorizer()

        # Streaming loop
        while True:
            # Get frameset of depth
            frames = pipeline.wait_for_frames()

            # Get depth frame
            depth_frame = frames.get_depth_frame()

            # Colorize depth frame to jet colormap
            # depth_color_frame = colorizer.colorize(depth_frame)

            # Convert depth_frame to numpy array to render image in opencv
            # depth_color_image = np.asanyarray(depth_color_frame.get_data())

            depth_array = np.asanyarray(depth_frame.get_data())

            width = 640
            height = 480

            points1 = []
            for ih in range(height):
                for iw in range(width):
                    points1.append([iw, ih])

            points1 = np.array(points1)
            points1 = np.column_stack((points1,np.ones(points1.shape[0]))).T

            points2 = (H@points1).T
            
            # print(points2)
            

            height_pmd = 350
            width_pmd = 450
            rs_dep_warped = [[[-10, -10, 0]] for i in range(height_pmd*width_pmd)]

            
            for ih in range(height):
                for iw in range(width):
                    p = points2[ih*width + iw]
                    p = p/p[-1]
                    p[-1] = depth_array[ih][iw]
                    if iw == 482 and ih == 23:
                        print('[{}][{}]->[{}][{}]'.format(iw, ih, p[0], p[1]))
                        input()
                    x = int(round(p[0], 0))
                    y = int(round(p[1], 0))
                    # CROP TO 450x350
                    if x in range(width_pmd) and y in range(height_pmd):
                        rs_dep_warped[y*width_pmd + x].append(p.tolist())
                    # points2[ip] = p
            
            for ih in range(height_pmd):
                for iw in range(width_pmd):
                    if len(rs_dep_warped[ih*width_pmd + iw]) <= 1:
                        rs_dep_warped[ih*width_pmd + iw] = 0
                        continue
                    candis = rs_dep_warped[ih*width_pmd + iw]
                    min_sqd_to_center = 0.25
                    result_d = 0
                    for px, py, d in candis:
                        # FIND NEAREST POINT
                        cur = (px-iw)*(px-iw) + (py-ih)*(py-ih)
                        if cur < min_sqd_to_center:
                            min_sqd_to_center = cur
                            result_d = d
                    rs_dep_warped[ih*width_pmd + iw] = result_d
            

            depth_png = np.reshape(rs_dep_warped, (height_pmd, width_pmd)) / 10
            depth_png = Image.fromarray(depth_png)
            depth_png = depth_png.convert("L")
            depth_png.save('test_out.png')
            print('output: test_out.png')
            # input()


            # # Render image in opencv window
            # cv2.imshow("Depth Stream", depth_color_image)
            # key = cv2.waitKey(1)
            # # if pressed escape exit program
            # if key == 27:
            #     cv2.destroyAllWindows()
            #     break

    finally:
        pass




'''
 [[ 2.42748485e+00 -1.00794196e-02  1.30204704e+02]
 [-2.50902968e-01  2.90014609e+00  1.32388254e+02]
 [-1.86331012e-04  6.13092674e-05  1.00000000e+00]]
'''
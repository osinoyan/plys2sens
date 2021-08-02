# from pipe.readrs import homography_cal
import matplotlib.pyplot as plt
import numpy as np
import cv2
import argparse
import os.path
from PIL import Image
import os
import struct


width = 450
height = 350


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
        # colorMap = struct.unpack('B'*3*mapLen, f.read(3*mapLen))  #REALSENSE
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
                # r = float(colorMap[ih*width*3 + iw*3 + 0])  #REALSENSE
                # g = float(colorMap[ih*width*3 + iw*3 + 1])  #REALSENSE
                # b = float(colorMap[ih*width*3 + iw*3 + 2])  #REALSENSE
                dep_array[ih][iw] = dep
                rgb_array[ih][iw] = np.array([red, red, red])
                # rgb_array[ih][iw] = np.array([r, g, b])  #REALSENSE
        data.append((dep_array, rgb_array))
    print('\nmax_dep: {}'.format(max_dep))

    header = (n_frame, width, height, max_dep)
    return header, data

def readDmpRS(file, depthShift):
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
        colorMap = struct.unpack('B'*3*mapLen, f.read(3*mapLen))  #REALSENSE
        # colorMap = struct.unpack('B'*mapLen, f.read(mapLen))

        dep_array = np.zeros((height, width, 1), dtype=np.float32)
        rgb_array = np.zeros((height, width, 3), dtype=np.float32)
        # nearst neighbor
        for ih in range(height):
            for iw in range(width):
                dep = depthMap[ih*width + iw] / depthShift
                if dep > max_dep:
                    max_dep = dep
                # red = float(colorMap[ih*width + iw]) / 255.0
                r = float(colorMap[ih*width*3 + iw*3 + 0])  #REALSENSE
                g = float(colorMap[ih*width*3 + iw*3 + 1])  #REALSENSE
                b = float(colorMap[ih*width*3 + iw*3 + 2])  #REALSENSE
                dep_array[ih][iw] = dep
                # rgb_array[ih][iw] = np.array([red, red, red])
                rgb_array[ih][iw] = np.array([r, g, b])  #REALSENSE
        data.append((dep_array, rgb_array))
    print('\nmax_dep: {}'.format(max_dep))

    header = (n_frame, width, height, max_dep)
    return header, data

def readPre(file):
    # input:  [string] file name
    # output: 
    f = open(file, 'rb')

    mapLen = width*height
    dep_array = np.zeros((height, width, 1), dtype=np.float32)
    for frame in range(1):
        depthMap = struct.unpack('f'*mapLen, f.read(4*mapLen))
        # nearst neighbor
        for ih in range(height):
            for iw in range(width):
                dep = depthMap[ih*width + iw]
                dep_array[ih][iw] = dep
    return dep_array

def colored(d):
    mxd = 0.05   # 5cm
    gradR = [255, 255, 0]
    gradG = [0, 255, 0]
    gradB = [0, 255, 255]
    
    if d > mxd: # > mxd
        r = gradR[0]
        g = gradG[0]
        b = gradB[0]
    elif d > 0: # 0 ~ mxd
        r = gradR[1] + (gradR[0]-gradR[1]) * d / mxd
        g = gradG[1] + (gradG[0]-gradG[1]) * d / mxd
        b = gradB[1] + (gradB[0]-gradB[1]) * d / mxd
    elif d == 0: # 0
        r = gradR[1]
        g = gradG[1]
        b = gradB[1]
    elif d >= -mxd: # -mxd ~ 0
        r = gradR[1] - (gradR[2]-gradR[1]) * d / mxd
        g = gradG[1] - (gradG[2]-gradG[1]) * d / mxd
        b = gradB[1] - (gradB[2]-gradB[1]) * d / mxd
    else: # < -mxd
        r = gradR[2]
        g = gradG[2]
        b = gradB[2]
    
    r = int(np.round(r, 0))
    g = int(np.round(g, 0))
    b = int(np.round(b, 0))
    return r, g, b

# Create object for parsing command-line options
parser = argparse.ArgumentParser(description="")

args = ['dmp', 
        'rs', 
        'preS',
        'preSR'
    ]

if 'rs' in args:
    parser.add_argument('rs', metavar='DIR', help='path to dmp')

if 'dmp' in args:
    parser.add_argument('dmp', metavar='DIR', help='path to dmp')

if 'preS' in args:
    parser.add_argument('preS', metavar='DIR', help='path to dmp')
    
if 'preSR' in args:
    parser.add_argument('preSR', metavar='DIR', help='path to dmp')

if __name__ == "__main__":

    args = parser.parse_args()

    if 'preS' in args:
        preS_depth = readPre(args.preS)    
    if 'preSR' in args:
        pre_depth = readPre(args.preSR)
    
    ######### READ RS ##################################
    if 'rs' in args:
        header, rs_data = readDmpRS(args.rs, 1)
        rs_depth, rs_color = rs_data[0]
        
        new_depth_png = []
        new_color_png = []
        for ih in range(height):
            for iw in range(width):
                dep = rs_depth[ih][iw]
                dep = dep * 100
                if dep > 255:
                    dep = 255
                new_depth_png.append(dep)
                r = rs_color[ih][iw][0]
                g = rs_color[ih][iw][1]
                b = rs_color[ih][iw][2]
                new_color_png.append(r)
                new_color_png.append(g)
                new_color_png.append(b)
                # print(new_color_png[-3:])
                # input()
    
        depth_png = Image.fromarray(np.reshape(new_depth_png, (height, width)))
        depth_png = depth_png.convert("L")
        depth_png.save('rs_depth_out.png')
        print('output: rs_depth_out.png')

        color_png = np.reshape(new_color_png, (height, width, 3))
        color_png = Image.fromarray(color_png.astype(np.uint8))
        color_png = color_png.convert("RGB")
        color_png.save('rs_color_out.png')
        print('output: rs_color_out.png')


    ######### READ DMP ##################################
    if 'dmp' in args:
        header, pmd_data = readDmp(args.dmp, 1)
        pmd_depth, pmd_color = pmd_data[0]
   
    
    ## PMD OUT COLOR ###################################
    # pmd_color = pmd_color*255
    # color_png = Image.fromarray(pmd_color.astype(np.uint8))
    # color_png = color_png.convert("RGB")
    # color_png.save('PMD_color_out.png')
    # print('output: PMD_color_out.png')
    # input()

    #### ERROR MAP (PMD - RS)###########################################
    err_map = []
    err_map_preSR = []
    err_map_preS = []
    abs_err = 0
    abs_err_preSR = 0
    abs_err_preS = 0
    # new_color_png = []
    for ih in range(height):
        for iw in range(width):
            err = pmd_depth[ih][iw] - rs_depth[ih][iw]
            err_preS = preS_depth[ih][iw] - rs_depth[ih][iw]
            err_preSR = pre_depth[ih][iw] - rs_depth[ih][iw]
            # ABSOLUTE ERROR SUM
            abs_err += abs(err)
            abs_err_preS += abs(err_preS)
            abs_err_preSR += abs(err_preSR)
            # r, g, b = colored(err)
            err_map.extend(colored(err))
            err_map_preS.extend(colored(err_preS))
            err_map_preSR.extend(colored(err_preSR))
    # ORIGINAL DEPTH ERROR MAP 
    out_err_map = np.reshape(err_map, (height, width, 3))
    out_err_map = Image.fromarray(out_err_map.astype(np.uint8))
    out_err_map = out_err_map.convert("RGB")
    filename = 'out_err_map.png'
    out_err_map.save(filename)
    print('output: {}'.format(filename))    
    # S DEPTH ERROR MAP 
    out_err_map = np.reshape(err_map_preS, (height, width, 3))
    out_err_map = Image.fromarray(out_err_map.astype(np.uint8))
    out_err_map = out_err_map.convert("RGB")
    filename = 'out_err_map_S.png'
    out_err_map.save(filename)
    print('output: {}'.format(filename))      
    # S+R DEPTH ERROR MAP 
    out_err_map = np.reshape(err_map_preSR, (height, width, 3))
    out_err_map = Image.fromarray(out_err_map.astype(np.uint8))
    out_err_map = out_err_map.convert("RGB")
    filename = 'out_err_map_R.png'
    out_err_map.save(filename)
    print('output: {}'.format(filename))

    mae = abs_err/(height*width)*100  # in cm
    mae_preSR = abs_err_preSR/(height*width)*100  # in cm
    mae_preS = abs_err_preS/(height*width)*100  # in cm
    print('MAE: {:.4f} cm.'.format(float(mae)))
    print('MAE preS: {:.4f} cm.'.format(float(mae_preS)))
    print('MAE preSR: {:.4f} cm.'.format(float(mae_preSR)))
    print('RE preS: {:.4f}% .'.format(float(mae_preS/mae*100)))
    print('RE preSR: {:.4f}% .'.format(float(mae_preSR/mae*100)))




    #########################################################
    y_0 = []
    y_1 = []
    y_3 = []
    y_4 = []
    sec = 175
    for i in range(0, 450):
        # print('[{}][{}]'.format(i, pmd_depth[175][i]))
        y_1.append(pmd_depth[sec][i][0])
        if 'rs' in args:
            y_0.append(rs_depth[sec][i])
        if 'preSR' in args:
            y_3.append(pre_depth[sec][i])
        if 'preS' in args:
            y_4.append(preS_depth[sec][i])
        
    
    y_2 = []
    # 00003_S2R100K
    # g0, g1, g2 = (83.0, 110.0, 79.0) 
    # x0, x1, x2 = (0, 129, 450)

    # 00004
    # g0, g1, g2 = (60, 91, 67) 
    # x0, x1, x2 = (0, 286, 450)

    # 00005
    g0, g1, g2 = (62.0, 121.0, 50.0) 
    x0, x1, x2 = (0, 242, 450)

    for i in range(x0, x2):
        d = 0
        if i in range(x0, x1):
            d = g0 + (i-x0)*(g1-g0)/(x1-x0)
        elif i in range(x1, x2):
            d = g1 + (i-x1)*(g2-g1)/(x2-x1)
        y_2.append(d/100)


    ######### PLOT #######################################

    x = range(0, 450)

    Data_1, = plt.plot(x, y_1, 'r-', label='ToF depth') #畫線
    # Data_2, = plt.plot(x, y_2, 'g-', label='Gronud-truth depth') #畫線
    if 'preS' in args:
        Data_4, = plt.plot(x, y_4, 'y--', label='SHARP-Net (S) depth') #畫線

    if 'preSR' in args:
        Data_3, = plt.plot(x, y_3, 'b--', label='SHARP-Net (S+R3E) depth') #畫線
   
    if 'rs' in args:
        Data_0, = plt.plot(x, y_0, 'g-', label='REALSENSE depth') #畫線
   
    plt.title("Depth Profile", fontsize=18) #圖表標題
    plt.tick_params(axis='both', labelsize=12, color='green')
    handles = [
        Data_1, 
        # Data_2
        ]
    if 'preS' in args:
        handles.append(Data_4)
    if 'preSR' in args:
        handles.append(Data_3)
    if 'rs' in args:
        handles.append(Data_0)
    plt.legend(handles=handles)
    # 00003
    # plt.axis([0, 450, 0.71, 1.15])
    # 00004
    # plt.axis([0, 450, 0.55, 1.0])
    # 00005
    # plt.axis([200, 300, 0.8, 1.25])
    # plt.axis([100, 350, 0.90, 1.25])
    # RS
    plt.axis([0, 450, 0.35, 0.7])
    plt.ylabel("depth(m)", fontsize=16) #y軸標題
    plt.savefig('testChart.png', bbox_inches='tight')




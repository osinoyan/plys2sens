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

# Create object for parsing command-line options
parser = argparse.ArgumentParser(description="")

parser.add_argument('dmp', metavar='DIR', help='path to dmp')
# parser.add_argument('preSR', metavar='DIR', help='path to dmp')
# parser.add_argument('preS', metavar='DIR', help='path to dmp')

if __name__ == "__main__":

    args = parser.parse_args()

    pre_depth = readPre(args.preSR)
    preS_depth = readPre(args.preS)
    
    ######### READ DMP ##################################
    header, pmd_data = readDmp(args.dmp, 1)
    pmd_depth, pmd_color = pmd_data[0]    
    
    # pmd_color = pmd_color*255
    # color_png = Image.fromarray(pmd_color.astype(np.uint8))
    # color_png = color_png.convert("RGB")
    # color_png.save('color_out.png')
    # print('output: color_out.png')
    # input()


    y_1 = []
    y_3 = []
    y_4 = []
    for i in range(135, 411):
        # print('[{}][{}]'.format(i, pmd_depth[175][i]))
        y_1.append(pmd_depth[175][i][0])
        y_3.append(pre_depth[175][i])
        y_4.append(preS_depth[175][i])
        
    
    y_2 = []
    for i in range(135, 411):
        d = 0
        if i in range(135, 147):
            d = 44.5 + (i-135)*(43.8-44.5)/(147-135)
        elif i in range(147, 230):
            d = 43.8 + (i-147)*(62.5-43.8)/(230-147)
        elif i in range(230, 411):
            d = 62.5 + (i-230)*(55.5-62.5)/(411-230)
        y_2.append(d/100)


    ######### PLOT #######################################

    x = range(135, 411)

    Data_1, = plt.plot(x, y_1, 'r-', label='ToF depth') #畫線
    Data_2, = plt.plot(x, y_2, 'g-', label='Gronud-truth depth') #畫線
    Data_3, = plt.plot(x, y_3, 'b--', label='SHARP-Net (S+R100K) depth') #畫線
    Data_4, = plt.plot(x, y_4, 'm--', label='SHARP-Net (S) depth') #畫線

    plt.title("Depth Profile", fontsize=18) #圖表標題
    plt.tick_params(axis='both', labelsize=12, color='green')
    plt.legend(handles=[Data_1, Data_2, Data_3, Data_4])
    plt.ylabel("depth(m)", fontsize=16) #y軸標題
    plt.savefig('testChart.png', bbox_inches='tight')
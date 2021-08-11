# from pipe.readrs import homography_cal
import matplotlib.pyplot as plt
import numpy as np
import cv2
import argparse
import os.path
from PIL import Image
import os
import struct
from datetime import datetime

n = datetime.now()
now_str = '{}-{}-{}  {}:{}:{}'.format(
    n.year, n.month, n.day, n.hour, n.minute, n.second)

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
    if d == -1000:
        return 0, 0, 0
    # mxd = 0.05   # 5cm
    # mxd = 0.10   # 10cm
    mxd = 0.20   # 20cm
    
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

def colored_r(d, max, min):
    if d == -1000:
        return 0, 0, 0
    # max, min = 0.40, 0.30
    # max, min = 0.20, 0.00
    
    gradDR = [127,   0,   0]
    gradR  = [255,   0,   0]
    gradO  = [255, 127,   0]
    gradY  = [255, 255,   0]
    gradYG = [127, 255,   0]
    gradG  = [  0, 255,   0]
    gradGB = [  0, 255, 255]
    gradB  = [  0,   0, 255]
    gradDB = [  0,   0, 127]
    
    grad = [gradDB, gradB, gradGB, gradG, gradYG,
            gradY, gradO, gradR, gradDR]

    d_range = list(range(9))
    d_range = [d_crr*(max-min)/8+min for d_crr in d_range]

    if d >= d_range[8]:
        r, g, b = gradDR
    elif d < d_range[0]:
        r, g, b = gradDB
    else:
        for i in [8, 7, 6, 5, 4, 3, 2, 1]:
            if d >= d_range[i-1]:
                d1, d0 = d_range[i], d_range[i-1]
                r1, g1, b1 = grad[i]
                r0, g0, b0 = grad[i-1]
                step = (d-d0) / (d1-d0)
                r = r0 + (r1-r0) * step
                g = g0 + (g1-g0) * step
                b = b0 + (b1-b0) * step
                break

    r = int(np.round(r, 0))
    g = int(np.round(g, 0))
    b = int(np.round(b, 0))
    return r, g, b

# Create object for parsing command-line options
parser = argparse.ArgumentParser(description="")

rs_color_out = False
pmd_color_out = False
pmd_depth_out = False
eval_mae_re = False
test_chart = False


# rs_color_out = True
# pmd_color_out = True
# pmd_depth_out = True
eval_mae_re = True
# test_chart = True

config = ['dmp',
        # 'gt',
        'rs',
        'preS',
        'preSR'
    ]

if 'rs' in config:
    parser.add_argument('rs', metavar='DIR', help='path to dmp')

if 'dmp' in config:
    parser.add_argument('dmp', metavar='DIR', help='path to dmp')

if 'preS' in config:
    parser.add_argument('preS', metavar='DIR', help='path to dmp')

if 'preSR' in config:
    parser.add_argument('preSR', metavar='DIR', help='path to dmp')

if __name__ == "__main__":

    args = parser.parse_args()

    if 'preS' in config:
        preS_depth = readPre(args.preS)    
    if 'preSR' in config:
        pre_depth = readPre(args.preSR)
    
    ######### READ RS ##################################
    if 'rs' in config:
        header, rs_data = readDmpRS(args.rs, 1)
        rs_depth, rs_color = rs_data[0]
        rs_name = args.rs.split('.ply.')[-2].split('/')[-1]
        
    if 'rs' in config and rs_color_out:
        new_depth_png = []
        new_color_png = []
        for ih in range(height):
            for iw in range(width):
                dep = rs_depth[ih][iw]
                # new_depth_png.extend(colored_r(ih, 350.0, 0.0))
                new_depth_png.extend(colored_r(dep, 2.0, 0.6))
                new_color_png.extend(rs_color[ih][iw])
                # print(new_color_png[-3:])
                # input()

        depth_png = np.reshape(new_depth_png, (height, width, 3))
        depth_png = Image.fromarray(depth_png.astype(np.uint8))
        depth_png = depth_png.convert("RGB")
        output_name = 'depth_{}.png'.format(rs_name)
        depth_png.save(output_name)
        print(output_name)

        # color_png = np.reshape(new_color_png, (height, width, 3))
        # color_png = Image.fromarray(color_png.astype(np.uint8))
        # color_png = color_png.convert("RGB")
        # output_name = 'color_{}.png'.format(rs_name)
        # color_png.save(output_name)
        # print(output_name)
   
    ######### READ DMP ##################################
    if 'dmp' in config:
        header, pmd_data = readDmp(args.dmp, 1)
        pmd_depth, pmd_color = pmd_data[0]
        pmd_name = args.dmp.split('.dmp')[-2].split('/')[-1]
    
    if pmd_depth_out:
        new_depth_png = []
        for ih in range(height):
            for iw in range(width):
                dep = pmd_depth[ih][iw]
                new_depth_png.extend(colored_r(dep, 2.0, 0.5))

        depth_png = np.reshape(new_depth_png, (height, width, 3))
        depth_png = Image.fromarray(depth_png.astype(np.uint8))
        depth_png = depth_png.convert("RGB")
        output_name = 'depth_{}.png'.format(pmd_name)
        depth_png.save(output_name)
        print(output_name)

    if pmd_color_out:
        pmd_color = pmd_color*255
        color_png = Image.fromarray(pmd_color.astype(np.uint8))
        color_png = color_png.convert("RGB")
        output_name = 'color_{}.png'.format(pmd_name)
        color_png.save(output_name)
        print(output_name)

    #### ERROR MAP (PMD - RS)###########################################
    if 'rs' in config and eval_mae_re:
        err_map = []
        err_map_preSR = []
        err_map_preS = []
        abs_err = 0
        abs_err_preSR = 0
        abs_err_preS = 0
        # eps is 0.001 cm
        eps = 0.00001
        # new_color_png = []
        for ih in range(height):
            for iw in range(width):
                # ERROR SUM
                err = pmd_depth[ih][iw] - rs_depth[ih][iw]
                if rs_depth[ih][iw] < eps:
                    err = 0
                # if pmd_depth[ih][iw] < eps:
                #     err = 0
                abs_err += abs(err)
                if pmd_depth[ih][iw] < eps:
                    err = -1000
                err_map.extend(colored(err))
                if 'preS' in config:
                    err_preS = preS_depth[ih][iw] - rs_depth[ih][iw]
                    if rs_depth[ih][iw] < eps:
                        err_preS = 0
                    # if preS_depth[ih][iw] < eps:
                    #     err_preS = 0
                    abs_err_preS += abs(err_preS)
                    if preS_depth[ih][iw] < eps:
                        err_preS = -1000
                    err_map_preS.extend(colored(err_preS))
                if 'preSR' in config:
                    err_preSR = pre_depth[ih][iw] - rs_depth[ih][iw]
                    if rs_depth[ih][iw] < eps:
                        err_preSR = 0
                    # if pre_depth[ih][iw] < eps:
                    #     err_preSR = 0
                    abs_err_preSR += abs(err_preSR)
                    if pre_depth[ih][iw] < eps:
                        err_preSR = -1000
                    err_map_preSR.extend(colored(err_preSR))
        
        # ORIGINAL DEPTH ERROR MAP 
        out_err_map = np.reshape(err_map, (height, width, 3))
        out_err_map = Image.fromarray(out_err_map.astype(np.uint8))
        out_err_map = out_err_map.convert("RGB")
        output_name = 'out_err_{}.png'.format(pmd_name)
        out_err_map.save(output_name)
        print(output_name)

        # S DEPTH ERROR MAP 
        if 'preS' in config:
            out_err_map = np.reshape(err_map_preS, (height, width, 3))
            out_err_map = Image.fromarray(out_err_map.astype(np.uint8))
            out_err_map = out_err_map.convert("RGB")
            output_name = 'out_err_S_{}.png'.format(pmd_name)
            out_err_map.save(output_name)
            print(output_name)

        # S+R DEPTH ERROR MAP 
        if 'preSR' in config:
            out_err_map = np.reshape(err_map_preSR, (height, width, 3))
            out_err_map = Image.fromarray(out_err_map.astype(np.uint8))
            out_err_map = out_err_map.convert("RGB")
            output_name = 'out_err_R_{}.png'.format(pmd_name)
            out_err_map.save(output_name)
            print(output_name)

        f = open("out_eval.txt", "a")
        f.write('--------------------------------\n')
        f.write('[{}] '.format(pmd_name))
        f.write(now_str + '\n')

        mae = abs_err/(height*width)*100  # in cm
        print('MAE: {:.4f} cm.'.format(float(mae)))
        f.write('MAE: {:.4f} cm.\n'.format(float(mae)))
        if 'preS' in config:
            mae_preS = abs_err_preS/(height*width)*100  # in cm
            print('MAE preS: {:.4f} cm.'.format(float(mae_preS)))
            f.write('MAE preS: {:.4f} cm.\n'.format(float(mae_preS)))
            print('RE preS: {:.4f}% .'.format(float(mae_preS/mae*100)))
            f.write('RE preS: {:.4f}% .\n'.format(float(mae_preS/mae*100)))
        if 'preSR' in config:
            mae_preSR = abs_err_preSR/(height*width)*100  # in cm
            print('MAE preSR: {:.4f} cm.'.format(float(mae_preSR)))
            f.write('MAE preSR: {:.4f} cm.\n'.format(float(mae_preSR)))
            print('RE preSR: {:.4f}% .'.format(float(mae_preSR/mae*100)))
            f.write('RE preSR: {:.4f}% .\n'.format(float(mae_preSR/mae*100)))

        f.close()
    ##### TEST CHART ###################################
    if test_chart:
        y_0 = []
        y_1 = []
        y_3 = []
        y_4 = []

        # VERTICAL
        sec = 97
        # x = range(0, 350)
        # for i in x:
        #     # print('[{}][{}]'.format(i, pmd_depth[175][i]))
        #     y_1.append(pmd_depth[i][sec][0])
        #     if 'rs' in args:
        #         y_0.append(rs_depth[i][sec])
        #     if 'preSR' in args:
        #         y_3.append(pre_depth[i][sec])
        #     if 'preS' in args:
        #         y_4.append(preS_depth[i][sec])
        
        # HORRIZONTAL
        sec = 175
        x = range(0, 450)
        for i in x:
            # print('[{}][{}]'.format(i, pmd_depth[175][i]))
            y_1.append(pmd_depth[sec][i][0])
            if 'rs' in args:
                y_0.append(rs_depth[sec][i])
            if 'preSR' in args:
                y_3.append(pre_depth[sec][i])
            if 'preS' in args:
                y_4.append(preS_depth[sec][i])
            
        
        y_2 = []

        
        # 00001
        g0, g1, g2 = (14, 62.5, 53) 
        x0, x1, x2 = (0, 230, 450)

        # 00003_S2R100K
        # g0, g1, g2 = (83.0, 110.0, 79.0) 
        # x0, x1, x2 = (0, 129, 450)

        # 00004
        # g0, g1, g2 = (60, 91, 67) 
        # x0, x1, x2 = (0, 286, 450)

        # 00005
        # g0, g1, g2 = (54.8, 56.0, 56.0) 
        # x0, x1, x2 = (0, 225, 450)

        for i in range(x0, x2):
            d = 0
            if i in range(x0, x1):
                d = g0 + (i-x0)*(g1-g0)/(x1-x0)
            elif i in range(x1, x2):
                d = g1 + (i-x1)*(g2-g1)/(x2-x1)
            y_2.append(d/100)


        ######### PLOT #######################################

        Data_1, = plt.plot(x, y_1, 'r-', label='ToF depth') #畫線
        
        if 'gt' in config:
            Data_2, = plt.plot(x, y_2, 'g-', label='Gronud-truth depth') #畫線   
        
        if 'preS' in config:
            Data_4, = plt.plot(x, y_4, 'y--', label='SHARP-Net depth') #畫線

        if 'preSR' in config:
            Data_3, = plt.plot(x, y_3, 'b--', label='SHARP-Net (+R) depth') #畫線
    
        if 'rs' in config:
            Data_0, = plt.plot(x, y_0, 'g-', label='REALSENSE depth') #畫線
    
        plt.title("Depth Profile", fontsize=18) #圖表標題
        plt.tick_params(axis='both', labelsize=12, color='green')
        handles = [Data_1]
        if 'gt' in config:
            handles.append(Data_2)
        if 'preS' in config:
            handles.append(Data_4)
        if 'preSR' in config:
            handles.append(Data_3)
        if 'rs' in config:
            handles.append(Data_0)
        plt.legend(handles=handles)
        
        # 00001
        # plt.axis([150, 409, 0.44, 0.64])

        # 00003
        # plt.axis([0, 450, 0.71, 1.15])
        # 00004
        # plt.axis([0, 450, 0.55, 1.0])
        # 00005
        # plt.axis([100, 350, 0.9, 1.25])
        # 00006
        # plt.axis([50, 400, 0.2, 0.8])
        # RS
        # plt.axis([0, 450, 0.35, 0.7])
        plt.ylabel("depth(m)", fontsize=16) #y軸標題
        plt.savefig('testChart.png', bbox_inches='tight')




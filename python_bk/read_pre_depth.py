############################################################################
#  2021/04/12   read .pgm files and convert to png files                   #
############################################################################
import argparse
import cv2
import struct
import numpy as np
import os
from os import listdir
from os.path import isfile, join

parser = argparse.ArgumentParser(description='pre_depth reader')
parser.add_argument('data', metavar='DIR',
                    help='path to data')


def read_dir(path):
    """
    input: path to pre_depth files
    void: convert pre_depth files to .pngs
    """
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    onlyfiles = sorted([int(file) for file in onlyfiles])
    onlyfiles = [str(file) for file in onlyfiles]

    if path[-1] != '/':
        path.append('/')
    outPath = './pre_depth'
    if not os.path.exists(outPath):
        os.makedirs(outPath)

    for file in onlyfiles:
        file_path = join(path, file)
        height, width, depthMap = read_depth(file_path)
        outFile = outPath + '/{}.png'.format(file)
        conver2png(height, width, depthMap, outFile)
        input()


def read_depth(file):
    # f = open(file, 'rb')
    height = 384
    width = 512
    dmap = np.fromfile(file, dtype=np.float32)
    return height, width, dmap


def conver2png(height, width, depthMap, outFile):
    # input: arr (2D-array)
    img_array = np.zeros((350, 450, 3), dtype=int)
    # depthRange = 2  # 0~2 meter
    # nearst neighbor
    for ih in range(height):
        for iw in range(width):
            oh = ih - 17
            ow = iw - 31
            isPadding = (oh < 0) or (oh >= 350) or (ow < 0) or (ow >= 450)
            if isPadding:
                continue

            rgb = depthMap[ih*width + iw]
            # print(rgb)
            # input()
            rgb = int(rgb*100)
            
            # print(rgb)
            # input()
            rgb = 0 if rgb < 0 else rgb
            rgb = 255 if rgb > 255 else rgb
            img_array[oh][ow] = np.array([rgb, rgb, rgb])
    # outFile = 'frame-000000.png'
    print(outFile)
    cv2.imwrite(outFile, img_array)


if __name__ == "__main__":
    args = parser.parse_args()
    read_dir(args.data)

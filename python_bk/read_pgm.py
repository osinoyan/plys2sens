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

parser = argparse.ArgumentParser(description='pgm reader')
parser.add_argument('data', metavar='DIR',
                    help='path to dataset')


def read_pgms(path):
    """
    input: path to .pgm files
    void: convert .pgm files to .pngs
    """
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    onlyfiles = sorted(onlyfiles)

    if path[-1] != '/':
        path.append('/')
    outPath = './pgm_{}'.format(path.split('/')[-2])
    if not os.path.exists(outPath):
        os.makedirs(outPath)

    for file in onlyfiles:
        file_path = join(path, file)
        height, width, depthMap = read_pgm(file_path)
        outFile = outPath + '/{}.png'.format(file.split('.')[-3])
        conver2png(height, width, depthMap, outFile)


def read_pgm(file):
    """Return a raster of integers from a PGM as a list of lists."""
    pgmf = open(file, 'rb')
    ass = pgmf.readline().decode('ascii')
    assert ass == 'P5\n'

    pgmf.readline()
    ass = pgmf.readline().decode('ascii')
    (width, height) = [int(i) for i in ass.split()]
  
    # ass = pgmf.readline().decode('ascii')
    x = pgmf.read(5)

    raster = []
    for y in range(height):
        row = []
        for y in range(width):
            # x = struct.unpack('H', pgmf.read(2))[0]
            # print(x)
            # input()
            row.append(struct.unpack('H', pgmf.read(2))[0])
        raster.append(row)
    # print(raster)
    return height, width, raster


def conver2png(height, width, depthMap, outFile):
    # input: arr (2D-array)
    img_array = np.zeros((height, width, 3), dtype=int)
    # depthRange = 2  # 0~2 meter
    # nearst neighbor
    for iw in range(width):
        for ih in range(height):
            rgb = depthMap[ih][iw]
            # print(rgb)
            # input()
            rgb = int(rgb*255/65535*30)
            
            # print(rgb)
            # input()
            rgb = 0 if rgb < 0 else rgb
            rgb = 255 if rgb > 255 else rgb
            img_array[ih][iw] = np.array([rgb, rgb, rgb])
    # outFile = 'frame-000000.png'
    print(outFile)
    cv2.imwrite(outFile, img_array)


if __name__ == "__main__":
    args = parser.parse_args()
    read_pgms(args.data)
    # height, width, depthMap = read_pgm(args.data)
    # conver2png(height, width, depthMap)
    # img_array = convertTo2D(points)
    # cv2.imwrite('output.png', img_array)

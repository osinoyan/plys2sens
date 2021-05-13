############################################################################
#  2021/03/30   read .dmp file and convert to png                          #
############################################################################
import argparse
import cv2
import struct
import numpy as np
import os

parser = argparse.ArgumentParser(description='dmp reader')
parser.add_argument('data', metavar='DIR',
                    help='path to dataset')
width = 450
height = 350
fx = 500
fy = 500
cx = 225
cy = 175


def readDmp(file):
    # input:  [string] file name
    # output: [array of np.array([int, int, int])] 2D depth map
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

    out_path = './out_{}'.format(file.split('/')[-1].split('.')[0])
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    for frame in range(n_frame):
        print('processing frame [{:03d}] ...'.format(frame))
        depthMap = struct.unpack('f'*mapLen, f.read(4*mapLen))
        colorMap = struct.unpack('B'*mapLen, f.read(mapLen))

        img_array = np.zeros((height, width, 3), dtype=int)
        depthRange = 1  # 0~2 meter
        # nearst neighbor
        for iw in range(width):
            for ih in range(height):
                rgb = depthMap[ih*width + iw]
                # print(rgb)
                # input()
                rgb = int(rgb * 100)
                rgb = 0 if rgb < 0 else rgb
                rgb = 255 if rgb > 255 else rgb
                img_array[ih][iw] = np.array([rgb, rgb, rgb])
        outFile = '{}/{:03d}.png'.format(out_path, frame)
        print(outFile)
        cv2.imwrite(outFile, img_array)


def convertTo2D(points):
    projectedPoints = []
    for point in points:
        tx, ty, tz = point['x'], point['y'], point['z']
        if tz == 0:
            continue
        # perspective
        tx = tx * fx / tz
        ty = ty * fy / tz
        # for drawing png
        tx = tx + cx
        ty = ty + cy
        projectedPoints.append({
            'x': tx, 'y': ty,
            'z': tz, 'red': point['red']
        })
    img_array = np.zeros((height, width, 3), dtype=int)
    # nearst neighbor
    for iw in range(width):
        for ih in range(height):
            nearestPoint = projectedPoints[0]
            gr = 2  # grid radius
            MXDist = gr * gr * 2 + 1  # out of a grid
            curSqrDist = MXDist
            for point in projectedPoints:
                px, py, pz = point['x'], point['y'], point['z']
                # whether the point in gr x gr grid
                if (px > iw - gr and px < iw + gr and py > ih - gr and py < ih + gr):
                    sqrDistToCenter = (px - iw) * (px - iw) + (py - ih) * (py - ih)
                    # find the nearest point to the center(iw, ih)
                    if sqrDistToCenter < curSqrDist:
                        curSqrDist = sqrDistToCenter
                        nearestPoint = point
            if curSqrDist < MXDist:
                rgb = int(nearestPoint['z'] * 255 / 7)
                rgb = 0 if rgb < 0 else rgb
                rgb = 255 if rgb > 255 else rgb
                img_array[ih][iw] = np.array([rgb, rgb, rgb])
    return img_array


if __name__ == "__main__":
    args = parser.parse_args()
    readDmp(args.data)
    # img_array = convertTo2D(points)
    # cv2.imwrite('output.png', img_array)

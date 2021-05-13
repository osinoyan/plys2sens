import argparse
import cv2
import numpy as np

parser = argparse.ArgumentParser(description='ply reader')
parser.add_argument('data', metavar='DIR',
                    help='path to dataset')
width = 450
height = 350
fx = 500
fy = 500
cx = 225
cy = 175


def readPly(file):
    # input:  [string] file name
    # output: [list of dic] 3D points
    f = open(file, 'r')
    while True:
        line = f.readline()
        if line == '':
            break
        if line.split('\n')[0] == 'end_header':
            break
    # read payload
    x = y = z = red = 0.0
    points = []
    while True:
        line = f.readline()
        if line == '':
            break
        words = line.split(' ')
        x, y, z = words[0:3]
        red = words[4]
        if not(x == 0 and y == 0 and z == 0):
            points.append({
                'x': float(x), 'y': float(y),
                'z': float(z), 'red': int(red)
            })
    return points


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
    points = readPly(args.data)
    img_array = convertTo2D(points)
    cv2.imwrite('output.png', img_array)

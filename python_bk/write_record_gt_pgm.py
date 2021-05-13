# read .dmp files and convert to multi-frame TFRecord
# with gound-truth obtained by BundleFusion .pgm files
import tensorflow as tf
import argparse
import numpy as np
import os
import cv2
import time
import struct
from os import listdir
from os.path import isfile, join

parser = argparse.ArgumentParser(description='dmp reader')
parser.add_argument('data', metavar='DIR',
                    help='path to dataset')
parser.add_argument('pgm', metavar='DIR',
                    help='path to pgm')

def _int64_feature(value):
    """Wrapper for inserting int64 features into Example proto."""
    if not isinstance(value, list):
        value = [value]
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def _bytes_feature(value):
    """Wrapper for inserting bytes features into Example proto."""
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def readDmp(file):
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

    header = (n_frame, width, height)

    mapLen = width*height
    data = []
    for frame in range(n_frame):
        print('processing frame [{:03d}] ...'.format(frame))
        depthMap = struct.unpack('f'*mapLen, f.read(4*mapLen))
        colorMap = struct.unpack('B'*mapLen, f.read(mapLen))

        img_array = np.zeros((height, width, 1), dtype=np.float32)
        img_array_3 = np.zeros((height, width, 3), dtype=np.float32)
        # depthRange = 2  # 0~2 meter
        # nearst neighbor
        for iw in range(width):
            for ih in range(height):
                dep = depthMap[ih*width + iw]
                # print(dep)
                # input()
                rgb = float(colorMap[ih*width + iw]) / 255.0
                img_array[ih][iw] = dep
                img_array_3[ih][iw] = np.array([rgb, rgb, rgb])
        data.append((img_array, img_array_3))
    return header, data


def read_pgm_data(path):
    """
    input: path to .pgm files
    output: list of {[array of np.array(int)] 2D depth map}
    """
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    onlyfiles = sorted(onlyfiles)

    data_pgm = []

    for file in onlyfiles:
        print('processing pgm [{}] ...'.format(file))
        file_path = join(path, file)
        height, width, depthMap = read_pgm(file_path)

        img_array = np.zeros((height, width, 1), dtype=np.float32)
        for iw in range(width):
            for ih in range(height):
                dep = float(depthMap[ih][iw]) / 1000
                img_array[ih][iw] = dep
        data_pgm.append(img_array)

    return data_pgm


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
            row.append(struct.unpack('H', pgmf.read(2))[0])
        raster.append(row)
    # print(raster)
    return height, width, raster


# write all example into one single tfrecords file
def write_tfRecord(
        header=None,
        data=None,
        data_pgm=None,
        label=None,
        file_name='test_yee.tfrecord'):
    """
    data: your data list or np.ndarray
    label: label list
    file_name: the tfrecord file storage data and label
    """
    n_frame, width, height = header
    
    if len(data_pgm) < n_frame:
        n_frame = len(data_pgm)

    # Compress the frames using JPG and store in as a list of strings
    # in 'frames'
    # here suppose we have 10 data with same shape [50,100,3], but
    # label has different length, eg. OCR task.
    with tf.python_io.TFRecordWriter(file_name) as writer:
        for i in range(n_frame):
            # prepare data and label
            # noisy_data = np.ones((height, width, 3), dtype=np.float32)  # np.ndarray
            img_array, img_array_3 = data[i]
            noisy_data = img_array  # np.ndarray
            noisy_data_3 = img_array_3  # np.ndarray

            gt_data = data_pgm[i]
            # label = list(np.arange(i+1))  # list of int

            features = {}  # each example has these features
            # features['label'] = _int64_feature(label)
            # 'label' is a feature of tf.train. BytesList
            features['noisy'] = _bytes_feature(noisy_data.tostring())
            features['intensity'] = _bytes_feature(noisy_data.tostring())
            features['rgb'] = _bytes_feature(noisy_data_3.tostring())
            features['gt'] = _bytes_feature(gt_data.tostring())

            # write serialized example into .tfrecords
            tfrecord_example = tf.train.Example(
                features=tf.train.Features(feature=features))
            writer.write(tfrecord_example.SerializeToString())


if __name__ == "__main__":
    args = parser.parse_args()
    header, data = readDmp(args.data)
    data_pgm = read_pgm_data(args.pgm)
    write_tfRecord(
        header=header,
        data=data,
        data_pgm=data_pgm,
        label=None,
        file_name='../datasets/tfrecords/yee/yee_eval.tfrecords'
    )

# read .dmp files and convert to multi-frame TFRecord
# with gound-truth obtained by BundleFusion .dmp files
# 2021.05.25
import tensorflow as tf
import argparse
import numpy as np
import random
import os
import cv2
import time
import struct
from os import listdir
from os.path import isfile, join

parser = argparse.ArgumentParser(description='dmp reader')
parser.add_argument('noisy', metavar='DIR',
                    help='path to dmps')
parser.add_argument('gt', metavar='DIR',
                    help='path to GT dmps')
# parser.add_argument("-f", '--flagMode',
#                     help="The flag that select the runing mode, such as train, eval",
#                     default='te', type=str)


def _int64_feature(value):
    """Wrapper for inserting int64 features into Example proto."""
    if not isinstance(value, list):
        value = [value]
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def _bytes_feature(value):
    """Wrapper for inserting bytes features into Example proto."""
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def readDmp(file, depthShift, n_frame_max):
    # input:  [string] file name
    # output: list of {( [array of np.array(int)] 2D depth map , [array of np.array([int, int, int])] ) 2D color map}
    # n_frame_max: maximum n_frame
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

    if n_frame_max != -1:
        n_frame = n_frame_max

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


# write all example into one single tfrecords file
def write_tfRecord(
        header=None,
        header_gt=None,
        data=None,
        data_gt=None,
        items=None,
        flag='train',
        label=None,
        file_name='test_yee.tfrecord'):
    """
    data: your data list or np.ndarray
    label: label list
    file_name: the tfrecord file storage data and label
    """
    print('writing {} ...'.format(file_name))
    n_frame, width, height, max_dep = header
    n_frame_gt, _, _, _ = header_gt
    
    if n_frame_gt < n_frame:
        n_frame = n_frame_gt

    # if flag == 'train':
    #     frame_range = range(0, n_frame)
    # elif flag == 'eval':
    #     frame_range = range(n_frame-10, n_frame)
    # else:
    #     frame_range = range(n_frame)

    max_dep_np = np.zeros((1), dtype=np.float32)
    max_dep_np[0] = max_dep
    # Compress the frames using JPG and store in as a list of strings
    # in 'frames'
    # here suppose we have 10 data with same shape [50,100,3], but
    # label has different length, eg. OCR task.
    with tf.python_io.TFRecordWriter(file_name) as writer:
        for i in items:
            print('[{}][{}/{}] ...'.format(flag, i, n_frame))
            # prepare data and label
            # noisy_data = np.ones((height, width, 3), dtype=np.float32)  # np.ndarray
            noisy_array, rgb_array_3 = data[i]

            gt_array, _ = data_gt[i]
            # label = list(np.arange(i+1))  # list of int

            features = {}  # each example has these features
            # features['label'] = _int64_feature(label)
            # 'label' is a feature of tf.train. BytesList
            features['max_dep'] = _bytes_feature(max_dep_np.tostring())
            features['noisy'] = _bytes_feature(noisy_array.tostring())
            features['intensity'] = _bytes_feature(noisy_array.tostring())
            features['rgb'] = _bytes_feature(rgb_array_3.tostring())
            features['gt'] = _bytes_feature(gt_array.tostring())

            # write serialized example into .tfrecords
            tfrecord_example = tf.train.Example(
                features=tf.train.Features(feature=features))
            writer.write(tfrecord_example.SerializeToString())


if __name__ == "__main__":
    args = parser.parse_args()

    noisy_dir = args.noisy
    noisy_files = [os.path.join(noisy_dir, f) for f in os.listdir(noisy_dir) if os.path.isfile(os.path.join(noisy_dir, f))]

    gt_dir = args.gt
    gt_files = [os.path.join(gt_dir, f) for f in os.listdir(gt_dir) if os.path.isfile(os.path.join(gt_dir, f))]

    noisy_files.sort()
    gt_files.sort()
    paired_files = list(zip(noisy_files, gt_files))

    print(noisy_files)
    print(gt_files)
    print(paired_files)
    print('OK ?')
    input()

    header_noisy = (0, 0, 0)
    data_noisy = []
    header_gt = (0, 0, 0)
    data_gt = []
    max_dep_all = 0

    for (noisy_file, gt_file) in paired_files:
        # GT
        header, data = readDmp(gt_file, 1, -1)
        data_gt.extend(data)
        n_frame, width, height, max_dep = header
        
        if max_dep > max_dep_all:
            max_dep_all = max_dep
        
        header_gt = header_noisy = (header_noisy[0] + n_frame, width, height, max_dep_all)

        # NOISY
        header, data = readDmp(noisy_file, 1, n_frame)
        _, _, _, max_dep = header

        if max_dep > max_dep_all:
            max_dep_all = max_dep
        
        header_gt = header_noisy = (header_noisy[0], width, height, max_dep_all)

        data_noisy.extend(data)
        
        print(header_noisy)
        print(len(data_noisy))
        print(header_gt)
        print(len(data_gt))
        print('OK????')
        # input()

    n_frame, _, _, _ = header_gt

    all_items = list(range(n_frame))
    eval_items = random.sample(all_items, n_frame // 10)
    train_items = [x for x in all_items if x not in eval_items]

    write_tfRecord(
        header=header_noisy,
        header_gt=header_gt,
        data=data_noisy,
        data_gt=data_gt,
        items=train_items,
        flag='train',
        label=None,
        file_name='../datasets/tfrecords/yee/yee_train.tfrecords'
    )
    write_tfRecord(
        header=header_noisy,
        header_gt=header_gt,
        data=data_noisy,
        data_gt=data_gt,
        items=eval_items,
        flag='eval',
        label=None,
        file_name='../datasets/tfrecords/yee/yee_eval.tfrecords'
    )
    # write_tfRecord(
    #     header=header_noisy,
    #     header_gt=header_gt,
    #     data=data_noisy,
    #     data_gt=data_gt,
    #     flag='all',
    #     label=None,
    #     file_name='../datasets/tfrecords/yee/yee_all.tfrecords'
    # )

# read .dmp files and convert to multi-frame TFRecord
# with gound-truth obtained by BundleFusion .dmp files
# 2021.08.10
# GATHER ALL SELECTED DATA!!!!
from io import IncrementalNewlineDecoder
import tensorflow as tf
import argparse
import numpy as np
import os
import cv2
import time
import random
import struct
from os import listdir
from os.path import isfile, join

parser = argparse.ArgumentParser(description='dmp reader')
# parser.add_argument('d1', metavar='DIR',
#                     help='path to dmp')
# parser.add_argument('gt', metavar='DIR',
#                     help='path to GT dmp')
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


def readDmp(file, depthShift, needs):
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
    n_frame_final = n_frame
    for frame in range(n_frame):
        depthMap = struct.unpack('f'*mapLen, f.read(4*mapLen))
        colorMap = struct.unpack('B'*mapLen, f.read(mapLen))

        if frame not in needs:
            n_frame_final -= 1
            continue

        print('processing frame [{:03d}] ...'.format(frame), end="\r")

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

    header = (n_frame_final, width, height, max_dep)
    return header, data


# write all example into one single tfrecords file
def write_tfRecord(
        header=None,
        header_gt=None,
        data=None,
        data_gt=None,
        flag='train',
        items=None,
        label=None,
        file_name='test_yee.tfrecord'):
    """
    data: your data list or np.ndarray
    label: label list
    file_name: the tfrecord file storage data and label
    """
    print('writing {} ...'.format(file_name))
    n_frame, width, height, max_dep = header
    # n_frame_gt, _, _, _ = header_gt
    
    # if n_frame_gt < n_frame:
    #     n_frame = n_frame_gt

    # n_frame = 219

    max_dep_np = np.zeros((1), dtype=np.float32)
    max_dep_np[0] = max_dep
    
    # eps is 0.001 cm
    eps = 0.00001
    
    # Compress the frames using JPG and store in as a list of strings
    # in 'frames'
    # here suppose we have 10 data with same shape [50,100,3], but
    # label has different length, eg. OCR task.

    n_item = len(items)

    with tf.python_io.TFRecordWriter(file_name) as writer:
        for i in items:
            print('[{}][{}/{}] ...'.format(flag, i, n_frame), end='\r')
            noisy_array, rgb_array_3 = data[i]
            gt_array, _ = data_gt[i]

            ######################################################
            #     PIXEL IN GT SET TO 0 IF THAT IN INPUT IS 0     #
            ##################################################################
            outlier_count = 0
            threshold = 0.01
            threshold = 350*450*threshold
            error_filter = 0.50  # 50cm
            for ih in range(height):
                for iw in range(width):
                    dep = noisy_array[ih][iw]
                    dep_g = gt_array[ih][iw]

                    if outlier_count > threshold:
                        break
                    if dep > 4.0:
                        gt_array[ih][iw] = dep
                        outlier_count += 1
                    if dep_g < eps:
                        gt_array[ih][iw] = dep
                        # outlier_count += 1
                    # if dep < eps:
                    #     gt_array[ih][iw] = 0
                    # if dep >= eps:
                    #     # dep_g += 0.01
                    #     error = dep_g - dep
                    #     # error *= 2.0
                    #     # max error
                    #     if (error > error_filter):
                    #         gt_array[ih][iw] = dep + error_filter
                    #     if (error < -error_filter):
                    #         gt_array[ih][iw] = dep - error_filter
                    #     else:
                    #         gt_array[ih][iw] = dep + error
            if outlier_count > threshold:
                n_item -= 1
                print('\n------ DROP FRAME [{}] ...'.format(i))
                continue



            ##################################################################

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
    
    print('\n[n_item]: {}'.format(n_item))
    print('------------------------------------')


if __name__ == "__main__":
        
    data_in = []
    data_pg = []
    n_frame_total = 0
    max_dep_total = 0


    df = 'SensReader/RC00.dmp'
    gf = 'SensReader/RC00.ply.GTA.dmp'
    need_items = list(range(0, 5000))
    args = parser.parse_args()
    header, data = readDmp(df, 1, need_items)
    header_gt, data_gt = readDmp(gf, 1, need_items)
    n_frame, width, height, max_dep = header
    n_frame_gt, _, _, _ = header_gt

    data_in.extend(data[:n_frame_gt])
    data_pg.extend(data_gt[:n_frame_gt])
    n_frame_total += n_frame_gt
    if max_dep > max_dep_total:
        max_dep_total = max_dep

    print(df)
    print('[n_frame]: {}'.format(n_frame))
    print('[n_frame_gt]: {}'.format(n_frame_gt))
    print('[max_dep]: {}'.format(max_dep))
    print('[len(data_in)]: {}'.format(len(data_in)))
    # input()



    df = 'SensReader/E02TR.dmp'
    gf = 'SensReader/E02TR.ply.GTA.dmp'
    need_items = list(range(0, 5000))
    args = parser.parse_args()
    header, data = readDmp(df, 1, need_items)
    header_gt, data_gt = readDmp(gf, 1, need_items)
    n_frame, width, height, max_dep = header
    n_frame_gt, _, _, _ = header_gt
    
    data_in.extend(data[:n_frame_gt])
    data_pg.extend(data_gt[:n_frame_gt])
    n_frame_total += n_frame_gt
    if max_dep > max_dep_total:
        max_dep_total = max_dep

    print(df)
    print('[n_frame]: {}'.format(n_frame))
    print('[n_frame_gt]: {}'.format(n_frame_gt))
    print('[max_dep]: {}'.format(max_dep))
    print('[len(data_in)]: {}'.format(len(data_in)))
    # input()



    df = 'SensReader/E07TR.dmp'
    gf = 'SensReader/E07TR.ply.GTA.dmp'
    need_items = list(range(285, 350))
    args = parser.parse_args()
    header, data = readDmp(df, 1, need_items)
    header_gt, data_gt = readDmp(gf, 1, need_items)
    n_frame, width, height, max_dep = header
    n_frame_gt, _, _, _ = header_gt
    
    data_in.extend(data[:n_frame_gt])
    data_pg.extend(data_gt[:n_frame_gt])
    n_frame_total += n_frame_gt
    if max_dep > max_dep_total:
        max_dep_total = max_dep

    print(df)
    print('[n_frame]: {}'.format(n_frame))
    print('[n_frame_gt]: {}'.format(n_frame_gt))
    print('[max_dep]: {}'.format(max_dep))
    print('[len(data_in)]: {}'.format(len(data_in)))
    # input()




    df = 'SensReader/MP15.dmp'
    gf = 'SensReader/MP15.ply.GTA.dmp'
    need_items = list(range(250, 300))
    args = parser.parse_args()
    header, data = readDmp(df, 1, need_items)
    header_gt, data_gt = readDmp(gf, 1, need_items)
    n_frame, width, height, max_dep = header
    n_frame_gt, _, _, _ = header_gt
    
    data_in.extend(data[:n_frame_gt])
    data_pg.extend(data_gt[:n_frame_gt])
    n_frame_total += n_frame_gt
    if max_dep > max_dep_total:
        max_dep_total = max_dep

    print(df)
    print('[n_frame]: {}'.format(n_frame))
    print('[n_frame_gt]: {}'.format(n_frame_gt))
    print('[max_dep]: {}'.format(max_dep))
    print('[len(data_in)]: {}'.format(len(data_in)))
    # input()



    df = 'SensReader/E11TR.dmp'
    gf = 'SensReader/E11TR.ply.GTA.dmp'
    need_items = list(range(650, 665))
    args = parser.parse_args()
    header, data = readDmp(df, 1, need_items)
    header_gt, data_gt = readDmp(gf, 1, need_items)
    n_frame, width, height, max_dep = header
    n_frame_gt, _, _, _ = header_gt
    
    data_in.extend(data[:n_frame_gt])
    data_pg.extend(data_gt[:n_frame_gt])
    n_frame_total += n_frame_gt
    if max_dep > max_dep_total:
        max_dep_total = max_dep

    print(df)
    print('[n_frame]: {}'.format(n_frame))
    print('[n_frame_gt]: {}'.format(n_frame_gt))
    print('[max_dep]: {}'.format(max_dep))
    print('[len(data_in)]: {}'.format(len(data_in)))
    # input()

    if max_dep_total > 4.0:
        max_dep_total = 4.0

    print('[max_dep_total]: {}'.format(max_dep_total))

    header_gt = header = (n_frame_total, width, height, max_dep_total)

    all_items = list(range(n_frame_total))
    eval_items = random.sample(all_items, n_frame_total // 10)
    train_items = [x for x in all_items if x not in eval_items]
    


    
    write_tfRecord(
        header=header,
        header_gt=header_gt,
        data=data_in,
        data_gt=data_pg,
        items=train_items,
        flag='train',
        label=None,
        file_name='../datasets/tfrecords/yee/yee_train.tfrecords'
    )
    write_tfRecord(
        header=header,
        header_gt=header_gt,
        data=data_in,
        data_gt=data_pg,
        items=eval_items,
        flag='eval',
        label=None,
        file_name='../datasets/tfrecords/yee/yee_eval.tfrecords'
    )
    # write_tfRecord(
    #     header=header,
    #     header_gt=header_gt,
    #     data=data,
    #     data_gt=data_gt,
    #     items=all_items,
    #     flag='all',
    #     label=None,
    #     file_name='../datasets/tfrecords/yee/yee_all.tfrecords'
    # )

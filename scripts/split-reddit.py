#!/usr/bin/env python
import os, sys, csv
import logging, argparse
import hashlib
import multiprocessing as mp
import pandas as pd

logging.basicConfig(format='[%(asctime)s][%(levelname)s][%(funcName)s] - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

input_directory = ""
output_directory = ""
num_splits = 1024
target_directories = {}

def hash(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


def get_bucket(s):
    return hash(s) % num_splits


def split(on):
    logger.debug("Creating target directories...")
    create_target_directories()
    logger.debug("Target directories created.")

    data_sets = os.listdir(input_directory)
    for data_set in data_sets:
        data_set_dir = os.path.join(input_directory, data_set)
        if not os.path.isdir(data_set_dir): continue
        logger.info("Splitting data-set: %s" % data_set)
        split_data_set(on, data_set_dir, data_set)


def split_data_set(on, data_set_path, sub_dir_name):
    targets = {}
    for i in range(num_splits):
        targets[i] = os.path.join(target_directories[i], sub_dir_name)
        if not os.path.isdir(targets[i]):
            os.mkdir(targets[i])

    data_files = map(lambda f: os.path.join(data_set_path, f), os.listdir(data_set_path))

    procs = []
    for file in data_files:
        procs.append(mp.Process(target=split_file, args=[on, file, targets]))


def split_file(on, file_path, targets):
    file_name = os.path.split(file_path)[1]
    logger.debug("Reading: %s" % file_path)
    df = pd.read_csv(file_path)
    logger.debug("Splitting: %s" % file_path)
    df['bucket'] = df[on].apply(get_bucket)
    for i in range(num_splits):
        output_file = os.path.join(targets[i], file_name)
        df[df['bucket'] == i].to_csv(output_file)


def create_target_directories():
    global target_directories
    target_directories = {i: os.path.join(output_directory, "%05d" % i) for i in range(num_splits)}
    for i in target_directories:
        target_dir = target_directories[i]
        if os.path.isfile(target_dir):
            logger.error("File exists: %s" % target_dir)
            exit(1)
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)  # create it if it doesn't exist


def parse_args():
    parser = argparse.ArgumentParser(description="Split the Reddit data-set", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    io_options_group = parser.add_argument_group("I/O Options")
    io_options_group.add_argument('-i', "--input", help="Input directory")
    io_options_group.add_argument('-o', "--output", help="Output directory")

    options_group = parser.add_argument_group("Options")
    options_group.add_argument('-n', '--num-splits', type=int, default=1024, help="Number of ways to split dataset")
    options_group.add_argument('-on', '--on', type=str, default="user_id", help="Field to split on")
    options_group.add_argument('-p', '--pool-size', type=int, default=10, help="Thread pool size")

    console_options_group = parser.add_argument_group("Console Options")
    console_options_group.add_argument('-v', '--verbose', action='store_true', help='verbose output')
    console_options_group.add_argument('--debug', action='store_true', help='Debug Console')

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.basicConfig(format='[%(asctime)s][%(levelname)s][%(funcName)s] - %(message)s')
    elif args.verbose:
        logger.setLevel(logging.INFO)
        logging.basicConfig(format='[%(asctime)s][%(levelname)s][%(funcName)s] - %(message)s')
    else:
        logger.setLevel(logging.WARNING)
        logging.basicConfig(format='[log][%(levelname)s] - %(message)s')
    return args


def main():
    args = parse_args()

    logger.debug("Input directory: %s" % args.input)
    if not os.path.exists(args.input):
        logger.error("Input directory: %s not found." % args.input)
        raise Exception()

    if not os.path.exists(args.output):
        logger.debug("Output directory: %s did not exist. Creating it..." % args.output)
        os.makedirs(args.output)
    else:
        logger.debug("Output directory: %s" % args.output)

    input_directory = args.input
    output_directory = args.output
    num_splits = args.num_splits
    split(args.on)


if __name__ == "__main__":
    main()

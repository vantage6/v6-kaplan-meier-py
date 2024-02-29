#!/usr/bin/env python3
# Simple PoC script to add some noise to a column in a dataset
import os
import argparse
import pandas as pd
import numpy as np
from scipy.stats import ks_2samp

DEFAULT_MAX_CLIP_VALUE = 5
DEFAULT_SIGMA = 1


def parse_args():
    parser = argparse.ArgumentParser(description="Add noise to a dataset")
    parser.add_argument("-i", "--input", type=str, required=True, help="Input file")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output file")
    parser.add_argument("-s", "--sigma", type=float, default=DEFAULT_SIGMA, help="Sigma for norm dist")
    parser.add_argument("-m", "--max_clip_value", type=int, default=DEFAULT_MAX_CLIP_VALUE, help="Clip value")
    parser.add_argument("-c", "--column_name", type=str, default="", help="Column name to add noise to")
    parser.add_argument("-e", "--column_name_event", type=str, default="", help="Column name of event")
    return parser.parse_args()


def main():
    args = parse_args()

    df = pd.read_csv(args.input)

    # check column name exists
    if args.column_name not in df.columns:
        raise ValueError(f"Column name {args.column_name} does not exist in the input file")

    original_dist = df[[args.column_name, args.column_name_event]].values

    noise = np.random.normal(0, args.sigma, df.shape[0])
    noise = np.round(noise).astype(int)
    noise = np.clip(noise, -args.max_clip_value, args.max_clip_value)

    noised = df[args.column_name] + noise
    # we assume we can observe event at t=0
    noised = np.clip(noised, 1, None)
    # change column values with noised values
    df[args.column_name] = noised
    print(f'Noised {args.column_name}')
    print(f'Min noise {min(noised)}')
    print(f'Max noise {max(noised)}\n')

    # check that output file does not already exist
    # if os.path.exists(args.output):
    #     raise ValueError(f"Output file {args.output} already exists")

    # check whether distributions are the same
    noise_dist = df[[args.column_name, args.column_name_event]].values
    statistic, pvalue = ks_2samp(original_dist.flatten(), noise_dist.flatten())
    print(f'Maximum difference between the CDF of the two samples: {statistic}')
    print(f'P-value: {pvalue}\n')

    # save output
    df.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()

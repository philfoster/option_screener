#! /usr/bin/python3

import pandas as pd
import argparse
from screener_tools import read_json_file

DEFAULT_ANALYZER_CONFIG="./etc/analyzer.json"

COL_RANK="Score"
COL_ROO="ROO Annualized(%)"
COL_TOTAL_GAIN="Total Annualized(%)"
COL_BETA="Beta"
COL_DOWNSIDE="Downside Protection(%)"
COL_DELTA="Delta"

WEIGHT_RANK="score_weight"
WEIGHT_ROO="roo_weight"
WEIGHT_TOTAL_GAIN="total_gain_weight"
WEIGHT_BETA="beta_weight"
WEIGHT_DOWNSIDE="downside_weight"
WEIGHT_DELTA="delta_weight"

DEFAULT_WEIGHT_RANK=1.0
DEFAULT_WEIGHT_ROO=2.0
DEFAULT_WEIGHT_TOTAL_GAIN=2.0
DEFAULT_WEIGHT_BETA=25
DEFAULT_WEIGHT_DOWNSIDE=20.0
DEFAULT_WEIGHT_DELTA=100.0

COL_RANK_SCORE="Rank Score"
COL_RANK_ROO="ROO Score"
COL_RANK_TOTAL_GAIN="Total Gain Score"
COL_RANK_BETA="Beta Score"
COL_RANK_DOWNSIDE="Downside Score"
COL_RANK_DELTA="Delta Score"
COL_RANK_OPTION="Total Option Score"

global GLOBAL_VERBOSE
global GLOBAL_CONFIG

def main(results_csv,output_file):
    df = pd.read_csv(results_csv)

    df[COL_RANK_SCORE] = calculate_simple_score(df[COL_RANK],GLOBAL_CONFIG.get(WEIGHT_RANK,DEFAULT_WEIGHT_RANK))
    df[COL_RANK_ROO] = calculate_simple_score(df[COL_ROO],GLOBAL_CONFIG.get(WEIGHT_ROO,DEFAULT_WEIGHT_ROO))
    df[COL_RANK_TOTAL_GAIN] = calculate_simple_score(df[COL_TOTAL_GAIN],GLOBAL_CONFIG.get(WEIGHT_TOTAL_GAIN,DEFAULT_WEIGHT_TOTAL_GAIN))
    df[COL_RANK_BETA] = calculate_beta_score(df[COL_BETA],GLOBAL_CONFIG.get(WEIGHT_BETA,DEFAULT_WEIGHT_BETA))
    df[COL_RANK_DOWNSIDE] = calculate_simple_score(df[COL_DOWNSIDE],GLOBAL_CONFIG.get(WEIGHT_DOWNSIDE,DEFAULT_WEIGHT_DOWNSIDE))
    df[COL_RANK_DELTA] = calculate_simple_score(df[COL_DELTA],GLOBAL_CONFIG.get(WEIGHT_DELTA,DEFAULT_WEIGHT_DELTA))

    df[COL_RANK_OPTION] = (df[COL_RANK_SCORE] + df[COL_RANK_ROO] + df[COL_RANK_TOTAL_GAIN] + df[COL_RANK_BETA] + df[COL_RANK_DOWNSIDE] + df[COL_RANK_DELTA] ) / 6

    print(df[COL_RANK_OPTION])

    df.to_csv(output_file)

def calculate_simple_score(series,weight):
    return series * weight

def calculate_beta_score(series,weight):
    return (3 - series) * weight

def debug(msg):
    if GLOBAL_DEBUG:
        print(msg)

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="analyzer configuration file", default=DEFAULT_ANALYZER_CONFIG)
    parser.add_argument('-r','--results', dest='results', required=True, help="CSV file with covered calls")
    parser.add_argument('-v','--verbose', dest='verbose', required=False,default=False,action='store_true',help="Increase verbosity")
    parser.add_argument('-d','--debug', dest='debug', required=False,default=False,action='store_true',help="Enable debugging")
    parser.add_argument('-o','--output-csv', dest='output', required=True, help="CSV file to write the output to")
    args = parser.parse_args()

    GLOBAL_VERBOSE = args.verbose
    GLOBAL_DEBUG = args.debug

    GLOBAL_CONFIG = read_json_file(args.config_file)

    main(args.results,args.output)


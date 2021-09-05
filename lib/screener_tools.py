import glob
import json
import os
from os.path import expanduser
from etrade_tools import *

# Screener config items
CACHE_DIR="cache_dir"
ETRADE_CONFIG="etrade_config"
QUESTIONS_DIR="questions_directory"
SYMBOLS_DIR="symbols_directory"
SECTOR_QUESTION_ID="sector_question_id"

# Defaults
DEFAULT_CACHE_DIR=".answers"
DEFAULT_PRICE_MIN=15.0
DEFAULT_PRICE_MAX=375.0
DEFAULT_VOLUME_MIN=400000
DEFAULT_OPEN_INTEREST_MIN=50
DEFAULT_SECTOR_FILE="~/.stock_sectors.json"

# Question configuration
QUESTION_NAME="name"
QUESTION_LIST="questions"
QUESTION_TEXT="question"
QUESTION_TYPE="type"
QUESTION_ID="uuid"
QUESTION_BLOCKER="blocker"
QUESTION_EXPIRATION_DAYS="expiration_days"
PRICE_MIN="price_min"
PRICE_MAX="price_max"
VOLUME_MIN="volume_min"
SECTOR_FILE="sector_file"
OPEN_INTEREST_MIN="open_interest_min"

# Cache constants
CACHE_SYMBOL="symbol"
CACHE_VALUE="value"
CACHE_EXPIRATION_TIMESTAMP="expiration_timestamp"
CACHE_QUESTION="question"

# Quetion types
TYPE_BOOLEAN="boolean"
TYPE_EARNINGS="earnings_date"
TYPE_SECTOR="sector_selection"
TYPE_PRICE="price_filter"
TYPE_VOLUME="volume_filter"
TYPE_OPEN_INTEREST="open_interest_filter"

def get_sector_from_cache(screener_config,symbol):
    answer_file = get_answer_file(screener_config.get(CACHE_DIR),symbol)
    if not os.path.exists(expanduser(answer_file)):
        return None

    sector_question_id = screener_config.get(SECTOR_QUESTION_ID,None)
    if sector_question_id is None:
        return None

    answers = get_all_answers_from_cache(answer_file)
    answer = answers.get(sector_question_id,None)
    if answer:
        return answer.get(CACHE_VALUE,None)
    return None

def cache_answers(answer_file,answers):
    write_json_file(answer_file,answers)

def get_answer_file(cache_dir,symbol):
    return f"{cache_dir}/{symbol.upper()}.json"

def get_all_answers_from_cache(cache_file):
    answers = dict()
    try:
        answers = read_json_file(cache_file)
    except Exception as e:
        pass
    return answers

def get_answer_from_cache(answer_file,symbol,question):
    question_id = question.get(QUESTION_ID)
    text = question.get(QUESTION_TEXT)

    answers = get_all_answers_from_cache(answer_file)

    # Create the question if needed
    if question_id in answers.keys():
        value = answers[question_id].get(CACHE_VALUE,None)
        expiration_timestamp = answers[question_id].get(CACHE_EXPIRATION_TIMESTAMP,None)

        if get_current_timestamp() < answers[question_id].get(CACHE_EXPIRATION_TIMESTAMP,0):
            return (value,expiration_timestamp)

    # Didn't find a fresh answer
    return (None,0)

def read_json_file(json_file):
    """ Read in a json file and return a json data structure """
    json_data = None
    with open(expanduser(json_file), "r") as cf:
        json_data = json.loads("".join(cf.readlines()))
    return json_data

def write_json_file(filename,data):
    with open(expanduser(filename), "w") as f:
        f.write(json.dumps(data,indent=2))

def get_questions(questions_dir):
    questions = dict()
    for file in glob.glob(f"{questions_dir}/*.json"):
        try:
            question_data = read_json_file(file)
            qname = question_data.get(QUESTION_NAME)
            questions[qname] = question_data
        except Exception as e:
            print(f"Could not read {file}: {e}")
    return questions

def get_symbols(symbols_dir):
    symbols = set()
    for file in glob.glob(f"{symbols_dir}/*"):
        with open(file,"r") as f:
            for line in f.readlines():
                for token in line.rstrip().split():
                    symbols.add(token)
    return symbols

def get_current_timestamp():
    return int(datetime.datetime.now().timestamp())


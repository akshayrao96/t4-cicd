# For code walk on 15th Oct only, delete/modify after
import os
import pprint
import json
from collections import OrderedDict
import ruamel.yaml
from util.yaml_parser import YamlParser
from util.config_tools import ConfigChecker
from util.common_utils import get_logger
logger = get_logger("tests.test_util.test_yaml_parser")

parser = YamlParser()
ans_json_path = os.path.join(os.path.dirname(__file__), 'test_data/expected/test_yaml_parser.json')
with open(ans_json_path, 'r') as openfile:
    # Reading from json file
    expected_ans_json = json.load(openfile)
    
# with open(ans_json_path, 'r') as openfile:
#     # Ordered dict variation
#     expected_ans_json_od = json.load(openfile, object_pairs_hook=OrderedDict)

def test_duplicate_pipeline_name():
    duplicate_name_path = os.path.join(os.path.dirname(__file__), 'test_data/duplicate_pipeline_name')
    print(duplicate_name_path)
    try:
        parser.parse_yaml_directory(duplicate_name_path)
        assert False
    except ValueError:
        assert True

def test_parse_yaml_file_not_found():
    not_found_path = os.path.join(os.path.dirname(__file__), 'test_data/duplicate_pipeline_name/not_found.yml')
    try:
        parser.parse_yaml_file(not_found_path)
        assert False
    except FileNotFoundError:
        assert True

def test_parse_yaml_file_invalid_dir():
    not_found_dir = os.path.join(os.path.dirname(__file__), 'test_data/not_found_dir')
    try:
        parser.parse_yaml_directory(not_found_dir)
        assert False
    except FileNotFoundError:
        assert True
        
def test_parse_yaml_file_duplicate_keys():
    not_found_path = os.path.join(os.path.dirname(__file__), 'test_data/valid_directory/duplicate_keys.yml')
    try:
        parser.parse_yaml_file(not_found_path)
        assert False
    except ruamel.yaml.YAMLError:
        assert True
        
def test_parse_yaml_file_valid():
    valid_file_path = os.path.join(os.path.dirname(__file__), 'test_data/valid_directory/valid_config.yml')
    extracted = parser.parse_yaml_file(valid_file_path)
    expected = expected_ans_json['test_parse_yaml_file_valid']
    # pprint.pprint(expected)
    assert extracted == expected
    
    checker = ConfigChecker()
    result_dict = checker.validate_config("valid_pipeline", extracted)
    expected_dict = expected_ans_json['test_validate_config_valid']
    # Required to ensure ordereddict are the same....
    expected_dict['pipeline_config']['stages'] = OrderedDict(expected_dict['pipeline_config']['stages'])
    logger.debug(result_dict)
    logger.debug(expected_dict)
    assert result_dict == expected_dict 
    
    valid_file_path = os.path.join(os.path.dirname(__file__), 'test_data/valid_directory/pipelines.yml')
    extracted = parser.parse_yaml_file(valid_file_path)
    # expected = expected_ans_json['test_parse_yaml_file_valid']
    result_dict = checker.validate_config("valid_pipeline_default", extracted, "pipelines.yml", error_lc=True)
    expected_dict = expected_ans_json['test_validate_config_valid_default']
    # Required to ensure ordereddict are the same....
    expected_dict['pipeline_config']['stages'] = OrderedDict(expected_dict['pipeline_config']['stages'])
    logger.debug(result_dict)
    logger.debug(expected_dict)
    assert result_dict == expected_dict 

    
def test_parse_yaml_file_cycle_detection():
    valid_file_path = os.path.join(os.path.dirname(__file__), 'test_data/valid_directory/cycle_config.yml')
    extracted = parser.parse_yaml_file(valid_file_path)
    
    checker = ConfigChecker()
    result_dict = checker.validate_config("cycle_pipeline", extracted)
    expected_dict = expected_ans_json['test_parse_yaml_file_cycle_detection_1']
    #pprint.pprint(result_dict)
    #pprint.pprint(expected_dict)
    assert result_dict == expected_dict
    
    # second check
    valid_file_path = os.path.join(os.path.dirname(__file__), 'test_data/valid_directory/cycle_config_2.yml')
    extracted = parser.parse_yaml_file(valid_file_path)
    expected_dict = expected_ans_json['test_parse_yaml_file_cycle_detection_2']
    result_dict = checker.validate_config("cycle_pipeline", extracted, 'cycle_config_2.yml',error_lc=True)
    assert result_dict == expected_dict

def test_parse_yaml_file_invalid_config():
    valid_file_path = os.path.join(os.path.dirname(__file__), 'test_data/valid_directory/invalid_config.yml')
    extracted = parser.parse_yaml_file(valid_file_path)
    checker = ConfigChecker()
    result_dict = checker.validate_config("invalid_pipeline", extracted, 'invalid_config.yml',error_lc=True)
    expected_dict = expected_ans_json['test_validate_config_invalid']
    assert result_dict == expected_dict
#     pprint.pprint(result_dict)
#     with open('test_ans.json', 'w', encoding='utf-8') as f:
#         json.dump(result_dict, f, ensure_ascii=False, indent=4)
    
# test_parse_yaml_file_invalid_config()

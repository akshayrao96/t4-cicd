import os
import json
import unittest
from collections import OrderedDict
import ruamel.yaml
import util.constant as c
from util.yaml_parser import YamlParser
from util.config_tools import ConfigChecker
from util.common_utils import get_logger
logger = get_logger("tests.test_util.test_yaml_parser")

class TestYamlParser(unittest.TestCase):
    """ Test the YamlParser

    Args:
        unittest (TestCase): base class
    """
    def setUp(self):
        """ Initial Set up
        """
        self.parser = YamlParser()
        ans_json_path = os.path.join(os.path.dirname(__file__),
                                     'test_data/expected/test_yaml_parser.json')
        with open(ans_json_path, 'r') as openfile:
            # Reading from json file
            self.expected_ans_json = json.load(openfile)
        self.checker = ConfigChecker()

    def test_duplicate_pipeline_name(self):
        """ Assert ValueError thrown for directory with duplicate pipeline names
        """
        duplicate_name_path = os.path.join(os.path.dirname(__file__),
                                           'test_data/duplicate_pipeline_name')
        try:
            self.parser.parse_yaml_directory(duplicate_name_path)
            assert False
        except ValueError:
            assert True

    def test_parse_yaml_file_not_found(self):
        """ Assert FileNotFoundError thrown for file not exist
        """
        not_found_path = os.path.join(os.path.dirname(__file__),
                                      'test_data/duplicate_pipeline_name/not_found.yml')
        try:
            self.parser.parse_yaml_file(not_found_path)
            assert False
        except FileNotFoundError:
            assert True

    def test_parse_yaml_file_invalid_dir(self):
        """ Assert FileNotFoundError thrown for directory not exist
        """
        not_found_dir = os.path.join(os.path.dirname(__file__), 'test_data/not_found_dir')
        try:
            self.parser.parse_yaml_directory(not_found_dir)
            assert False
        except FileNotFoundError:
            assert True

    def test_parse_yaml_file_duplicate_keys(self):
        """ Assert YAMLError thrown with duplicate keys
        """
        not_found_path = os.path.join(os.path.dirname(__file__),
                                      'test_data/valid_directory/duplicate_keys.yml')
        try:
            self.parser.parse_yaml_file(not_found_path)
            assert False
        except ruamel.yaml.YAMLError:
            assert True

    def test_parse_yaml_file_valid(self):
        """ Test parse the valid config file """
        valid_file_path = os.path.join(os.path.dirname(__file__),
                                       'test_data/valid_directory/valid_config.yml')
        extracted = self.parser.parse_yaml_file(valid_file_path)
        expected = self.expected_ans_json['test_parse_yaml_file_valid']
        assert extracted == expected

        # Integration Test with ConfigChecker
        result = self.checker.validate_config("valid_pipeline", extracted)
        result_dict = result.model_dump(by_alias=True)
        expected_dict = self.expected_ans_json['test_validate_config_valid']
        # Required to ensure ordereddict are the same....
        expected_dict[c.FIELD_PIPELINE_CONFIG][c.KEY_STAGES] = OrderedDict(expected_dict[c.FIELD_PIPELINE_CONFIG][c.KEY_STAGES])
        assert result_dict == expected_dict

        # Integration Test with ConfigChecker using another file
        valid_file_path = os.path.join(os.path.dirname(__file__),
                                       'test_data/valid_directory/pipelines.yml')
        extracted = self.parser.parse_yaml_file(valid_file_path)
        result = self.checker.validate_config("valid_pipeline_default",
                                              extracted, "pipelines.yml", error_lc=True)
        result_dict = result.model_dump(by_alias=True)
        expected_dict = self.expected_ans_json['test_validate_config_valid_default']
        # Required to ensure ordereddict are the same....
        expected_dict[c.FIELD_PIPELINE_CONFIG][c.KEY_STAGES] = OrderedDict(expected_dict[c.FIELD_PIPELINE_CONFIG][c.KEY_STAGES])
        assert result_dict == expected_dict 

    def test_parse_yaml_by_pipeline_name(self):
        """ Test the method parse_yaml_by_pipeline_name 
        """
        valid_dir = os.path.join(os.path.dirname(__file__), 'test_data/valid_directory/')
        extracted = self.parser.parse_yaml_by_pipeline_name("valid_pipeline", valid_dir)
        expected = self.expected_ans_json['test_parse_yaml_file_valid']
        assert extracted.pipeline_config == expected
        assert extracted.pipeline_file_name == "valid_config.yml"

    def test_parse_yaml_by_pipeline_name_fail(self):
        """ Test the method parse_yaml_by_pipeline_name with no pipeline_name exits
        """
        valid_dir = os.path.join(os.path.dirname(__file__), 'test_data/valid_directory/')
        try:
            # This pipeline name does not exist in the directory, should throw FileNotFoundError
            extracted = self.parser.parse_yaml_by_pipeline_name("not_found_pipeline", valid_dir)
            assert False
        except FileNotFoundError as fe:
            assert True

    def test_parse_yaml_file_cycle_detection(self):
        """ Test for cycle detection
        """
        cycle_file_path = os.path.join(os.path.dirname(__file__),
                                       'test_data/valid_directory/cycle_config.yml')
        extracted = self.parser.parse_yaml_file(cycle_file_path)

        # Integration Test with ConfigChecker
        result = self.checker.validate_config("cycle_pipeline", extracted)
        result_dict = result.model_dump(by_alias=True)
        expected_dict = self.expected_ans_json['test_parse_yaml_file_cycle_detection_1']
        assert result_dict == expected_dict

        # Integration Test with ConfigChecker, second cycle check
        cycle_file_path = os.path.join(os.path.dirname(__file__),
                                       'test_data/valid_directory/cycle_config_2.yml')
        extracted = self.parser.parse_yaml_file(cycle_file_path)
        expected_dict = self.expected_ans_json['test_parse_yaml_file_cycle_detection_2']
        result = self.checker.validate_config("cycle_pipeline", extracted,
                                              'cycle_config_2.yml',error_lc=True)
        result_dict = result.model_dump(by_alias=True)
        assert result_dict == expected_dict

    def test_parse_yaml_file_invalid_config(self):
        file_path = os.path.join(os.path.dirname(__file__),
                                 'test_data/valid_directory/invalid_config.yml')
        extracted = self.parser.parse_yaml_file(file_path)

        # Integration Test with ConfigChecker, test for invalid config
        result = self.checker.validate_config("invalid_pipeline", extracted,
                                              'invalid_config.yml',error_lc=True)
        result_dict = result.model_dump(by_alias=True)
        expected_dict = self.expected_ans_json['test_validate_config_invalid']
        assert result_dict == expected_dict

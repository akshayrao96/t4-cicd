""" This module provide all class and methods necessary to parse the yaml file(s) 
from a given filepath or directory. It will retain the lines and columns information 
down to last key level for further processing and usage downstream
"""
from typing import Text
import os
import ruamel.yaml
import util.constant as c
from util.common_utils import get_logger
from util.model import (RawPipelineInfo)

logger = get_logger(logger_name='util.yaml_parser')
# pylint: disable=logging-fstring-interpolation
class Str(ruamel.yaml.scalarstring.ScalarString):
    """ Subclass the parent class add the __slots__ property

    Args:
        ruamel (ruamel.yaml.scalarstring.ScalarString): parent class

    Returns:
        Str: an object of this class
    """
    __slots__ = ['lc']

    style = ""

    def __new__(cls, value):
        return ruamel.yaml.scalarstring.ScalarString.__new__(cls, value)


class MyPreservedScalarString(ruamel.yaml.scalarstring.PreservedScalarString):
    """Subclass the parent class add the __slots__ property

    Args:
        ruamel (ruamel.yaml.scalarstring.PreservedScalarString): parent class
    """
    __slots__ = ['lc']


class MyDoubleQuotedScalarString(ruamel.yaml.scalarstring.DoubleQuotedScalarString):
    """Subclass the parent class add the __slots__ property

    Args:
        ruamel (ruamel.yaml.scalarstring.DoubleQuotedScalarString): parent class
    """
    __slots__ = ['lc']


class MySingleQuotedScalarString(ruamel.yaml.scalarstring.SingleQuotedScalarString):
    """Subclass the parent class add the __slots__ property

    Args:
        ruamel (ruamel.yaml.scalarstring.SingleQuotedScalarString): parent class
    """
    __slots__ = ['lc']


class MyConstructor(ruamel.yaml.constructor.RoundTripConstructor):
    """ Subclass the parent class to override the method

    Args:
        ruamel (ruamel.yaml.constructor.RoundTripConstructor): parent class
    """
    def construct_scalar(self, node):
        """ Override the construct_scalar method

        Args:
            node (ruamel.yaml.nodes.ScalarNode): single dictionary cell

        Raises:
            ruamel.yaml.constructor.ConstructorError: _description_

        Returns:
            ruamel.yaml.nodes.ScalarNode: dictionary cell with lc.line and lc.col info
        """
        # pylint: disable=attribute-defined-outside-init
        if not isinstance(node, ruamel.yaml.nodes.ScalarNode):
            raise ruamel.yaml.constructor.ConstructorError(
                None, None,
                f"expected a scalar node, but found {node.id}",
                node.start_mark)

        if node.style == '|' and isinstance(node.value, Text):
            ret_val = MyPreservedScalarString(node.value)
        elif bool(self._preserve_quotes) and isinstance(node.value, Text):
            if node.style == "'":
                ret_val = MySingleQuotedScalarString(node.value)
            elif node.style == '"':
                ret_val = MyDoubleQuotedScalarString(node.value)
            else:
                ret_val = Str(node.value)
        else:
            ret_val = Str(node.value)
        ret_val.lc = ruamel.yaml.comments.LineCol()
        ret_val.lc.line = node.start_mark.line
        ret_val.lc.col = node.start_mark.column
        return ret_val

class YamlParser:
    """ Basic YamlParser to extract content from the yaml files
    """

    def __init__(self):
        """ Initialize the yaml parser
        """
        self.yaml = ruamel.yaml.YAML(typ='rt')
        self.yaml.Constructor = MyConstructor
        self.yaml.preserve_quotes = True

    def _get_yaml_filepaths(self, directory:str) -> list[str]:
        """ Helper method to search for all the YAML files in the 
        given directory.

        Args:
            directory (str): directory to search for

        Raises:
            FileNotFoundError: if the directory does not exist

        Returns:
            list[str]: a list of the absolute paths of the YAML files.
        """
        if not os.path.isdir(directory):
            error_msg = f"Given directory:{directory} is not a valid directory"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        yaml_filepaths = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.yml', '.yaml')):
                    yaml_filepaths.append(os.path.join(root, file))
        return yaml_filepaths

    def parse_yaml_directory(self, directory:str) -> dict:
        """
        Parse all YAML files in the given directory. Check for duplicate 
        pipeline name
        
        Args:
            directory (str): directory to search for
        
        Raises:
            FileNotFoundError: if the directory does not exist
            ValueError: for duplicate pipeline_name
            
        Returns:
            dict: A nested dictionary with pipeline_name as main key, 
            and RawPipelineInfo object as value
        """
        yaml_files = self._get_yaml_filepaths(directory)
        yaml_dict = {}
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as file:
                    yaml_content = self.yaml.load(file)
                    # Extract the filename without extension or path
                    pipeline_file_name = os.path.basename(yaml_file)
                    pl_name = yaml_content[c.KEY_GLOBAL][c.KEY_PIPE_NAME]
                    if pl_name in yaml_dict:
                        err_msg = f"{pipeline_file_name}:{pl_name.lc.line}:{pl_name.lc.col} "
                        err_msg += f"Duplicate key error for pipeline_name:{pl_name}"
                        logger.error(err_msg)
                        raise ValueError(err_msg)
                    yaml_dict[pl_name] = RawPipelineInfo(pipeline_name=pl_name,
                                                      pipeline_file_name=pipeline_file_name,
                                                      pipeline_config=yaml_content)
            except (FileNotFoundError, ruamel.yaml.YAMLError, TypeError) as e:
                # We want to continue process rest of the file, so catch the error here.
                logger.warning("Failed to parse YAML file at %s. Error: %s", yaml_file, e)
            except KeyError as k:
                logger.warning(f"Failed to parse YAML file at {yaml_file}. No key found for {k}")
        logger.info("Successfully parsed YAML files: %s", list(yaml_dict.keys()))
        return yaml_dict

    def parse_yaml_file(self, file_path: str) -> dict:
        """ Parse a single YAML file and return the content as a dictionary.
        Ignore potential duplicate pipeline name with other file. 

        Args:
            file_path (str): the absolute path of the yaml file

        Raises:
            FileNotFoundError: if file_path not valid or unable to parse
            yaml.YAMLError: If the YAML file cannot be parsed.

        Returns:
            dict: the key-value pairs from the YAML file. 
            contain the lines and columns information of the key
        """
        if not os.path.isfile(file_path):
            error_msg = f"Given file_path:{file_path} is not a valid yaml file"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                logger.info("Parsing YAML file at %s", file_path)
                return self.yaml.load(file)
        except ruamel.yaml.YAMLError as e:
            logger.error("Failed to parse YAML file at %s. Error: %s", file_path, e)
            raise

    def parse_yaml_by_pipeline_name(self, pipeline_name:str, directory:str) -> RawPipelineInfo:
        """ Parse a single YAML file from a given directory with the pipeline_name
        as specified. Check for duplicate pipeline name

        Args:
            pipeline_name (str): target pipeline_name to parse
            directory (str): directory to search for

        Raises:
            FileNotFoundError: if the pipeline name dont exist
            ValueError: for duplicate pipeline_name
            
        Returns:
            PipelineInfo: the Pydantic model contains key-value pairs of pipeline 
            information
        """
        all_yaml_dict = self.parse_yaml_directory(directory)
        if pipeline_name not in all_yaml_dict:
            err_msg = f"Target pipeline {pipeline_name} do not exist "
            err_msg += f"in given directory {directory}"
            raise FileNotFoundError(err_msg)
        return all_yaml_dict[pipeline_name]

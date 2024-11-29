""" All testing method for config tool
"""
from collections import OrderedDict
import unittest
import util.config_tools as config
import util.constant as c
from util.common_utils import get_logger

logger = get_logger("tests.test_util.test_config_tools")

class TestConfigChecker(unittest.TestCase):
    """ Test the ConfigChecker class """
    def setUp(self):
        self.checker = config.ConfigChecker()
        self.expected_dict = {
            c.KEY_GLOBAL: {
                c.KEY_PIPE_NAME: 'test_pipeline',
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_REG: c.DEFAULT_DOCKER_REGISTRY,
                    c.KEY_DOCKER_IMG:'ubuntu:latest'
                },
                c.KEY_ARTIFACT_PATH: 'Github.com'
            }
        }
        self.expected_error_msg = ""
        self.actual_dict = {}

    def test_check_global_section(self):
        """ test the _check_global_section() method
        """
        # Normal check
        input_dict = {
            c.KEY_GLOBAL: {
                c.KEY_PIPE_NAME: 'test_pipeline',
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_REG:c.DEFAULT_DOCKER_REGISTRY,
                    c.KEY_DOCKER_IMG:'ubuntu:latest'
                },
                c.KEY_ARTIFACT_PATH: 'Github.com'
            }
        }

        passed, error_msg = self.checker._check_global_section(
            pipeline_config=input_dict, processed_config=self.actual_dict)
        self.assertTrue(passed)
        self.assertEqual(error_msg, self.expected_error_msg)
        self.assertEqual(self.actual_dict, self.expected_dict)


    def test_check_global_section_missing_docker_reg(self):
        """ test the _check_global_section() for special case, no docker registry defined
        """
        # Normal check
        input_dict = {
            c.KEY_GLOBAL: {
                c.KEY_PIPE_NAME: 'test_pipeline',
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_IMG:'ubuntu:latest'
                },
                c.KEY_ARTIFACT_PATH: 'Github.com'
            }
        }
        passed, error_msg = self.checker._check_global_section(
            pipeline_config=input_dict, processed_config=self.actual_dict)
        self.assertTrue(passed)
        self.assertEqual(error_msg, self.expected_error_msg)
        self.assertEqual(self.actual_dict, self.expected_dict)

    def test_check_global_section_missing_pipeline_name(self):
        """ test the _check_global_section() for special case, no pipeline_name defined
        """
        input_dict = {
            c.KEY_GLOBAL: {
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_IMG:'ubuntu:latest'
                },
                c.KEY_ARTIFACT_PATH: 'Github.com'
            }
        }
        expected_dict = {
            c.KEY_GLOBAL: {
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_REG:c.DEFAULT_DOCKER_REGISTRY,
                    c.KEY_DOCKER_IMG:'ubuntu:latest'
                },
                c.KEY_ARTIFACT_PATH: 'Github.com'
            }
        }
        expected_error_msg = "Pipeline: from file:. Error in section:global key not found error for subkey:pipeline_name\n"
        actual_dict = {}
        passed, error_msg = self.checker._check_global_section(
            pipeline_config=input_dict, processed_config=actual_dict)
        assert not passed
        assert error_msg == expected_error_msg
        assert actual_dict == expected_dict


def test_check_stages_section():
    """ test the _check_stages_section() for only the fill in default
    """
    checker = config.ConfigChecker()

    # Normal check
    input_dict = {
        c.KEY_JOBS:{
            'compile':{
                c.JOB_SUBKEY_STAGE:'build'
            },
            'pytest':{
                c.JOB_SUBKEY_STAGE:'test',
                c.JOB_SUBKEY_NEEDS:['pylint']
            },
            'pylint':{
                c.JOB_SUBKEY_STAGE:'test',
            },
            'pydoc':{
                c.JOB_SUBKEY_STAGE:'doc'
            },
            'pydeploy':{
                c.JOB_SUBKEY_STAGE:'deploy'
            }
        }
    }
    expected_dict = {
        c.KEY_STAGES:OrderedDict({
                # Note since Python 3.7,
                # dict is ordered which guarantee the insertion order
                'build':{
                    c.KEY_JOB_GRAPH:{'compile':[]},
                    c.KEY_JOB_ORDER:[['compile']]
                }, 
                'test':{
                    c.KEY_JOB_GRAPH:{
                        'pylint':['pytest'],
                        'pytest':[]
                    },
                    c.KEY_JOB_ORDER:[['pylint', 'pytest']]
                },
                'doc':{
                    c.KEY_JOB_GRAPH:{'pydoc':[]},
                    c.KEY_JOB_ORDER:[['pydoc']]
                },
                'deploy':{
                    c.KEY_JOB_GRAPH:{'pydeploy':[]},
                    c.KEY_JOB_ORDER:[['pydeploy']]
                },
        })
    }
    expected_error_msg = ""
    actual_dict = {}
    passed, error_msg = checker._check_stages_section(
        pipeline_config=input_dict, processed_config=actual_dict
    )
    assert passed
    assert error_msg == expected_error_msg
    assert actual_dict == expected_dict

def test_check_stages_jobs_relationship():
    """ test the _check_stages_jobs_relationship() for normal success
    """
    checker = config.ConfigChecker()
    stage_list = ['build', 'test']
    jobs_dict = {
        'compile':{
            c.JOB_SUBKEY_STAGE:'build'
        },
        'pytest':{
            c.JOB_SUBKEY_STAGE:'test'
        },
        'pylint':{
            c.JOB_SUBKEY_STAGE:'test'
        },
    }
    expected_stages = OrderedDict(
        {'build':{'compile'},
        'test': {'pytest', 'pylint'}}
    )
    expected_error_msg = ""
    passed, error_msg, actual_stages = checker._check_stages_jobs_relationship(stage_list, jobs_dict)
    assert passed
    assert error_msg == expected_error_msg
    assert actual_stages == expected_stages

def test_check_stages_jobs_relationship_fails():
    """ test the _check_stages_jobs_relationship() for fail cases
    """
    checker = config.ConfigChecker()
    stage_list = ['build', 'test']
    # No stage key defined
    jobs_dict = {
        'compile':{
        },
        'pytest':{
            c.JOB_SUBKEY_STAGE:'test'
        },
        'pylint':{
            c.JOB_SUBKEY_STAGE:'test'
        },
    }
    expected_stages = OrderedDict()
    expected_error_msg = "Error in section:jobs job:compile No stage key defined\n"
    expected_error_msg += "Error in section:stages stage:build No job defined for this stage\n"
    passed, error_msg, actual_stages = checker._check_stages_jobs_relationship(stage_list, jobs_dict)
    assert not passed
    assert error_msg == expected_error_msg
    assert actual_stages == expected_stages
    # Job defined unknown stage
    jobs_dict = {
        'compile':{
            c.JOB_SUBKEY_STAGE:'build'
        },
        'pytest':{
            c.JOB_SUBKEY_STAGE:'testing'
        },
        'pylint':{
            c.JOB_SUBKEY_STAGE:'test'
        },
    }
    expected_stages = OrderedDict()
    expected_error_msg = "Error in section:jobs job:pytest stage value testing defined does not exist in stages list\n"
    passed, error_msg, actual_stages = checker._check_stages_jobs_relationship(stage_list, jobs_dict)
    assert not passed
    assert error_msg == expected_error_msg
    assert actual_stages == expected_stages

def test_check_jobs_dependencies():
    """ Test the _check_jobs_dependencies() method for individual stages 
    """
    checker = config.ConfigChecker()
    stage_name = 'test'
    job_list = ['compile', 'pytest']
    jobs_dict = {
        'compile':{
            c.JOB_SUBKEY_STAGE:'build',
        },

        'pylint':{
            c.JOB_SUBKEY_STAGE:'test'
        },
        'pytest':{
            c.JOB_SUBKEY_STAGE:'test',
            c.JOB_SUBKEY_NEEDS:['compile']
        },
    }
    expected_error_msg = ""
    expected_result_dict = {
        c.KEY_JOB_GRAPH:{
            'compile':['pytest'],
            'pytest':[]
        },
        c.KEY_JOB_ORDER:[[
            'compile', 'pytest'
        ]]
    }
    passed, actual_error_msg, actual_result = checker._check_jobs_dependencies(stage_name,
                                                                               job_list, jobs_dict)
    assert passed
    assert actual_error_msg == expected_error_msg
    assert actual_result == expected_result_dict

def test_topo_sort():
    """ test the topo_sort() function 
    """
    checker = config.ConfigChecker()
    stage_name = 'test'
    adjacency_list = {
        'job1':[],
        # job2 is required by job1
        'job2':['job1']
    }
    expected_order = [['job2', 'job1']]
    expected_error_msg = ""
    passed, actual_error_msg, actual_order = checker._group_n_sort(stage_name, adjacency_list)
    assert passed
    assert actual_error_msg == expected_error_msg
    assert actual_order == expected_order

def test_check_jobs_section():
    """ test the check_jobs_section function 
    """
    checker = config.ConfigChecker()

    # Normal check
    input_dict = {
        c.KEY_GLOBAL: {
                c.KEY_PIPE_NAME: 'test_pipeline',
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_REG:c.DEFAULT_DOCKER_REGISTRY,
                    c.KEY_DOCKER_IMG:'ubuntu:latest'
                },
                c.KEY_ARTIFACT_PATH: 'Github.com'
        },
        c.KEY_JOBS: {
            # First job with every things defined
            'compile':{
                c.JOB_SUBKEY_STAGE: 'build',
                c.JOB_SUBKEY_ALLOW: True,
                c.JOB_SUBKEY_NEEDS:['checkout'],
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_REG:"ghcr.io",
                    c.KEY_DOCKER_IMG:"ubuntu:22.04",
                },
                c.KEY_ARTIFACT_PATH: 'Github.com/cicd',
                c.JOB_SUBKEY_ARTIFACT:{
                    c.ARTIFACT_SUBKEY_ONSUCCESS: False,
                    c.ARTIFACT_SUBKEY_PATH: ['build/lib', 'build/doc'],
                },
                c.JOB_SUBKEY_SCRIPTS: ['poetry install']
            },
            # Second job with minimal required defined
            'checkout':{
                c.JOB_SUBKEY_STAGE: 'build',
                c.JOB_SUBKEY_SCRIPTS: ['git clone']
            }
        }
    }
    expected_dict = {
        c.KEY_GLOBAL: {
                c.KEY_PIPE_NAME: 'test_pipeline',
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_REG:c.DEFAULT_DOCKER_REGISTRY,
                    c.KEY_DOCKER_IMG:'ubuntu:latest'
                },
                c.KEY_ARTIFACT_PATH: 'Github.com'
        },
        c.KEY_JOBS: {
            # First job with every things defined
            'compile':{
                c.JOB_SUBKEY_STAGE: 'build',
                c.JOB_SUBKEY_ALLOW: True,
                c.JOB_SUBKEY_NEEDS:['checkout'],
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_REG:"ghcr.io",
                    c.KEY_DOCKER_IMG:"ubuntu:22.04",
                },
                c.KEY_ARTIFACT_PATH: 'Github.com/cicd',
                c.JOB_SUBKEY_ARTIFACT:{
                    c.ARTIFACT_SUBKEY_ONSUCCESS: False,
                    c.ARTIFACT_SUBKEY_PATH: ['build/lib', 'build/doc'],
                },
                c.JOB_SUBKEY_SCRIPTS: ['poetry install']
            },
            # Second job with minimal required defined
            'checkout':{
                c.JOB_SUBKEY_STAGE: 'build',
                c.JOB_SUBKEY_ALLOW: c.DEFAULT_FLAG_JOB_ALLOW_FAIL,
                c.JOB_SUBKEY_NEEDS: c.DEFAULT_LIST,
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_REG:c.DEFAULT_DOCKER_REGISTRY,
                    c.KEY_DOCKER_IMG:'ubuntu:latest'
                },
                c.KEY_ARTIFACT_PATH: 'Github.com',
                c.JOB_SUBKEY_SCRIPTS: ['git clone']
            }
        }
    }
    expected_error_msg = ""
    actual_dict = {
        c.KEY_GLOBAL: {
                c.KEY_PIPE_NAME: 'test_pipeline',
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_REG:c.DEFAULT_DOCKER_REGISTRY,
                    c.KEY_DOCKER_IMG:'ubuntu:latest'
                },
                c.KEY_ARTIFACT_PATH: 'Github.com'
        },
    }
    passed, error_msg = checker._check_jobs_section(input_dict, actual_dict)
    assert passed
    assert error_msg == expected_error_msg
    assert actual_dict == expected_dict

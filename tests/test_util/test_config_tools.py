""" All testing method for config tool
"""
from collections import OrderedDict
import util.config_tools as config
# from util.config_tools import (ConfigChecker)
from util.common_utils import get_logger


def test_check_global_section():
    """ test the _check_global_section() method
    """
    checker = config.ConfigChecker()

    # Normal check
    input_dict = {
        "global": {
            'pipeline_name': 'test_pipeline',
            'docker_registry': 'docker',
            'docker_image': 'ubuntu:latest',
            'artifact_upload_path': 'Github.com'
        }
    }
    expected_dict = {
        "global": {
            'pipeline_name': 'test_pipeline',
            'docker_registry': 'docker',
            'docker_image': 'ubuntu:latest',
            'artifact_upload_path': 'Github.com'
        }
    }
    expected_error_msg = ""
    actual_dict = {}
    passed, error_msg = checker._check_global_section(
        pipeline_config=input_dict, processed_config=actual_dict)
    assert passed
    assert error_msg == expected_error_msg
    assert actual_dict == expected_dict


def test_check_global_section_missing_docker_reg():
    """ test the _check_global_section() for special case, no docker registry defined
    """
    checker = config.ConfigChecker()

    # Normal check
    input_dict = {
        "global": {
            'pipeline_name': 'test_pipeline',
            'docker_image': 'ubuntu:latest',
            'artifact_upload_path': 'Github.com'
        }
    }
    expected_dict = {
        "global": {
            'pipeline_name': 'test_pipeline',
            'docker_registry': 'dockerhub',
            'docker_image': 'ubuntu:latest',
            'artifact_upload_path': 'Github.com'
        }
    }
    expected_error_msg = ""
    actual_dict = {}
    passed, error_msg = checker._check_global_section(
        pipeline_config=input_dict, processed_config=actual_dict)
    assert passed
    assert error_msg == expected_error_msg
    assert actual_dict == expected_dict


def test_check_global_section_missing_pipeline_name():
    """ test the _check_global_section() for special case, no pipeline_name defined
    """
    checker = config.ConfigChecker()

    # Normal check
    input_dict = {
        "global": {
            'docker_image': 'ubuntu:latest',
            'artifact_upload_path': 'Github.com'
        }
    }
    expected_dict = {
        "global": {
            'docker_registry': 'dockerhub',
            'docker_image': 'ubuntu:latest',
            'artifact_upload_path': 'Github.com'
        }
    }
    expected_error_msg = "Error in section:global key not found error for subkey:pipeline_name\n"
    actual_dict = {}
    passed, error_msg = checker._check_global_section(
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
        config.SECT_KEY_JOBS:{
            'compile':{
            config.JOB_SUBKEY_STAGE:'build'
            },
            'pytest':{
                config.JOB_SUBKEY_STAGE:'test',
                config.JOB_SUBKEY_NEEDS:['pylint']
            },
            'pylint':{
                config.JOB_SUBKEY_STAGE:'test',
                
            },
            'pydoc':{
                config.JOB_SUBKEY_STAGE:'doc'
            },
            'pydeploy':{
                config.JOB_SUBKEY_STAGE:'deploy'
            }
        }
    }
    expected_dict = {
        config.SECT_KEY_STAGES:OrderedDict({
                # Note since Python 3.7 , 
                # dict is ordered which guarantee the insertion order
                'build':{
                    config.STAGE_SUBKEY_JOB_GRAPH:{'compile':[]},
                    config.STAGE_SUBKEY_JOB_ORDER:[['compile']]
                }, 
                'test':{
                    config.STAGE_SUBKEY_JOB_GRAPH:{
                        'pylint':['pytest'],
                        'pytest':[]
                    },
                    config.STAGE_SUBKEY_JOB_ORDER:[['pylint', 'pytest']]
                },
                'doc':{
                    config.STAGE_SUBKEY_JOB_GRAPH:{'pydoc':[]},
                    config.STAGE_SUBKEY_JOB_ORDER:[['pydoc']]
                },
            
                'deploy':{
                    config.STAGE_SUBKEY_JOB_GRAPH:{'pydeploy':[]},
                    config.STAGE_SUBKEY_JOB_ORDER:[['pydeploy']]
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
            config.JOB_SUBKEY_STAGE:'build'
        },
        'pytest':{
            config.JOB_SUBKEY_STAGE:'test'
        },
        'pylint':{
            config.JOB_SUBKEY_STAGE:'test'
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
            config.JOB_SUBKEY_STAGE:'test'
        },
        'pylint':{
            config.JOB_SUBKEY_STAGE:'test'
        },
    }
    expected_stages = OrderedDict()
    expected_error_msg = f"No stage key defined for job compile\nNo job defined for stage build\n"
    passed, error_msg, actual_stages = checker._check_stages_jobs_relationship(stage_list, jobs_dict)
    assert not passed
    assert error_msg == expected_error_msg
    assert actual_stages == expected_stages
    
    # Job defined unknown stage
    jobs_dict = {
        'compile':{
            config.JOB_SUBKEY_STAGE:'build'
        },
        'pytest':{
            config.JOB_SUBKEY_STAGE:'testing'
        },
        'pylint':{
            config.JOB_SUBKEY_STAGE:'test'
        },
    }
    expected_stages = OrderedDict()
    expected_error_msg = f"stage value testing defined for job pytest does not exist in stages list\n"
    passed, error_msg, actual_stages = checker._check_stages_jobs_relationship(stage_list, jobs_dict)
    assert not passed
    assert error_msg == expected_error_msg
    assert actual_stages == expected_stages

def test_check_jobs_dependencies():
    """ Test the _check_jobs_dependencies() method for individual stages 
    """
    checker = config.ConfigChecker()
    job_list = ['compile', 'pytest']
    jobs_dict = {
        'compile':{
            config.JOB_SUBKEY_STAGE:'build',
            
        },

        'pylint':{
            config.JOB_SUBKEY_STAGE:'test'
        },
        
        'pytest':{
            config.JOB_SUBKEY_STAGE:'test',
            config.JOB_SUBKEY_NEEDS:['compile']
        },
    }
    expected_error_msg = ""
    expected_result_dict = {
        config.STAGE_SUBKEY_JOB_GRAPH:{
            'compile':['pytest'],
            'pytest':[]
        },
        config.STAGE_SUBKEY_JOB_ORDER:[[
            'compile', 'pytest'
        ]]
    }
    passed, actual_error_msg, actual_result = checker._check_jobs_dependencies(job_list, jobs_dict)
    assert passed
    assert actual_error_msg == expected_error_msg
    assert actual_result == expected_result_dict

def test_topo_sort():
    """ test the topo_sort() function 
    """
    checker = config.ConfigChecker()
    adjacency_list = {
        'job1':[],
        # job2 is required by job1
        'job2':['job1']
    }
    expected_order = ['job2', 'job1']
    expected_error_msg = ""
    passed, actual_error_msg, actual_order = checker._topo_sort(adjacency_list)
    assert passed
    assert actual_error_msg == expected_error_msg
    assert actual_order == expected_order

def test_check_jobs_section():
    """ test the check_jobs_section function 
    """
    checker = config.ConfigChecker()
    
    # Normal check
    input_dict = {
        config.SECT_KEY_GLOBAL: {
            config.SUBSECT_KEY_PIPE_NAME: 'test_pipeline',
            config.SUBSECT_KEY_DOCKER_REG: 'docker',
            config.SUBSECT_KEY_DOCKER_IMG: 'ubuntu:latest',
            config.SUBSECT_KEY_ARTIFACT_PATH: 'Github.com'
        }, 
        config.SECT_KEY_JOBS: {
            # First job with every things defined
            'compile':{
                config.JOB_SUBKEY_STAGE: 'build',
                config.JOB_SUBKEY_ALLOW: True,
                config.JOB_SUBKEY_NEEDS:['checkout'],
                config.SUBSECT_KEY_DOCKER_REG:"ghcr.io",
                config.SUBSECT_KEY_DOCKER_IMG:"ubuntu:22.04",
                config.SUBSECT_KEY_ARTIFACT_PATH: 'Github.com/cicd',
                config.JOB_SUBKEY_ARTIFACT:{
                    config.ARTIFACT_SUBKEY_ONSUCCESS: False,
                    config.ARTIFACT_SUBKEY_PATH: ['build/lib', 'build/doc'],
                },
                config.JOB_SUBKEY_SCRIPTS: ['poetry install']
            },
            # Second job with minimal required defined
            'checkout':{
                config.JOB_SUBKEY_STAGE: 'build',
                config.JOB_SUBKEY_SCRIPTS: ['git clone']
            }
        }
    }
    expected_dict = {
        config.SECT_KEY_JOBS: {
            # First job with every things defined
            'compile':{
                config.JOB_SUBKEY_STAGE: 'build',
                config.JOB_SUBKEY_ALLOW: True,
                config.JOB_SUBKEY_NEEDS:['checkout'],
                config.SUBSECT_KEY_DOCKER_REG:"ghcr.io",
                config.SUBSECT_KEY_DOCKER_IMG:"ubuntu:22.04",
                config.SUBSECT_KEY_ARTIFACT_PATH: 'Github.com/cicd',
                config.JOB_SUBKEY_ARTIFACT:{
                    config.ARTIFACT_SUBKEY_ONSUCCESS: False,
                    config.ARTIFACT_SUBKEY_PATH: ['build/lib', 'build/doc'],
                },
                config.JOB_SUBKEY_SCRIPTS: ['poetry install']
            },
            # Second job with minimal required defined
            'checkout':{
                config.JOB_SUBKEY_STAGE: 'build',
                config.JOB_SUBKEY_ALLOW: config.DEFAULT_FLAG_JOB_ALLOW_FAIL,
                config.JOB_SUBKEY_NEEDS: config.DEFAULT_LIST,
                config.SUBSECT_KEY_DOCKER_REG:'docker',
                config.SUBSECT_KEY_DOCKER_IMG: 'ubuntu:latest',
                config.SUBSECT_KEY_ARTIFACT_PATH: 'Github.com',
                config.JOB_SUBKEY_SCRIPTS: ['git clone']
            }
        }
    }
    expected_error_msg = ""
    actual_dict = {}
    passed, error_msg = checker._check_jobs_section(input_dict, actual_dict)
    assert passed
    assert error_msg == expected_error_msg
    assert actual_dict == expected_dict
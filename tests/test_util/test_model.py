""" test the models defined in model.py
"""
import copy
import unittest
import time
import util.constant as c
import util.model as model
from util.common_utils import (get_logger)

logger = get_logger("tests.test_util.test_model")

class TestModel(unittest.TestCase):
    """
    Unit tests for validating models defined in `model.py`.
    """
    def setUp(self):
        self.global_section = {
            c.KEY_PIPE_NAME: "test_pipeline",
            c.KEY_DOCKER:{
                    c.KEY_DOCKER_REG: 'dockerhub',
                    c.KEY_DOCKER_IMG: 'image'
                },
            c.KEY_ARTIFACT_PATH: "/temp"
        }
        self.sample_job_config = {
                c.JOB_SUBKEY_STAGE: 'stage',
                c.JOB_SUBKEY_ALLOW: True,
                c.JOB_SUBKEY_NEEDS: [],
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_REG: 'dockerhub',
                    c.KEY_DOCKER_IMG: 'image'
                },
                c.KEY_ARTIFACT_PATH: 'path',
                c.JOB_SUBKEY_SCRIPTS:['sh','ls'],
            }
        self.sample_session = {
            c.FIELD_USER_ID:"random",
            c.FIELD_REPO_NAME: "cicd-python",
            c.FIELD_REPO_URL: "https://github.com/sjchin88/cicd-python",
            c.FIELD_BRANCH: c.DEFAULT_BRANCH,
            c.FIELD_COMMIT_HASH: "random",
            c.FIELD_IS_REMOTE: True,
        }
        self.sample_stage = {
                    "job_graph": {
                        "checkout": [
                            "compile"
                        ],
                        "compile": []
                    },
                    "job_groups": [
                        [
                            "checkout",
                            "compile"
                        ]
                    ]
        }
        self.sample_pipeline_config = {
            c.KEY_GLOBAL:self.global_section, 
            c.KEY_STAGES:{
                'stage1':self.sample_stage
            },
            c.FIELD_JOBS:{
                'job1':self.sample_job_config
            }
        }

    def test_job_config(self):
        """ Test the JobConfig model
        """
        job_config = model.JobConfig.model_validate(self.sample_job_config)
        print(job_config)
        assert True

    def test_job_log(self):
        """ Test the JobLog model
        """
        sample_job_log = copy.deepcopy(self.sample_job_config)
        sample_job_log[c.REPORT_KEY_JOBNAME] = 'sample_job'
        sample_job_log[c.REPORT_KEY_START] = time.asctime()
        job_log = model.JobLog.model_validate(sample_job_log)
        job_log.completion_time = time.asctime()
        print(job_log.model_dump())
        assert True

    def test_Global_Config(self):
        global_section = model.GlobalConfig.model_validate(self.global_section)
        assert True

    def test_SessionDetail(self):
        session_detail = model.SessionDetail.model_validate(self.sample_session)
        assert True

    def test_validated_stage(self):
        single_stage = model.ValidatedStage.model_validate(self.sample_stage)
        assert True

    def test_pipeline_config(self):
        pipeline = model.PipelineConfig.model_validate(self.sample_pipeline_config)
        assert True

    def test_pipeline_history(self):
        pipeline_history = {
            c.FIELD_PIPELINE_NAME: "sample_pipeline",
            c.FIELD_PIPELINE_FILE_NAME: "sample_pipeline.yml",
            c.FIELD_LAST_COMMIT_HASH: "random",
            c.FIELD_PIPELINE_CONFIG:self.sample_pipeline_config
        }
        history = model.PipelineInfo.model_validate(pipeline_history)
        print(history.model_dump())
        logger.debug(history)

        # Test handling of None field
        pipeline_history = {
            c.FIELD_PIPELINE_NAME: "sample_pipeline",
            c.FIELD_PIPELINE_FILE_NAME: "sample_pipeline.yml",
            c.FIELD_JOB_RUN_HISTORY: None,
            c.FIELD_LAST_COMMIT_HASH: "random",
            c.FIELD_PIPELINE_CONFIG:self.sample_pipeline_config
        }
        history = model.PipelineInfo.model_validate(pipeline_history)
        logger.debug(history)
        assert True


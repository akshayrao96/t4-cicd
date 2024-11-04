""" test the models defined in model.py
"""
import copy
import unittest
import time
import util.constant as c 
import util.model as model

class TestModel(unittest.TestCase):
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

    def test_job_config(self):
        """ Test the JobConfig model
        """
        
        job_config = model.JobConfig.model_validate(self.sample_job_config)
        print(job_config)
        assert True
        #assert job_config == sample_job_config

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
        
# test_job_config()
# test_job_log()
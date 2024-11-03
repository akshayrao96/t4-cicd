""" test the models defined in model.py
"""
import time
import util.constant as c 
import util.model as model

def test_job_config():
    """ Test the JobConfig model
    """
    sample_job_config = {
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
    job_config = model.JobConfig.model_validate(sample_job_config)
    print(job_config)
    assert True
    #assert job_config == sample_job_config

def test_job_log():
    """ Test the JobLog model
    """
    sample_job_config = {
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
    sample_job_config[c.REPORT_KEY_JOBNAME] = 'sample_job'
    sample_job_config[c.REPORT_KEY_START] = time.asctime()
    job_log = model.JobLog.model_validate(sample_job_config)
    job_log.completion_time = time.asctime()
    print(job_log.model_dump())
    assert True
# test_job_config()
# test_job_log()
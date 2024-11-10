""" provide common model class based on pydantic 
for easier validation and formating. 
Note we cant use constant when defining the field here
"""
import time
from collections import OrderedDict
from typing import (Optional, Union)
from pydantic import (BaseModel, Field, field_validator)
import util.constant as c

class DockerConfig(BaseModel):
    """ class to hold configuration for a docker section 
    with registry and image

    Args:
        BaseModel (BaseModel): Base Pydantic Class
    """
    registry: str
    image: str

class ArtifactConfig(BaseModel):
    """ class to hold configuration for an artifact section

    Args:
        BaseModel (BaseModel): Base Pydantic Class
    """
    on_success_only:bool
    paths: list[str]

class JobConfig(BaseModel):
    """ class to hold configuration for a job

    Args:
        BaseModel (BaseModel): Base Pydantic Class
    """
    stage: str
    allow_failure: bool
    needs: list[str]
    docker:DockerConfig
    artifact_upload_path: Optional[str]
    scripts:list[str]
    artifacts:Optional[ArtifactConfig] = None

class JobLog(BaseModel):
    """ class to hold information for a single job

    Args:
        BaseModel (BaseModel): Base Pydantic Class
    """
    job_name:str
    job_status: Optional[str] = c.STATUS_FAILED
    allow_failure: bool
    start_time: str
    # If put Optional the default must be supplied
    completion_time:Optional[str] = time.asctime()
    job_logs:Optional[str] = ""

class SessionDetail(BaseModel):
    """ class to hold information to identify a repo for pipeline run

    Args:
        BaseModel (BaseModel): Base Pydantic Class
    """
    user_id:str
    repo_name:str
    repo_url:str
    branch:str
    commit_hash:str
    is_remote:bool
    last_temp_working_dir:Optional[str] = None
    time:Optional[str] = time.asctime()

class GlobalConfig(BaseModel):
    """ class to hold information for a validated global section

    Args:
        BaseModel (BaseModel): Base Pydantic Class
    """
    pipeline_name:str
    docker:DockerConfig
    artifact_upload_path:str

class ValidatedStage(BaseModel):
    """ class to hold information for a Validated Stage in Stages Section

    Args:
        BaseModel (BaseModel): Base Pydantic Class
    """
    job_graph:dict
    job_groups:list[list]

class PipelineConfig(BaseModel):
    """ class to hold information for a valid pipeline configuration

    Args:
        BaseModel (BaseModel): Base Pydantic Class
    """
    global_:GlobalConfig = Field(alias='global')
    stages : OrderedDict
    jobs:dict

class RawPipelineInfo(BaseModel):
    """ class to hold information for a single pipeline 
    before pipeline config validations
    
    Args:
        BaseModel (BaseModel): Base Pydantic Class
    """
    pipeline_name: str
    pipeline_file_name: str
    pipeline_config: dict

class PipelineInfo(BaseModel):
    """ class to hold information for a single pipeline 
    Args:
        BaseModel (BaseModel): Base Pydantic Class
    """
    pipeline_name: str
    pipeline_file_name: str
    pipeline_config: PipelineConfig
    job_run_history: Optional[list] = []
    active: Optional[bool] = False
    running: Optional[bool] = False
    last_commit_hash: Optional[str] = ""

    @field_validator("job_run_history")
    @classmethod
    def set_job_run_history(cls, job_run_history):
        """ validate the job_run_history field dynamically, 
        so if None value is supplied, or no value is supplied, 
        it will set to empty list

        Args:
            job_run_history (list): existing job_run_history

        Returns:
            list: existing list or new list
        """
        return job_run_history or []

class ValidationResult(BaseModel):
    """ class to hold validation result for a single pipeline 
    Args:
        BaseModel (BaseModel): Base Pydantic Class
    """
    valid: bool
    error_msg: str
    pipeline_config: Union[PipelineConfig, dict]

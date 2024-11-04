""" provide common model class based on pydantic 
for easier validation and formating. 
Note we cant use constant when defining the field here
"""
import time
from typing import Optional
from pydantic import BaseModel
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
    
class GlobalConfig(BaseModel):
    """ class to hold information for a global section

    Args:
        BaseModel (BaseModel): Base Pydantic Class
    """
    pipeline_name:str
    docker:DockerConfig
    artifact_upload_path:str
    
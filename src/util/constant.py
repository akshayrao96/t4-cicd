""" Constants that will be used within this program
"""

# MongoDB Database and Collections
MONGO_DB_NAME = 'CICDControllerDB'
MONGO_PIPELINES_TABLE = 'repo_configs'
MONGO_JOBS_TABLE = 'jobs_history'
MONGO_REPOS_TABLE = 'sessions'

# Common Field Names
FIELD_ID = '_id'  # MongoDB ObjectId field
FIELD_REPO_NAME = 'repo_name'
FIELD_REPO_URL = 'repo_url'
FIELD_BRANCH = 'branch'
FIELD_PIPELINE_NAME = 'pipeline_name'

# Fields for `sessions` Table
FIELD_USER_ID = 'user_id'
FIELD_COMMIT_HASH = 'commit_hash'
FIELD_IS_REMOTE = 'is_remote'
FIELD_TIME = 'time'

# Fields for `repo_configs` Table
FIELD_PIPELINES = 'pipelines'
FIELD_PIPELINE_FILE_NAME = 'pipeline_file_name'
FIELD_PIPELINE_CONFIG = 'pipeline_config'
FIELD_JOB_RUN_HISTORY = 'job_run_history'
FIELD_ACTIVE = 'active'
FIELD_RUNNING = 'running'
FIELD_LAST_COMMIT_HASH = 'last_commit_hash'

# Fields for `jobs_history` Table
FIELD_RUN_NUMBER = 'run_number'
FIELD_GIT_COMMIT_HASH = 'git_commit_hash'
FIELD_PIPELINE_CONFIG_USED = 'pipeline_config_used'
FIELD_STATUS = 'status'
FIELD_START_TIME = 'start_time'
FIELD_COMPLETION_TIME = 'completion_time'
FIELD_LOGS = 'logs'
FIELD_STAGE_NAME = 'stage_name'
FIELD_STAGE_STATUS = 'stage_status'
FIELD_JOBS = 'jobs'
FIELD_JOB_NAME = 'job_name'
FIELD_JOB_STATUS = 'job_status'
FIELD_JOB_ALLOW_FAILURE = 'allow_failure'
FIELD_JOB_LOGS = 'job_logs'

# Job and Stage Statuses
STATUS_PENDING = 'pending'
STATUS_COMPLETE = 'complete'
STATUS_SUCCESS = 'success'
STATUS_FAILED = 'failed'
STATUS_CANCELLED = 'cancelled'

# Pipeline Configurations
DEFAULT_DOCKER_REGISTRY = 'dockerhub'
KEY_GLOBAL = 'global'
KEY_STAGES = 'stages'
KEY_JOBS = 'jobs'
KEY_PIPE_NAME = 'pipeline_name'
KEY_PIPE_CONFIG = 'pipeline_config'
KEY_PIPE_FILE = 'pipeline_file_name'
KEY_DOCKER = 'docker'
KEY_DOCKER_REG = 'registry'
KEY_DOCKER_IMG = 'image'
KEY_ARTIFACT_PATH = 'artifact_upload_path'
KEY_JOB_GRAPH = 'job_graph'
KEY_JOB_ORDER = 'job_groups'
JOB_SUBKEY_STAGE = 'stage'
JOB_SUBKEY_ALLOW = 'allow_failure'
JOB_SUBKEY_NEEDS = 'needs'
JOB_SUBKEY_SCRIPTS = 'scripts'
JOB_SUBKEY_ARTIFACT = 'artifacts'
ARTIFACT_SUBKEY_ONSUCCESS = 'on_success_only'
ARTIFACT_SUBKEY_PATH = 'paths'
RETURN_KEY_VALID = 'valid'
RETURN_KEY_ERR = 'error_msg'
REPORT_KEY_JOBNAME = 'job_name'
REPORT_KEY_JOBSTATUS = 'job_status'
REPORT_KEY_START = 'start_time'
REPORT_KEY_END = 'completion_time'
REPORT_KEY_JOBLOG = 'job_logs'

# Other Constants
DEFAULT_CONFIG_PL_FILE = "pipelines.yml"
DEFAULT_CONFIG_FILE_PATH = ".cicd-pipelines/pipelines.yml"
DEFAULT_CONFIG_DIR = '.cicd-pipelines/'
DEFAULT_S3_LOC = 'us-west-2'
DEFAULT_BRANCH = 'main'
DEFAULT_STAGES = ['build', 'test', 'doc', 'deploy']
DEFAULT_DOCKER_REGISTRY = 'dockerhub'
DEFAULT_FLAG_JOB_ALLOW_FAIL = False
DEFAULT_FLAG_ARTIFACT_UPLOAD_ONSUCCESS = True
DEFAULT_STR = ""
DEFAULT_LIST = []
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_DOCKER_DIR = '/app'
REGEX_SHELL_ERR = r'(sh:\s?)(\d+)(:)'

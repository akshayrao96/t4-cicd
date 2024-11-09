# Main Schema for Datastore

## Tables required

- sessions - Record UserID and Information for repo that the developer is working on.

- repo_configs - Record all pipelines information and status (past and present pipeline) for a particular repo.

- jobs_history - all job runs history

Note: MongoDB will add a ObjectId for each documents

## Table Details (sessions)

Fields required:

- userid (primary key)
- repo_name
- repo_url
- branch
- commit hash working on
- Whether the repo is local / remote
- if remote , last_temp_working_dir
- last access timestamp?

## Table Details (repo_configs)

Fields required:
Primary keys - repo_name, repo_url and branch

- repo_name
- repo_url
- branch
- Pipelines Information and Status (past and present pipeline)
  <!---Consider using key-values pair here, with key = pipeline_name, values = single pipelines_info --->
  - pipeline_name (primary key for pipeline)
  - pipeline_file_name (can be different from pipeline_name)
  - (validated) pipeline_config - pipeline config that failed validation will not be stored
  - job_run_history (list of job runs id for this pipeline)
  - active (boolean flag)
  - running (boolean flag to indicate if this pipeline is currently running)
  - last_commit_hash (use to identify if need to reload and validate new pipeline config)

## Table Detals (jobs_history)

Fields required:

- jobs_id (primary key)
<!---Should probably change pipeline_number to pipeline_name--->
- pipeline_name
- run_number
- git commit hash
- pipeline_config_used
- pipeline_status (success/failed/cancelled)
- logs - organized by stages
  - stage_name
  - stage_status
  - jobs
    <!---Consider using key-values pair here, with key = job_name, values = single job_log info --->
    - job_name
    - job_status
    - allows_failure
    - start_time
    - completion_time
    - logs & error output

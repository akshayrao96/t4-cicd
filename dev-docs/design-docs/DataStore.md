# Main Schema for Datastore

Schema design for the datastore used in the CI/CD system.


---

## Schema Design

### **Tables Required**
1. **sessions**  
   Records `UserID` and details about the repository that the developer is working on.

2. **repo_configs**  
   Stores all pipeline information (past and present) for a particular repository, including pipeline configurations and statuses.

3. **jobs_history**  
   Maintains the history of all job runs, including their statuses and logs.

> **Note:** MongoDB automatically adds an `ObjectId (_id)`for each document.

---

## Table Details

### **1. Sessions**

**Fields Required**:
- `user_id` (Primary Key): Unique identifier for the user.
- `repo_name`: Name of the repository.
- `repo_url`: URL of the repository.
- `branch`: Current branch being worked on.
- `commit_hash`: Commit hash of the current work.
- `is_remote` (Boolean): Indicates whether the repository is local or remote.
- `time`: Timestamp of the last session access.

---

### **2. Repo_Configs**

**Primary Keys**: `repo_name`, `repo_url`, `branch`

**Fields Required**:
- `repo_name`: Name of the repository.
- `repo_url`: URL of the repository.
- `branch`: Current branch being worked on.
- `pipelines`(Dictionary): Contains information about all pipelines (past and present) for the repository
  - `pipeline_name` Key for identifying pipeline items.
  - `pipeline_file_name`: File name associated with the pipeline (may differ from `pipeline_name`).
  - `pipeline_config`: Validated pipeline configuration. Failed validations are not stored.
  - `job_run_history`: List of job run IDs associated with the pipeline.
  - `active`: Boolean flag indicating if the pipeline is active.
  - `running`: Boolean flag indicating if the pipeline is currently running.
  - `last_commit_hash`: Commit hash used to determine if the pipeline configuration needs revalidation.

---

### **3. Jobs_History**

**Fields Required**:
- `pipeline_name`: Name of the associated pipeline.
- `run_number`: Sequential run number for the pipeline.
- `git_commit_hash`: Commit hash used during the job execution.
- `pipeline_config_used`: Configuration of the pipeline used for the job.
- `status`: Status of the job (`success`, `failed`, `canceled`).
- `start_time`: Start timestamp of the job.
- `completion_time`: Completion timestamp of the job.
- `logs`: Organized logs for each stage and job within the stage.
  - **Stage-level logs**:
    - `stage_name`
    - `stage_status`
    - `start_time`
    - `completion_time`
  - **Job-level logs** (within each stage):
    - `job_name`
    - `job_status`
    - `allows_failure`: Boolean flag indicating if failure was allowed for the job.
    - `start_time`
    - `completion_time`
    - `job_logs`

> **Note:** Consider using a key-value pair structure for job logs, where the key is `job_name` and the value is the log information.

---

## Environment Setup

The database URL must be stored in the `~/.bashrc` or `~/.zshrc` file as an environment variable (`MONGO_DB_URL`) to ensure connectivity.

```bash
"export MONGO_DB_URL="<your-mongodb-url>"
```

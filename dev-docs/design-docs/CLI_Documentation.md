# CID Command Line Prompts Documentation

Last updated - 2024-11-21

This documentation outlines all available CID CLI commands that t4-cicd implement.

## `cid`

Base entry point for running cid service
Codebase: `./src/cli/__main__.py`

### `cid`

- **Command**: `cid`
- **Description**: Displays help and shows all available commands associated with `cid`.
- **Input**: None
- **Equivalent**: `cid --help`
- **Output**: Displays all options and commands associated with the `cid` input.

```
% cid

Usage: cid [OPTIONS] COMMAND [ARGS]...

  Main command to run cid

Options:
  -v, --version  Displays version of cid tool
  --help         Show this message and exit.

Commands:
  config    Command working with pipeline and repo configurations
  pipeline  All commands related to pipeline

```

### `cid --version`

- **Description**: Version of the cid service being used
- **Input**: None
- **Output**: Displays current version

```
% cid

cid version 1.0.0
```

## `cid config`

All configurations for the cid service (eg. checking pipelines, checking the repo)
Codebase: `./src/cli/cmd_config.py`

### `cid config`

- **Description**: Checks configuration file for the set repository inside `.cicd-pipelines`. Default file is `pipelines.yml`.
- **Input**: None
- **Equivalent Command**: `cid config --check --config-file pipelines.yml`
- **Output**:
  - Displays key-value pairing of the `pipelines.yml` file if successful.
  - Prints error if the file does not exist, is not formatted properly, or has cyclic dependencies.

```
% cid config

Using config file: pipelines.yml
Checking config file at: pipelines.yml
2024-10-19 16:04:35,876 - util.repo_manager - INFO - Parsing YAML file at /Users/akshayrao/Desktop/zooby/neu/cs6510/project/t4-cicd/.cicd-pipelines/pipelines.yml
Check passed = True
Error message (if any) =

Printing processed_config
{'global': {'artifact_upload_path': 'GitHub.com',
            'docker_image': 'ubuntu:latest',
            'docker_registry': 'dockerhub',
            'pipeline_name': 'valid_pipeline_default'},
 'jobs': ...

 }
```

### `cid config --check --config-file <FILENAME>.yml`

- **Description**: Checks configuration file for the set repository in the `.cicd-pipelines` directory. Will also save valid configuration to the datastore.
- **Input**: `<FILENAME>` is a file with a `.yml` file extension, and it must reside in `.cicd-pipelines/`.
- **Equivalent**: `cid config` if `pipelines.yml` file is given.
- **Output**:
  - Displays key-value pairing of the `.yml` file provided.
  - Prints errors if the file is not found or improperly formatted.
    - FileNotFound or general yaml parsing error - will only print the first error encountered
    - further config validation errors - will print all validation errors found so the user can try to fix it in one go

```
 % cid config --check --config-file valid_config.yml

Using config file: valid_config.yml
Checking config file at: valid_config.yml
2024-10-19 17:03:11,340 - util.repo_manager - INFO - Parsing YAML file at /Users/akshayrao/Desktop/zooby/neu/cs6510/project/t4-cicd/.cicd-pipelines/valid_config.yml
Check passed = True
Error message (if any) =

Printing processed_config
{'global': {'artifact_upload_path': 'GitHub.com',
            'docker_image': 'ubuntu:latest',
            'docker_registry': 'dockerhub',
            'pipeline_name': 'valid_pipeline'},
 'jobs': ...

 }
```

- **Considerations**:
  - Only files in the `.cicd-pipelines` folder are allowed. Running `cid config --check --config-file ./cicd-pipelines/valid_config.yml` results in an error.
  - files with duplicate names are not allowed by any File System. Files with duplicate pipeline names are only check against what is in the datastore.

### `cid config --check --config-file <FILENAME> --no-set`

- **Description**: The --no-set flag allows to check the config file only without further interaction with the cicd system. Ie. it will not set the repo, and will not save the config file to datastore.
- **Input**: `<FILENAME>` is a file with a `.yml` file extension, and it must reside in `.cicd-pipelines/`.
- **Output**: 
  - prints out the configuration file that is in dict form
  - prints error if input filename is not found or error in keys of the configuration file.

```
% cid config --check --config-file pipelines.yml --no-set
checking config file at: .cicd-pipelines/pipelines.yml
Validating file in pipelines.yml
Check passed = True
Error message (if any) =

Printing processed_config
{'global': {'artifact_upload_path': 'temp',
            'docker': {'image': 'sjchin88/python-git-poetry:latest',
                       'registry': 'dockerhub'},
            'pipeline_name': 'cicd_pipeline'},
 'jobs': ...
}
```

### `cid config --check-all`

- **Description**: Checks all configuration file for the set repository in the `.cicd-pipelines` directory. Will also save all valid configurations to the datastore.
- **Input**: None
- **Output**:
  - Displays key-value pairing of the `.yml` file provided.
  - Prints errors if the file is not found or improperly formatted.
    - FileNotFound or general yaml parsing error - will only print the first error encountered
    - further config validation errors - will print all validation errors found so the user can try to fix it in one go
- **Considerations**:
  - Only files in the `.cicd-pipelines` folder will be checked.
  - files with duplicate names are not allowed by any File System. Files with duplicate pipeline names will be checked when loading.

### `cid config --check-all --dir <directory> --no-set`

- csj added 2024-10-19
- **Description**: The --no-set flag allows to check all config files within the directory only without further interaction with the cicd system. Ie. it will not set the repo, and will not save the config file to datastore.
  The directory argument must be supplied.

### `cid config set-repo <REPO>` TODO: need to update

- **Description**: Configures the cid service to work on the given repository.

- **Considerations**:
  - `<REPO>` can be either local or remote?
  - The user must not be in a git repository directory in the terminal when running this command.
  - Need to determine how configurations will work when the project is packaged/unpackaged (binaries).

### `cid config get-repo` TODO: need to update

- **Description**: Returns the repository for the cid service to work on.

- **Considerations**:
  - Return the repository that the user is currently in, if applicable.
  - Otherwise, return the last set repository.

### `cid config override` TODO: need to update

## `cid pipeline`

All pipeline related commands. Pipeline in this case is anything to do with executions of a yaml file
Codebase: `./src/cli/cmd_pipeline.py`

### `cid pipeline`
- **Description**: Returns help for commands to run for `cid pipeline`.
- **Input**: None
- **Output**: Help commands.

```
% cid pipeline

Usage: cid pipeline [OPTIONS] COMMAND [ARGS]...

  All commands related to pipeline

Options:
  --help  Show this message and exit.

Commands:
  report  Report pipeline provides user to retrieve the pipeline history.
  run     Run pipeline given the configuration file.
```

### `cid pipeline run`

- **Description**: Runs the default pipeline file `.cicd-pipelines/pipelines.yml`
- **Input**: None
- **Output**: Real-time output log of the pipeline running.
- **Equivalent Command**: `cid pipeline run --file pipelines.yml

```
% cid pipeline run
Repository is configured in current directory
Validating file in pipelines.yml
Remote run feature is not implemented, still running pipeline on local
Stage:build Job:checkout - Streaming Job Logs
Cloning into '.'
...
Job:checkout success

Stage:build Job:compile - Streaming Job Logs
Creating virtualenv cicd-python-9TtSrW0h-py3.12 in /app/.cache/pypoetry/virtualenvs
Installing dependencies from lock file
...
```

- **Brief Description of Handling Logic**:
  - The program will first check if the user is in a git repository.
    - If the user is in git repository, but target repo is provided and different, the program will throw error (cannot run command for other repo in an existing repo)
    - Else, the program will try to switch to target branch and commit.
  - If the user is not in a git repository,
    - If target repo is provided, it will try to set the current directory to target repo, branch and commit
    - Else, it will try to set the current directory to previously used repository, branch and commit by the user
  - Second check is on the --pipeline and --file arguments, only one should be supplied.
    - The program will try to extract the yaml file content based on given --pipeline or --file
  - Third step, process and try to apply the overrides if any
  - Fourth step, validated the pipeline configuration
  - Fifth step, determine if this is going to be a dry-run
  - For non dry-run, actual run will be perform.

### `cid pipeline run --dry-run`

- **Description**: Informs the user what would happen if the pipeline was run (dry-run mode).
- **Equivalent Command**: `cid pipeline run --dry-run --file .cicd-pipelines/pipelines.yml`
- **Considerations**:
  - Same as the considerations for running a pipeline, but no actual artifacts will be generated since nothing will be run.

```sh
% cid pipeline run --dry-run       
Repository is configured in current directory
Validating file in pipelines.yml

===== [INFO] Global =====
pipeline_name: cicd_pipeline, docker: {'registry': 'dockerhub', 'image': 'sjchin88/python-git-poetry:latest'}, artifact_upload_path: temp, 

===== [INFO] Stages: 'build' =====
Running job: "checkout", ..., docker: {'registry': 'dockerhub', 'image': 'sjchin88/python-git-poetry:latest'}

===== [INFO] Stages: 'test' =====
Running job: "pylint", ..., docker: {'registry': 'dockerhub', 'image': 'sjchin88/python-git-poetry:latest'}, artifacts: {'on_success_only': False, 'paths': ['htmlcov']}
```

### `cid pipeline run --dry-run --pipeline <PIPELINE_NAME>`
- **Description**: In dry-run, user is able to specify the Pipeline Name that they define in `global.pipeline_name` in the yaml file.
- **Input**: `pipeline_name` that validate the configuration file
- **Output**: print the dry run jobs in the order that is specified in the file. 
```sh
% cid pipeline run --dry-run --pipeline cicd-javascript        
Repository is configured in current directory
Validating file in javascript-template.yml

===== [INFO] Global =====
pipeline_name: cicd-javascript, docker: {'registry': 'dockerhub', 'image': 'node:latest'}, artifact_upload_path: temp, 

===== [INFO] Stages: 'build' =====
...
```

### `cid pipeline report --help`
- **Description**: Returns help for commands to run for cid pipeline.
- **Input**: None
- **Output**: Help commands.
- **Reason**:
  - unlike `cid config` or `cid pipeline run`, `report` requires user to specify `--repo` on which repo to view. if not specified it will output error
  ```sh 
  % cid pipeline report                                                 
  
  "missing ['repo_url'] input. please run cid pipeline report--repo. For further help, run cid pipeline report --help for valid usage"
  ```


### `cid pipeline report --repo <REPO_URL>`
- **Description**: display report for all pipelines for the REPO_URL specified
- **Input**: repository URL to get the history 
- **Output**: 
  - provides the overview of the history, such as pipeline name, run #, status, and other details.

```sh
Pipeline Name: cicd_pipeline
Run Number: 1
Git Commit Hash: 16adc46
Status: success
Start Time: Sun Nov 10 17:33:33 2024
Completion Time: Sun Nov 10 17:33:48 2024
Pipeline Name: cicd_pipeline
Run Number: 2
...
Pipeline Name: cicd_pipeline2
Run Number: 1
Git Commit Hash: 16adc46
Status: success
Start Time: Sun Nov 10 19:32:05 2024
Completion Time: Sun Nov 10 19:32:18 2024
Pipeline Name: cicd_pipeline2
Run Number: 2
...
```

### `cid pipeline report --repo <REPO_URL> --pipeline PIPELINE_NAME`
- **Description**: display report for the given PIPELINE_NAME for the REPO_URL specified
- **Input**: 
  - repository URL to get the history 
  - pipeline_name to filter
- **Output**:
  - provides the overview of the history, such as pipeline name, run #, status, and other details.
```
cid pipeline report --repo https://github.com/sjchin88/cicd-python --pipeline cicd_pipeline
Pipeline Name: cicd_pipeline
Run Number: 1
Git Commit Hash: 16adc46
Status: success
Start Time: Sun Nov 10 17:33:33 2024
Completion Time: Sun Nov 10 17:33:48 2024
Pipeline Name: cicd_pipeline
Run Number: 2
Git Commit Hash: 16adc46
...
```
### `cid pipeline report --repo <REPO_URL> --pipeline PIPELINE_NAME --run RUN_NUMBER`
- **Description**: display report for all pipelines for the REPO_URL specified
- **Input**: 
  - repository URL to get the history 
  - specific pipeline_name for the report
  - the run number
- **Output**: 
  - provides the overview of the history, such as pipeline name, run #, status, and other details.
  - in addition, more details on the `Stages` that includes list of stage name, status, and start / completion time
```
cid pipeline report --repo https://github.com/sjchin88/cicd-python --pipeline cicd_pipeline --run 1                              
Pipeline Name: cicd_pipeline
Run Number: 1
Git Commit Hash: 16adc46
Status: success
Start Time: Sun Nov 10 17:33:33 2024
Completion Time: Sun Nov 10 17:33:48 2024
Stages:
  Stage Name: build
  Status: success
  Start Time: Sun Nov 10 17:33:33 2024
  Completion Time: Sun Nov 10 17:33:48 2024

  Stage Name: test
  Status: success
  Start Time: Sun Nov 10 17:33:33 2024
  Completion Time: Sun Nov 10 17:33:48 2024
```
### `cid pipeline report --repo <REPO_URL> --pipeline PIPELINE_NAME --stage STAGE`
- **Description**: display the report for the specific stage (build, test) for all pipelines
- **Input**: 
  - repository URL to get the history 
  - specific pipeline_name for the report
  - stage name
- **Output**: 
  - provides the overview of the history, such as pipeline name, run #, status, and other details.
  - Details on the `Stages` that includes list of stage name, status, and start / completion time
  - In addition, provide `Jobs` information that is part of the Stage.

Note: user can specify the run number (ex. `--run 1`) to  only limit the report to just a single run. The report will yield to the same output.

```
% cid pipeline report --repo https://github.com/sjchin88/cicd-python --pipeline cicd_pipeline --stage test 
Pipeline Name: cicd_pipeline
Run Number: 1
Git Commit Hash: 16adc46
Stage Name: test
Stage Status: success
Jobs:
  Job Name: pylint
    Job Status: success
    Allows Failure: False
    Start Time: Sun Nov 10 17:33:41 2024
    Completion Time: Sun Nov 10 17:33:45 2024

  Job Name: pytest
    Job Status: success
    Allows Failure: False
    Start Time: Sun Nov 10 17:33:45 2024
    Completion Time: Sun Nov 10 17:33:48 2024

Pipeline Name: cicd_pipeline
Run Number: 2
Git Commit Hash: 16adc46
Stage Name: test
Stage Status: success
Jobs:
  Job Name: pylint
    Job Status: success
    Allows Failure: False
    Start Time: Sun Nov 10 19:30:11 2024
    Completion Time: Sun Nov 10 19:30:15 2024

  Job Name: pytest
    Job Status: success
    Allows Failure: False
    Start Time: Sun Nov 10 19:30:15 2024
    Completion Time: Sun Nov 10 19:30:18 2024

Pipeline Name: cicd_pipeline
...
```

### `cid pipeline report --repo <REPO_URL> --pipeline PIPELINE_NAME --stage STAGE_NAME --job JOB_NAME`
- **Description**: display the report for the specific job (pylint, pytest, etc) for all pipelines
- **Input**: 
  - repository URL to get the history 
  - specific pipeline_name for the report
  - stage name
- **Output**: 
  - provides the overview of the history, such as pipeline name, run #, status, and other details.
  - Details on the `Stages` that includes list of stage name, status, and start / completion time
  - In addition, provide `Jobs` information that is part of the Stage.

```sh
cid pipeline report --repo https://github.com/sjchin88/cicd-python --pipeline cicd_pipeline --stage test --job pylint --run 1
Pipeline Name: cicd_pipeline
Run Number: 1
Git Commit Hash: 16adc46
Stage Name: test
Job Name: pylint
Job Status: success
Allows Failure: False
Start Time: Sun Nov 10 17:33:41 2024
Completion Time: Sun Nov 10 17:33:45 2024

```
- **Input Validation**:
  - `--stage` must be given if user want to specify the `--job`.
  ```sh
  % cid pipeline report --repo https://github.com/sjchin88/cicd-python --pipeline cicd_pipeline --job pylint            
  
  "missing flag. --stage flag must be given along with --job"
  ```
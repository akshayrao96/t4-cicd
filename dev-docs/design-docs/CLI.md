# CID Command Line Prompts Documentation

Last updated - 2024-11-28

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

```sh
$ cid

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

```sh
$ cid --version

cid version 0.1.0
```

## `cid config`

All configurations for the cid service (eg. checking pipelines, checking the repo)
Codebase: `./src/cli/cmd_config.py`

```sh
$ cid config --help
Usage: cid config [OPTIONS] COMMAND [ARGS]...

  Command working with pipeline and repo configurations

  This command allows you to manage and validate configuration files used in
  pipeline executions. You can run this to check the configuration files in
  default location or pass a custom file/directory to check.

Options:
  --check             checks the validity of the YAML configuration file.
                      Default behaviour. If this option is selected, the --dir
                      argument will be ignored.
  --check-all         checks validity of all YAML configuration files.
                      If this option is selected, the --config-file argument
                      will be ignored.
  --no-set            validate the config/configs without setting the repo and
                      saving the validated info to datastore
  --config-file TEXT  specifies the YAML configuration file to check.
                      used with --check flag. If not specified, default to
                      .cicd-pipelines/pipelines.yml  [default: pipelines.yml]
  --dir TEXT          specify the directory to check all configuration files.
                      used with --check-all flag  [default: .cicd-pipelines/]
  --json              output in json format
  --help              Show this message and exit.

Commands:
  get-repo  Display information about the currently configured repository.
  override  Apply configuration overrides to a pipeline configuration...
  set-repo  Configure a new repository for pipeline checks in the current...
```

### `cid config`

- **Description**: Checks configuration file for the set repository inside `.cicd-pipelines`. Default file is `pipelines.yml`.
- **Input**: None
- **Equivalent Command**: `cid config --check --config-file pipelines.yml`
- **Output**:
  - Displays key-value pairing of the `pipelines.yml` file if successful.
  - Prints error if the file does not exist, is not formatted properly, or has cyclic dependencies.
  - a json flag `--json` can be used to print all validation output in json format when available.

```sh
$ cid config

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
- **Input**: `<FILENAME>` is a file with a `.yml` file extension, if no directory information is given the program will assume it resides in `.cicd-pipelines/`. You can also specify an absolute file path, eg `.cicd-pipelines/pipelines.yml`
- **Equivalent**: `cid config` if `pipelines.yml` file is given.
- **Output**:
  - Displays key-value pairing of the `.yml` file provided.
  - Prints errors if the file is not found or improperly formatted.
    - FileNotFound or general yaml parsing error - will only print the first error encountered
    - further config validation errors - will print all validation errors found so the user can try to fix it in one go

```sh
 $ cid config --check --config-file valid_config.yml

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
  - Files with duplicate names are not allowed by any File System.
  - Files with duplicate pipeline names will be checked and detected when
    - performing cid config --check-all on the entire directory
    - attempt to run the pipeline based on target pipeline name.

### `cid config --check --config-file <FILENAME>.yml --no-set`

- **Description**: The --no-set flag allows to check the config file only without further interaction with the cicd system. Ie. it will not set the repo, and will not save the config file to datastore.
- **Input**: `<FILENAME>` is a file with a `.yml` file extension, if no directory information is given the program will assume it resides in `.cicd-pipelines/`. You can also specify an absolute file path, eg `.cicd-pipelines/pipelines.yml`
- **Output**:
  - prints out the configuration file that is in dict form
  - prints error if input filename is not found or error in keys of the configuration file.

```sh
$ cid config --check --config-file pipelines.yml --no-set
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
- **Equivalent**: `cid config --check-all --dir .cicd-pipelines`
- **Output**:
  - Displays key-value pairing of the `.yml` file provided.
  - Prints errors if the file is not found or improperly formatted.
    - FileNotFound or general yaml parsing error - will only print the first error encountered
    - further config validation errors - will print all validation errors found so the user can try to fix it in one go
- **Considerations**:
  - Only files in the `.cicd-pipelines` folder will be checked.
  - files with duplicate names are not allowed by any File System. Files with duplicate pipeline names will be checked when loading.

```sh
$ cid config --check-all
Repository is configured in current directory
.cicd-pipelines
set repo, checking and saving all config files in directory .cicd-pipelines
...
Status for invalid_pipeline:failed
error message:
invalid_config.yml:11:8 Error in section:jobs job:nostage No stage key defined
invalid_config.yml:17:15 Error in section:jobs job:wrongstage stage value ['wrong-stage'] defined does not exist in stages list
Error in section:stages stage:deploy No job defined for this stage
invalid_config.yml:11:8 jobs:nostage key not found error for subkey:stage
invalid_config.yml:23:8 jobs:checkout key not found error for subkey:scripts
invalid_config.yml:50:12 jobs:compile no artifact upload path defined
jobs:pytest key not found error for subkey:image

Status for cicd-javascript:passed
printing top 10 lines of processed config:
{'global': {'artifact_upload_path': 'test-cicd-cs6510',
            'docker': {'image': 'node:latest', 'registry': 'dockerhub'},
            'pipeline_name': 'cicd-javascript'},
 'jobs': {'checkout': {'allow_failure': False,
                       'artifact_upload_path': 'test-cicd-cs6510',
                       'docker': {'image': 'node:latest',
                                  'registry': 'dockerhub'},
                       'needs': [],
                       'scripts': ['git clone '
                                   'https://github.com/sjchin88/cicd-javascript '
...
```

### `cid config --check-all --dir <directory> --no-set`

- **Description**: The --dir option allows user to supply a custom directory to check all the configuration file inside. The --no-set flag allows to check all config files within the directory only without further interaction with the cicd system. Ie. it will not set the repo, and will not save the config file to datastore.
- **Input**: an absolute folder path location to validate the configuration files.
- **Output**: will out the same as running `cid config --check-all` when directory is set to .cicd-pipelines/
- **Consideration**:
  - return error if directory given is an invalid with error message `Invalid directory:<dir>`

### `cid config set-repo REPO_URL`

```sh
$ cid config set-repo --help
Usage: cid config set-repo [OPTIONS] REPO_URL

  Configure a new repository for pipeline checks in the current directory.

  This command clones the specified repository into the current working
  directory (PWD) and optionally checks out the specified branch and commit.
  The current directory must be empty for this operation to succeed.
  ...

Options:
  --branch TEXT  Specify the branch to retrieve. If not given, 'main' is used.
  --commit TEXT  Specify the commit hash to retrieve. If not given, latest
                 commit is used.
  --help         Show this message and exit.
```

- **Description**: Configures the cid service to work on the given repository.
- **Input**: valid public repository url (such as https://www.github.com, git@github.com, https://www.gitlab.com), or local repository directory.
- **Output**:
  - On success: Displays the repository details (URL, branch, and commit hash).
  - On failure: Displays an error message indicating the reason for failure.
- **Considerations**:
  - The repository is cloned into the PWD.
  - If `--branch` is provided, the specified branch is checked out (default: 'main').
  - If `--commit` is provided, the specified commit is checked out. If not provided,
    the latest commit on the branch is used.
  - If the current directory is not empty, the operation will fail with an error message.

```sh
#On success
empty-repo $ cid config set-repo https://github.com/sjchin88/cicd-python
Repository set successfully.

Current working directory configured:

Repository URL: https://github.com/sjchin88/cicd-python
Repository Name: cicd-python
Branch: main
Commit Hash: 9bbc007bcf0e20eabb58765983e0722e8c7f39f4

#On failure
t4-cicd git:(main) $ cid config set-repo https://github.com/sjchin88/cicd-python
Currently in a Git repository: 't4-cicd'. Please navigate to an empty directory.
```

### `cid config get-repo`

```sh
$ cid config get-repo --help
Usage: cid config get-repo [OPTIONS]

  Display information about the currently configured repository.

  This command retrieves and displays details of the currently configured Git
  repository, either from the current working directory if it is a Git
  repository, or from the last set repository stored in the system.

  ...
Options:
  --help  Show this message and exit.
```

- **Description**: Returns the repository for the cid service to work on.
- **Input**: None
- **Output**: Repository information of the saved repository
- **Considerations**:
  - If the current directory is a Git repository, it displays the URL, branch, and latest commit hash.
  - If the current directory is not a Git repository but a previous repository configuration
    exists, it retrieves and displays details of the last configured repository.
  - If no repository is configured, it provides guidance for setting a repository.

```sh
$ cid config get-repo
Repository is configured in current directory

Repository configured in current working directory:

Repository URL: git@github.com:CS6510-SEA-F24/t4-cicd.git
Repository Name: t4-cicd
Branch: 124-project-documentation
Commit Hash: 8ea04ac58b62ef65e8d2328f7b29d28943fbd13a
```

### `cid config override`

```sh
$ cid config override --help
Usage: cid config override [OPTIONS]

  Apply configuration overrides to a pipeline configuration stored in the
  database,  check the validation result.  Override configurations in
  'key=value' format. Multiple overrides can be provided.

  Example usage:     cid config override --pipeline pipeline_name --override
  "global.docker.image=gradle:jdk8"

Options:
  --pipeline TEXT  pipeline name to update  [required]
  --override TEXT  Override configuration in 'key=value' format
  --save           flag to save the overrides config into database
  --json           output in json format
  --help           Show this message and exit.
```

**Additional notes**:

- Main usage scenario - check the overrides on configuration without saving.
- The initial pipeline configuration for target pipeline name need to be saved into the datastore (MongoDB) first using the cid config command or previous cid pipeline run commands.
- The `--save` option allow user to save the override configuration, default is not saving.
- The `--json` flag allow display of the validated configuration in json format.

## `cid pipeline`

All pipeline related commands. Pipeline in this case is anything to do with executions of a yaml file
Codebase: `./src/cli/cmd_pipeline.py`

```sh
$ cid pipeline

Usage: cid pipeline [OPTIONS] COMMAND [ARGS]...

  All commands related to pipeline

Options:
  --help  Show this message and exit.

Commands:
  report  Report pipeline provides user to retrieve the pipeline history.
  run     Run pipeline given the configuration file.
```

### `cid pipeline [--help]`

- **Description**: Returns help for commands to run for `cid pipeline`.
- **Input**: None
- **Output**: Help commands.

### `cid pipeline run`

- **Description**: Runs the default pipeline file `.cicd-pipelines/pipelines.yml`
- **Input**: None
- **Output**: Real-time output log of the pipeline running.
- **Equivalent Command**: `cid pipeline run --file .cicd-pipelines/pipelines.yml`

```sh
$ cid pipeline run --help
Usage: cid pipeline run [OPTIONS]

  Run pipeline given the configuration file. Base command is cid pipeline run,
  this will run the pipeline specified in .cicd-pipelines/pipelines.yml for
  current repository or  previously set repository.

  To change the target repository, branch, commit, target pipeline by name /
  file path,  use the corresponding options.

Options:
  --file TEXT        configuration file path. if --file not specified, default
                     to .cicd-pipelines/pipelines.yml
  --pipeline TEXT    pipeline name to run
  -r, --repo TEXT    repository url or local directory path
  -b, --branch TEXT  repository branch name
  -c, --commit TEXT  commit hash
  --local            run pipeline locally
  --dry-run          dry-run options to simulate the pipeline process
  --yaml             print validated config in yaml format for dry run
  --override TEXT    Override configuration in 'key=value' format
  --help             Show this message and exit.


$ cid pipeline run
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

### `cid pipeline run --file FILE_NAME`

- **Description**: User is able to specify the file name they want to run. Default to .cicd-pipelines/pipelines.yml If directory information is absent, will look for file within the .cicd-pipelines/ folder. Applicable to --dry-run command option as well. Not compatible with --pipeline option, if both arguments are given will raise error.
- **Input**: `PIPELINE_NAME` to be executed
- **Output**: perform actual run / dry run based on pipeline name

### `cid pipeline run --pipeline PIPELINE_NAME`

- **Description**: User is able to specify the Pipeline Name that they define in `global.pipeline_name` in the yaml file. The yaml file need to reside on the .cicd-pipelines/ directory.
  Applicable to --dry-run command option as well. Not compatible with --file option.
- **Input**: `PIPELINE_NAME` to be executed
- **Output**: perform actual run / dry run based on pipeline name

```sh
% cid pipeline run --dry-run --pipeline cicd-javascript
Repository is configured in current directory
Validating file in javascript-template.yml

===== [INFO] Global =====
pipeline_name: cicd-javascript, docker: {'registry': 'dockerhub', 'image': 'node:latest'}, artifact_upload_path: temp,

===== [INFO] Stages: 'build' =====
...
```

### `cid pipeline run --repo REPO_URL --branch BRANCH --commit COMMIT`

**Description**: User can run the pipeline for specific repository, branch and commit. The details behaviour are as follow

- If REPO_URL is given, the command must be run in an empty directory. The specific REPO_URL, branch and commit will be checked out.
- If REPO_URL is not given, but target Branch and Commit are given. The command must be running in the root level of a Git Repository. The program will attempt to switch to target branch and commit.
- If Commit is given and is not the latest commit of the target branch, the repository will be checkout with the HEAD in DETACHED state, this allow the users to switch back to the latest commit via `git switch -` without loosing any of the development works between the latest commit and target commit.
- BRANCH if not given will be defaulted to current active branch.
- COMMIT if not given will be defaulted to the latest commit of target branch.

### `cid pipeline run --dry-run`

- **Description**: Informs the user what would happen if the pipeline was run (dry-run mode).
- **Equivalent Command**: `cid pipeline run --dry-run --file .cicd-pipelines/pipelines.yml`
- **Considerations**:
  - Same as the considerations for running a pipeline, but no actual artifacts will be generated since nothing will be run.
  - The pipeline configuration used for the dry-run will be saved into the datastore (MongoDB), if you just want to check the configuration without saving,
    look at the cid config and cid config override commands.

```sh
$ cid pipeline run --dry-run
Repository is configured in current directory
Validating file in pipelines.yml

===== [INFO] Global =====
pipeline_name: cicd_pipeline, docker: {'registry': 'dockerhub', 'image': 'sjchin88/python-git-poetry:latest'}, artifact_upload_path: temp,

===== [INFO] Stages: 'build' =====
Running job: "checkout", ..., docker: {'registry': 'dockerhub', 'image': 'sjchin88/python-git-poetry:latest'}

===== [INFO] Stages: 'test' =====
Running job: "pylint", ..., docker: {'registry': 'dockerhub', 'image': 'sjchin88/python-git-poetry:latest'}, artifacts: {'on_success_only': False, 'paths': ['htmlcov']}
```

### `cid pipeline run --dry-run --yaml`

- **Description**: print validated config in yaml format for dry run, in addition of dry run result.

### `cid pipeline run --override <OVERRIDE> [OPTIONS]`

- **Description**: perform override of target pipeline configuration
- **Input**: `OVERRIDE` key.value to change from the configuration file.
- **Output**: For dry run only: print the configuration file in plain text or yaml (if `--yaml` flag is specified)

```sh
% cid pipeline run --override global.docker.image=gradle:jdk8 --dry-run --yaml
Repository is configured in current directory
Validating file in pipelines.yml
global:
  pipeline_name: cicd_pipeline
  docker:
    registry: dockerhub
    image: sjchin88/python-git-poetry:latest
  artifact_upload_path: test-cicd-cs6510
jobs:
    ...
```

### `cid pipeline report --help`

```sh
$ cid pipeline report --help
Usage: cid pipeline report [OPTIONS]

  Report pipeline provides user to retrieve the pipeline history.

Options:
  -r, --repo TEXT    url of the repository (https://)
  --local            retrieve local pipeline history
  --pipeline TEXT    pipeline name to get the history
  -b, --branch TEXT  branch name of the repository; default is 'main'
  -s, --stage TEXT   stage name to view report; default stages options:
                     [build, test, doc, deploy]
  --job TEXT         job name to view report
  -r, --run TEXT     run number to get the report
  --help             Show this message and exit.
```

- **Description**: Returns help for commands to run for cid pipeline.
- **Input**: None
- **Output**: Help commands.

### `cid pipeline report [--repo REPO_URL]`

- **Description**: display report for all pipelines for the REPO_URL specified. If not specified, repo default to the current repo stored in MongoDB.
- **Input**: repository URL to get the history
- **Output**:
  - provides the overview of the history, such as pipeline name, branch name, run #, status, and other details.

```sh
Pipeline Name: cicd_pipeline
Branch Name: main
Run Number: 1
Git Commit Hash: 16adc46
Status: success
Start Time: Sun Nov 10 17:33:33 2024
Completion Time: Sun Nov 10 17:33:48 2024
Pipeline Name: cicd_pipeline
Run Number: 2
...
Pipeline Name: cicd_pipeline2
Branch Name: development
Run Number: 1
Git Commit Hash: 16adc46
Status: success
Start Time: Sun Nov 10 19:32:05 2024
Completion Time: Sun Nov 10 19:32:18 2024
Pipeline Name: cicd_pipeline2
Run Number: 2
...
```

### `cid pipeline report --repo REPO_URL --pipeline PIPELINE_NAME`

- **Description**: display report for the given PIPELINE_NAME for the REPO_URL specified
- **Input**:
  - repository URL to get the history
  - pipeline_name to filter
- **Output**:
  - provides the overview of the history, such as pipeline name, run #, status, and other details.

```
cid pipeline report --repo https://github.com/sjchin88/cicd-python --pipeline cicd_pipeline
Pipeline Name: cicd_pipeline
Branch Name: main
Run Number: 1
Git Commit Hash: 16adc46
Status: success
Start Time: Sun Nov 10 17:33:33 2024
Completion Time: Sun Nov 10 17:33:48 2024

Pipeline Name: cicd_pipeline
Branch Name: main
Run Number: 2
Git Commit Hash: 16adc46
...
```

### `cid pipeline report --repo REPO_URL --pipeline PIPELINE_NAME --run RUN_NUMBER`

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
Branch Name: main
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

### `cid pipeline report --repo REPO_URL --pipeline PIPELINE_NAME --stage STAGE`

- **Description**: display the report for the specific stage (build, test) for all pipelines
- **Input**:
  - repository URL to get the history
  - specific pipeline_name for the report
  - stage name
- **Output**:
  - provides the overview of the history, such as pipeline name, run #, status, and other details.
  - Details on the `Stages` that includes list of stage name, status, and start / completion time
  - In addition, provide `Jobs` information that is part of the Stage.

Note: user can specify the run number (ex. `--run 1`) to only limit the report to just a single run. The report will yield to the same output.

```
% cid pipeline report --repo https://github.com/sjchin88/cicd-python --pipeline cicd_pipeline --stage test
Pipeline Name: cicd_pipeline
Branch Name: main
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
Branch Name: main
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

### `cid pipeline report --repo REPO_URL --pipeline PIPELINE_NAME --stage STAGE_NAME --job JOB_NAME`

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
Branch Name: main
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

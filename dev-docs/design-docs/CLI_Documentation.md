# CID Command Line Prompts Documentation

Last updated - 2024-11-09

This documentation outlines all available CID CLI commands and their current implementation status.
Each command is tagged with its requirement abbreviation (L1, etc.) and implementation priority level.
Commands that are stubbed (function definition exists but logic is not yet added) are marked with a priority:

- `0` - Highest priority (for this sprint)
- `1` - Medium priority (not important yet)
- `2` - Low priority (not a requirement but useful to have)

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
  config    Configuration commands for pipelines.
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

### `cid --logs` **(not implemented, 2)**

- **Description**: All logs ran by the cli client. Not repository dependent, but useful for the client to see what they've ran so far.
- **Considerations**:
  - Logs from the time the cid service started?
  - All logs so far?
  - Somehow store the current client's history (e.g., IP address)?

## `cid config`

All configurations for the cid service (eg. checking pipelines, checking the repo)
Codebase: `./src/cli/cmd_config.py`

### `cid config`

- **Description**: Checks configuration file for the set repository inside `.cicd-pipelines`. Default file is `pipelines.yml`.
- **Input**: None
- **Equivalent**: `cid config --check --config-file pipelines.yml`
- **Output**:
  - Displays key-value pairing of the `pipelines.yml` file if successful.
  - Prints error if the file does not exist, is not formatted properly, or has cyclic dependencies.

```
% cid config

Using config file: pipelines.yml
Checking config file at: pipelines.yml
2024-10-19 16:04:35,876 - util.repo_manager - INFO - Parsing YAML file at /Users/akshayrao/Desktop/zooby/neu/cs6510/project/t4-cicd/.cicd-pipelines/pipelines.yml
Check pass or fail = True
Error message (if any) =

Printing processed_config
{'global': {'artifact_upload_path': 'GitHub.com',
            'docker_image': 'ubuntu:latest',
            'docker_registry': 'dockerhub',
            'pipeline_name': 'valid_pipeline_default'},
 'jobs': ...

 }
```

- **Considerations**:
  - What to exactly show to client?

### `cid config --check --config-file <FILENAME>`

- **Description**: Checks configuration file for the set repository in the `.cicd-pipelines` directory. Will also save valid configuration to the datastore.
- **Input**: `<FILENAME>` is a file with a `.yml` file extension, and it must reside in `.cicd-pipelines`.
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
Check pass or fail = True
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

- csj added 2024-10-19
- **Description**: The --no-set flag allows to check the config file only without further interaction with the cicd system. Ie. it will not set the repo, and will not save the config file to datastore.

### `cid config --check-all`

- csj added 2024-10-19
- **Description**: Checks all configuration file for the set repository in the `.cicd-pipelines` directory. Will also save all valid configurations to the datastore.
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

### `cid config --set-url <REPO>` **(not implemented, 0)**

- **Description**: Configures the cid service to work on the given repository.

- **Considerations**:
  - `<REPO>` can be either local or remote?
  - The user must not be in a git repository directory in the terminal when running this command.
  - Need to determine how configurations will work when the project is packaged/unpackaged (binaries).

### `cid config --get-url` **(not implemented, 0)**

- **Description**: Returns the repository for the cid service to work on.

- **Considerations**:
  - Return the repository that the user is currently in, if applicable.
  - Otherwise, return the last set repository.

## `cid pipeline`

All pipeline related commands. Pipeline in this case is anything to do with executions of a yaml file
Codebase: `./src/cli/cmd_pipeline.py`

### `cid pipeline`

- **Description**: Returns help for commands to run for `cid pipeline`.
- **Input**: None
- **Output**: Help commands.

```
% cid pipeline

Run pipeline check with default config file path=.cicd-pipelines/pipeline.yml
Usage: cid pipeline [OPTIONS] COMMAND [ARGS]...

  All commands related to pipeline

Options:
  --help  Show this message and exit.

Commands:
  log  Obtains logs of pipeline run attached to current repository
  run  Run pipeline given the configuration file.
```

#### `cid pipeline run`

- **Description**: Runs the pipelines for the repository set.
- **Current usage**:

```
% cid pipeline run

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
  --dry-run          dry-run options to simulate the pipelineprocess
  --yaml             print output in yaml format
  --override TEXT    Override configuration in 'key=value' format
  --help             Show this message and exit.
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

### `cid pipeline --dry-run`

- **Description**: Informs the user what would happen if the pipeline was run (dry-run mode).
- **Considerations**:
  - Same as the considerations for running a pipeline, but no actual artifacts will be generated since nothing will be run.

### `cid pipeline log` **(stub, not implemented, 1)**

- **Description**: Gets logs for a particular pipeline (repository-dependent, most likely client-dependent). Hash code of each run is stored.
- **Input**: `--tail <n>` can be added to extract only the last `n` lines.
- **Current Usage (stub, no logic yet)**:

```
% cid pipeline log

Last pipeline command output: local : 60105820

[2024-10-01 10:00:00] Starting pipeline 'Build and Test'
[2024-10-01 10:00:10] Build: Success
[2024-10-01 10:00:20] Test: Running tests...
[2024-10-01 10:01:00] Test: Success
[2024-10-01 10:02:00] Deploy: Success
[2024-10-01 10:03:00] Pipeline 'Build and Test' completed.

[60105820] Pipeline 'Build and Test' completed.
```

- **Considerations**:
  - What exactly should be retrieved from the logs? The design of this will help inform the database schema design.

# Feature Status

This document provides an overview of the current state of features for the CI/CD project, including implemented and partially implemented functionality.

---

## Overview

This CI/CD tool lets developers run YAML-based pipelines locally on their machines. It supports running pipelines against Java, JavaScript and Python repository local or remote, given a branch and/or commit. This eliminates the need to push changes to external services like GitHub Actions for testing.

The tool is packaged into a single binary, with a CLI offering documentation.

---

## Implemented Features

| Abbr.  | Feature                          | Description                                                                                           | Notes              |
| ------ | -------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------ |
| U1     | Remote Repo Local CI/CD Run      | Run a CI/CD pipeline locally for a public Git repository using the CLI.                               | Fully implemented. |
| U2     | Local Repo Local CI/CD Run       | Run a CI/CD pipeline locally for a cloned Git repository on the developer's machine.                  | Fully implemented. |
| C1     | Configuration File Location      | All configuration files are stored in a `.cicd-pipelines` folder in the target repository.            | Fully implemented. |
| C2     | Independent Configuration Files  | Each configuration file defines a pipeline independently with no cross-file dependencies.             | Fully implemented. |
| C3     | Global Configuration Section     | Define global properties like pipeline name, docker image, and artifact paths at the pipeline level.  | Fully implemented. |
| C3.1   | Job Overrides for Global Keys    | Jobs can override global keys by specifying new values in the configuration file.                     | Fully implemented. |
| C3.2   | Unique Pipeline Names            | Ensure all pipelines have unique names within a repository.                                           | Fully implemented. |
| C4     | Custom Stages                    | Default stages (`build`, `test`, `doc`, `deploy`) are provided but can be overridden in config files. | Fully implemented. |
| C5.1   | Unique Job Names                 | Each job has a unique name within its stage, and empty stages throw errors.                           | Fully implemented. |
| C5.2   | Job Stage Assignment             | Jobs must belong to a defined stage in the configuration.                                             | Fully implemented. |
| C5.3   | Docker Image Definition          | Each job specifies a Docker image and can override global image definitions.                          | Fully implemented. |
| C5.4   | Commands Execution in Jobs       | Jobs can define one or more commands, executed serially, with pipeline execution stopping on failure. | Fully implemented. |
| C5.6   | Job Dependencies                 | Jobs can specify dependencies within the same pipeline file, and the system ensures no cycles exist.  | Fully implemented. |
| C5.7.2 | Default Artifact Upload Behavior | Artifacts are uploaded by default if the job succeeds.                                                | Fully implemented. |
| L1     | Configuration File Validation    | CLI checks the validity of the configuration file by default and reports errors.                      | Fully implemented. |
| L2     | Dry Run Option                   | CLI dry run provides execution order of stages and jobs.                                              | Fully implemented. |
| L3     | Error Reporting                  | CLI provides detailed error messages, including line and column numbers.                              | Fully implemented. |
| L4.1   | Summary of Past Pipeline Runs    | Display past pipeline runs for a repository, including status, timestamps, and other details.         | Fully implemented. |
| L4.2   | Pipeline Run Summary             | Retrieve detailed summaries of individual pipeline runs.                                              | Fully implemented. |
| L4.3   | Stage Summary                    | Retrieve stage summaries for a specific pipeline run.                                                 | Fully implemented. |
| L4.4   | Job Summary                      | Retrieve job summaries for a specific stage and pipeline run.                                         | Fully implemented. |

| L6 | Run Pipeline | CLI supports running pipelines with options for repo, branch, commit, and overrides. | Fully implemented. |
| L6.1 | Config File Key Overrides | CLI allows overrides for specific keys in the configuration file. | Fully implemented. |

---

## Partially Implemented Features

| Abbr.                       | Feature                | Implemented Work                                                                                       | Future Work Needed                                               |
| --------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| Initial set of Requirements | Job Parallel Run       | The validated pipeline configuration will store jobs for a stage in groups that can be run in parallel | Update pipeline run method to execute the job groups in parallel |
| C5.5                        | Job Allow Failure      | Allows marking jobs as "failed" but continues to the next job or stage.                                | Ensure remaining commands in failed jobs are executed.           |
| C5.7.1                      | Artifact Specification | Supports specifying files and folders for upload.                                                      | Specifying artifacts via regex patterns.                         |
| L5                          | Local Mode             | The users can supply the --local flag.                                                                 | Remote pipeline run is currently not fully support               |

---

## Extra Features Implemented

| Feature                                      | Description                                                                                                                  |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Validating yaml files in an entire directory | Users can validate all pipeline files in a directory by using `cid config --check-all` option                                |
| Check overrides without running              | Users can test the overrides applied to the pipeline configuration stored in the database using `cid config override` option |

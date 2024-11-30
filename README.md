# T4-CICD Project

This project is a CI/CD system designed to work on **Python**, **Java**, and **JavaScript** programs.

## About This README

This README is divided into two main sections:

1. **User Section**:

   - For those who want to use the application, this section provides setup instructions, requirements for external services, and basic usage commands.

2. **Developer Section**:
   - For contributors or developers working on this project, this section includes instructions for setting up the development environment, managing dependencies, running tests, and generating documentation.

# User Setup Instructions For Using The Application

The `t4-cicd` CLI application requires the following external services:

- MongoDB service
- Docker Engine service
- AWS S3 Service (user must use their own AWS account)

## Setting Up the Docker Engine Service

Install Docker Desktop from the [official website](https://www.docker.com/products/docker-desktop/). Docker Engine is included in the Docker Desktop installation.

On macOS or Windows:
Ensure Docker Desktop is open and running before using the `t4-cicd` CLI application.

On Linux:
Install Docker Engine directly via your package manager and ensure the Docker service (dockerd) is running.

The `t4-cicd` CLI uses the Docker Engine to perform its operations.

## Setting Up the MongoDB Service

You can use a local or remote MongoDB Service. You will need to save the URL to the MongoDB service
into a `.env` file in your project folder, or as an environment variable in your shell configuration file i.e., `~/.bashrc` or `~/.zshrc`.

The example below shows how to set up the `MONGO_DB_URL` for a local and remote MongoDB service.

```shell
# Local
export MONGO_DB_URL="mongodb://localhost:27017/"

# Remote, replace the <db_username>, <db_password> and <cluster_address>
export MONGO_DB_URL="mongodb+srv://<db_username>:<db_password>@<cluster_address>/"
```

Follow these instructions for setting up local MongoDB service.
Download the MongoDB Community Server from
https://www.mongodb.com/try/download/community-kubernetes-operator

Follow the instructions for self-managed deployments
https://www.mongodb.com/docs/manual/administration/install-community/

To view the database, use MongoDB Compass (comes together with MongoDB installation)

## Setting Up the AWS S3 Service

S3 bucket names must be globally unique across all AWS accounts. In order for `Upload Artifact` feature to work, user/developer needs to specify a unique name in their configuration file `artifact_upload_path: "<UNIQUE_BUCKET_NAME>"`.

```yml
global:
  pipeline_name: "cicd_pipeline"
  docker: #...
  artifact_upload_path: <UNIQUE_BUCKET_NAME>
```

You need to copy and paste the following AWS credentials into `~/.aws/credentials` file.
The credentials you provided must be able to create a bucket and upload into S3.

```shell
aws_access_key_id=<your_id>
aws_secret_access_key=<your_secret_access_key>
aws_session_token=<your_session_token> #if applicable
```

You also need to set up the target region in your `.env` file or set it as environment variable.

```shell
DEFAULT_S3_LOC=<AWS_REGION>
# example set to us-west-2
DEFAULT_S3_LOC='us-west-2'
```

## Installing the Program

You can install directly from PyPI using pip. It is recommended to install it under a virtual environment. See the section under Developer set up for how to activate a virtual environment.

```shell
pip install t4-cicd
```

## Basic usage

There are 2 options for running the application:

1. Run the command in a Git repository’s root directory to target that repository.
2. Run the command in an empty directory and specify the target repository, which can be either local or remote.

**Note**: The target repository must contain a `.cicd-pipelines` folder with a `pipelines.yml` file. These files will be used as the default configuration if not explicitly specified in the command.

Check [here](https://drive.google.com/file/d/1Mj3mnk20G5_Zj8X6bcFSnPRqY0stA-zu/view?usp=sharing) for the syntax required to write the YML file, check [here](https://drive.google.com/file/d/17vtjnLadMs-ItmI6e787_bvmH_j2YPVa/view?usp=sharing) for sample pipeline configuration.

The main commands of the CLI you can run are listed below. Use the --help flag for detailed information about each command.

```shell
# Checking pipeline configuration file,
# only work within a git repository
cid config

# Setting up repository
cid config set-repo

# Getting repository info
cid config get-repo

# Override pipeline configuration value in Datastore (MongoDB)
# only work within a git repository
cid config override

# Running a pipeline run
cid pipeline run

# Retrieve pipeline report
cid pipeline report
```

## Errors and Debug Information

- When errors occur, the program stdout and stderr will give a brief summary of the error message.

- For error details to help in debugging, you can look for the `debug.log` file created:
  - By default, a `debug.log` file will be created at the parent directory where the command was executed.
  - i.e., command is executed in directory `/temp/t4-cicd`, a `debug.log` will be at `/temp`

# Developer Setup Instructions

First, follow the [User Setup Instructions](#User-Setup-Instructions-For-Using-The-Application) to set the Docker Engine service, MongoDB service and AWS S3 service.

## Installation Instruction from Project GitHub Folder

Reference for Poetry and Click [here](https://medium.com/@chinsj/develop-and-deploy-cli-tool-on-python-with-poetry-and-click-ab62f4341c45)

## Prerequisites:

1. Installed Python 3.12 from official [website](https://www.python.org/downloads/)
2. Installed pipx and poetry

```shell
# Install pipx
python -m pip install --user pipx
python -m pipx ensurepath

# Then go to your environment variable on windows/OS, check the path added and
# update lowercase to uppercase if necessary
# restart your window/OS.

# Installation of poetry using pipx
pipx install poetry
```

3. Activated Virtual Environment

```shell
# Navigate to the project directory
# First create your virtual environment using venv,
# Give it a name like myenv, if you use other name, add it to the .gitignore file
# venv come with standard python package
python -m venv myenv

# Activate your virtual environment. For bash terminal
source <your_venv_dir>/Scripts/activate

# Example when you name venv as myenv
# For Windows
source myenv/Scripts/activate
# For Mac / Unix
source myenv/bin/activate
```

The alternative way to activate the virtual environment is to run `poetry shell`.
This is less recommended as the downside of this approach is any command not starting with poetry
will run using your background environment package instead from the virtual environment.

```sh
poetry shell
```

## Installation, Lint & Test

```shell
# This will install all dependencies, and the project itself into your venv
poetry install

# Run pylint for src directory, --fail-under score to be 9.5
poetry run pylint ./src --fail-under=9.5

# Run pytest with coverage, note current passing coverage score is set at 50%
poetry run pytest

# Run pydoctor to generate the API documentation. This will generate a folder name 'apidocs/'
# in the repository.
# This required Administrative right. To link the file
poetry run pydoctor

# To test if you can run the command
poetry run cid --help
# Or
cid --help
```

## Development - Managing Dependencies

[Reference](https://python-poetry.org/docs/managing-dependencies/#installing-group-dependencies) for dependencies management.

Please check the pyproject.toml file to ensure the dependency is added/removed

```shell
# Adding new dependency for general
poetry add <dependency/lib/package>

# Adding new dependency for development environment only
poetry add <dependency/lib/package> --group dev

# Remove dependencies
poetry remove <dependency/lib/package>
# Remove dependencies from development environment
poetry remove <dependency/lib/package> --group dev
```

## Development - Using Logging

### Steps:

- Use the `get_logger()` function from `util.common_utils`
- Provide arguments to change the logging level and/or directory
- By default, a `debug.log` file will be created at a parent directory where you run the command. You can change its location.
  i.e., if you run the command under directory `/temp/t4-cicd`, a `debug.log` will be at `/temp`

## Development Documentation:

Check out the list of documents under [dev-docs/design-docs](dev-docs/design-docs) folder for the following:

- CLI Documentation
- Component Design
- Configuration File Documentation
- Data Store Documentation
- System Design
- Testing Documentation

For API Documentations, you can look for the artifact generated by the last GitHub workflow action step, with name api-documentations.
The backup API Documentations are available in the following share location [here](https://drive.google.com/file/d/16LzQ7oikFJ35t3c1kQeRPyio3Ls2h4Jc/view?usp=sharing).
Look for index.html to start.

## Contributions

Please fork the repository, create a branch for your changes, and submit a pull request.

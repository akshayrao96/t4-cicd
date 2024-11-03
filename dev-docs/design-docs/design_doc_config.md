# Configuration File Syntax Requirements and Expected ConfigChecker return

[Reference](https://neu-seattle.gitlab.io/asd/cs6510f24/CS6510-F24/main/project/requirements.html#_requirements_iteration_2) for the requirements.

## General Need To Know

- The system is case sensitive. ie. 'Global' and 'global' are two different keywords.

  - Rationale: The system should pass all defined variables as it is to downstream processes (like docker, environment, display and storage) without modifying the case. Modifying case may cause unexpected behaviour for the user
  - Rationale2: This avoid making the parsing and validation process become too complicated.

- yaml parsing and validation is done in two stages

  - Stage 1 : the yaml is parsed using standard yaml parser library based on standard yaml syntax. Errors reported can be identified by the lines and columns in the yaml file where the first error occurs.
  - Stage 2 : the yaml content is further parsed checked by the ConfigChecker. Further error in parsing and checking the content can be identified by the key:values pair of the error

- Future improvement if required: to trace back error encountered in stage 2 to specific line and column in yml file

## Syntax Requirements

### The Global Section

References for

[Docker Image](https://docs.gitlab.com/ee/ci/docker/using_docker_images.html)

```yaml
# global keyword is required to identify the section for all global properties (Req #C3) at the top level.
global:
  # pipeline_name keyword is required to identify name of the pipeline
  # can be different from yaml file name
  # must be unique within this repo
  # used to identify the pipeline in the controller and for all
  # subsequent operations (Req #C3.1)
  pipeline_name: <chosen pipeline name>

  # Global Keys/Variables can be set here for all stages and jobs.(Req #C3.2)
  # Although these are optional, for certain keys if they are not defined here, they must be defined for each jobs

  # docker_registry - only dockerhub is currently supported out of the box, putting 'dockerhub' as the value will point to dockerhub.
  # If no value is specified , will use dockerhub as default
  # For other container registries, you need to supply the url prefix
  # like ghcr.io for github container
  docker:
    registry: <'dockerhub' or other registries url prefix>

    # docker_image, must be defined either here globally or for each individual jobs
    # image name must be in one of the following formats
    # image: <image-name> (Same as using <image-name> with the latest tag)
    # image: <image-name>:<tag>
    # Note the registry value must be specified using the docker_registry key, only namespace/image:tag are allowed as value in docker_image, namespace is optional if the image is from official (like ubuntu)
    image: <namespace>/<image>:<tag>

  # Repo path to use for artifact uploads into
  # If Job configurations optionally specify artifacts to upload (Req #C5.7)
  # Then the artifact_upload_path need to be specified either here globally or
  # for the job that will upload artifacts
  artifact_upload_path: <valid upload path>
```

### The stages section

```yaml
# stages definition (Req #C5.7) is optional. If not defined it will use the default stages name and order
# default stages: [build, test, doc, deploy]
# If there is a stages definition in the configuration file then the default is ignored and the CICD
# should only consider the stages and their order as defined in the configuration file.
# Stage names must be unique for a pipeline.
# each stage must have at least one or more jobs
# stages keyword is required at the top level to identify the section.
# stages order will be as listed under the stages keyword
stages:
  - <stage_name1>
  - <stage_name2>
```

### The jobs section

```yaml
# jobs keyword is required at the top level to identify the section.
# each job's name is identified by the key's value below the jobs keyword(Req #C5.1).
# job's name need to be unique within the pipeline and should be string that accepts UTF-8
# Example below
jobs:
    <job_name1>:
        <configs>:<config_values>
    <job_name2>:
        <configs>:<config_values>

# Further details for Job Configurations are as follow
jobs:
    <job_name1>:
        # stage name is required. a job can only be part of 1 stage (Req #C5.2)
        stage: <stage_name>

        # allow_failure flag allow override the default behavior and allow for the pipeline execution
        # to continue even if this job has failed.
        # available values: True or False(default option)
        allow_failure: True

        # Dependencies are specified in needs section (Req #C5.6). It can be
        # no dependency - when no key-value pair is included
        # only one dependency - can be specified as needs: [<job required>]
        # more than one dependencies - specified as below
        # cycle detection check will be performed (Req #C5.6.1)
        needs: [<job_required_1>, <job_required_2>]

        # override global keys (Req #C3.1, C5.3)such as docker_registry, docker_image, repo_path for uploads
        # Refer to the global section. If these values are not defined it will use global defaults
        # image name is required to be set at either here or global section.
        docker: <'dockerhub' or other registries url prefix>
            registry:
            image: <namespace(optional)>/<image>:<tag(optional)>
        artifact_upload_path: <valid upload path>

        # scripts keyword is used to identify the commands to run as part of a job
        # each job must have at least 1 command (Req #C5.6)
        # multiple commands will be run in the order specified
        scripts:
            - <command_1>
            - <command_2>

        # artifacts keyword is used to identify the configurations for artifact processing (Req #C5.7)
        # available config key-values pair are listed and explained below
        # the artifact will be uploaded to the artifact_upload_path defined when job completed
        artifacts:
            # on_success_only: attemp to upload the artifact(s) on success only,
            # available values are True/False, by default is True
            on_success_only: False

            # paths will specify the artifact file/directory to upload (Req #C5.7.1)
            # can be a file name like README.md
            # or a directory appended with / like build/
            # or simple regex like
            # Star for any match, e.g.
                # READ* matches all files that start with READ
                # *.java matches all files that end in .java.
                # The character . is not part of our regular expression language.
                # build/*/doc/ matches all directories named classes that are one directory away from build
                # e.g. build/java/doc, build/python/doc/ match, while build/java/reports/doc does not match
            # Double star for directories at any depth
                # build/**/doc/ matches all directories, regardless how deep, that contain a doc sub directory
            # all paths must start with - prefix
            paths:
                - <filename>
                - <path>

```

## Return from ConfigChecker validation

### High Level Dictionary Return

The ConfigChecker validation method will return a dictionary with the following key:value pairs at the top level.

```python
# Top-level of dictionary return
{
    #valid flag indicates if the validation passed or failed
    'valid':<True or False>,

    # If validation passed this will be an empty string
    'error_msg': <str of error messages collected>,

    # pipeline_config is the dictionary of the pipeline config processed.
    # if validation failed, it will be empty, else its content is explain below
    'pipeline_config': dict
}

# Top-level of pipeline_config dictionary
{
    # key-value pairs as extracted from the global section.
    # for docker_registry if not specified default option will be used
    'global': dict,

    # stages info as extracted and processed from the stages section. See next section
    'stages': list[dict],

    # jobs info as extracted and processed from the jobs section. See next section
    'jobs': dict
}
```

### Stages information

```python
# The values for the stages will be an OrderedDict
# Order of the dict represents the order in which the stages should be executed.
# in example below, stage 1 must be run before stage 2
# Each stage will have additional information available
'stages':OrderedDict([
    'stage1':{
        # job_graph is the adjacency list representation of the jobs dependencies
        # the key is the job_name other jobs depend on
        # the value is the list of jobs that required the key to completed
        # eg, job_a:[job_b, job_c] means job_b and job_c must wait for job_a to complete
        # this could be empty if no dependency specified
        'job_graph':{
            'job_1':['<required_by>'],
            # rest of dependencies
        },

        # job_groups specify a list of job_group that can be run parallel and independed of each other
        # ie, if we have two groups of job like [[job1], [job2]], job1 and job2 can be run in parallel
        # however within the same job group, the jobs are arranged in topological order and must be run
        # in order specified. ie [job2, job3] means job2 must be run before job3.
        # This guarantee when running job3, all requirements have been specified.
        'job_groups':[
            ['<job_1>'],
            ['<job_2>', '<job_3>'],
        ]
    },
    'stage2':{
        # ....
    }
])


```

### Jobs information

```python
# The dict for jobs will be a key=value pairs, where
# key=job_name, value=all configurations required to run the job
# If the job configuration is not specify in the yml file, the default values will be filled in .
# Example
'jobs':{
    '<job_name1>':{
        'stage': '<stage_name>',
        'allow_failure': <True or False(default)>,
        'needs': ['<job_required_1>', '<job_required_2>'], # set to empty list if not supplied
        'docker':
            'registry': "<'dockerhub' or other registries url prefix>",
            'image': '<namespace(optional)>/<image>:<tag(optional)>',
        'artifact_upload_path': '<valid upload path>', # set to empty string if not required
        'scripts': ['<command_1>', '<command_2>']
        'artifacts': {
            'on_success_only': <True(default) or False>,
            'paths': ['filename', 'path1']
        }
    },
    '<job_name2>':{
        #...
    }
}


```

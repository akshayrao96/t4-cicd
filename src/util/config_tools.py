""" config_tools module provide all class and method required to further 
validate and process the content of pipeline_configuration 
"""
import collections
from util.common_utils import (get_logger)

logger = get_logger("util.config_tools")

DEFAULT_DOCKER_REGISTRY = 'dockerhub'
DEFAULT_STAGES = ['build', 'test', 'doc', 'deploy']
DEFAULT_FLAG_JOB_ALLOW_FAIL = False
DEFAULT_FLAG_ARTIFACT_UPLOAD_ONSUCCESS = True
DEFAULT_STR = ""
DEFAULT_LIST = []
DEFAULT_DICT = {}

SECT_KEY_GLOBAL = 'global'
SECT_KEY_STAGES = 'stages'
SECT_KEY_JOBS = 'jobs'
SUBSECT_KEY_PIPE_NAME = 'pipeline_name'
SUBSECT_KEY_DOCKER_REG = 'docker_registry'
SUBSECT_KEY_DOCKER_IMG = 'docker_image'
SUBSECT_KEY_ARTIFACT_PATH = 'artifact_upload_path'
STAGE_SUBKEY_JOB_GRAPH = 'job_graph'
STAGE_SUBKEY_JOB_ORDER = 'job_groups'
JOB_SUBKEY_STAGE = 'stage'
JOB_SUBKEY_ALLOW = 'allow_failure'
JOB_SUBKEY_NEEDS = 'needs'
JOB_SUBKEY_SCRIPTS = 'scripts'
JOB_SUBKEY_ARTIFACT = 'artifacts'
ARTIFACT_SUBKEY_ONSUCCESS = 'on_success_only'
ARTIFACT_SUBKEY_PATH = 'paths'
RETURN_SECT_KEY_VALID = 'valid'
RETURN_SECT_KEY_ERR = 'error_msg'
RETURN_SECT_KEY_CONFIG = 'pipeline_config'
# pylint: disable=logging-fstring-interpolation
# pylint: disable=fixme
# pylint: disable=too-few-public-methods

class ConfigChecker:
    """ ConfigChecker class performing validation and processing for 
    pipeline configurations.
    """

    def __init__(self, pipeline_name: str = DEFAULT_STR, log_tool=logger) -> None:
        """ Default Constructor

        Args:
            pipeline_name (str, optional): pipeline_name to identify the config. 
                Can be changed later by validate_config method. Defaults to empty string. 
            log_tool (logging.Logger, optional): log tool to be used by this class. 
                Defaults to logger.
        """
        self.logger = log_tool
        self.pipeline_name = pipeline_name

    def validate_config(self, pipeline_name: str, pipeline_config: dict) -> dict:
        """ validate the pipeline configuration file. 

        Args:
            pipeline_name (str): pipeline_name to identify the config
            pipeline_config (dict): pipeline_configuration to be validated

        Returns:
            dict: dictionary of {
                    'valid':<True or False>, 
                    valid flag indicates if the validation passed or failed.\n 
                    'error_msg': <str of error messages collected>,
                    If validation passed this will be an empty string \n
                    'pipeline_config': dict. pipeline_config is the dictionary of 
                    the pipeline config processed. if validation failed, it will be empty
            }
        """
        self.pipeline_name = pipeline_name
        result_flag = True
        result_error_msg = ""
        processed_pipeline_config = {}
        # First check global section
        global_flag, global_error = self._check_global_section(
                pipeline_config,
                processed_pipeline_config
            )
        # Next check stages section
        stage_flag, stage_error = self._check_stages_section(
                pipeline_config,
                processed_pipeline_config
            )
        # Third check jobs section
        job_flag, job_error = self._check_jobs_section(
                pipeline_config,
                processed_pipeline_config
            )
        result_flag = global_flag and stage_flag and job_flag
        result_error_msg += global_error + stage_error + job_error
        return {
            RETURN_SECT_KEY_VALID:result_flag,
            RETURN_SECT_KEY_ERR: result_error_msg,
            RETURN_SECT_KEY_CONFIG: processed_pipeline_config if result_flag else {}
        }

    def _check_individual_config(self, sub_key: str,
                                 config_dict: dict,
                                 res_dict: dict,
                                 default_if_absent: any = None,
                                 expected_type: any = str,
                                 error_prefix: str = "") -> tuple[bool, str]:
        """ Helper method to check individual config

        Args:
            sub_key (str): subsection key to look for
            config_dict (dict): dictionary to check for 
            res_dict (dict): dictionary to store the result. will be modified in-place
            default_if_absent (any, optional): default value if the corresponding key not found, 
                if not supplied will report error when key not found. Defaults to None.
            expected_type (any, optional): expected type of corresponding value. Defaults to str.
            error_prefix (str, optional): prefix for error message for further identification. 
                Defaults to empty str
        Returns:
            tuple[bool, str]: First boolean indicates if the individual config check is successful
                              Second string return error message if any
        """
        result_flag = True
        result_error_msg = error_prefix
        if sub_key not in config_dict:
            if default_if_absent is None:
                result_flag = False
                result_error_msg += "key not found error for subkey:"
                result_error_msg += f"{sub_key}\n"
            else:
                if not isinstance(default_if_absent, expected_type):
                    result_flag = False
                    result_error_msg += "type error for default value"
                    result_error_msg += f"{default_if_absent}:"
                    result_error_msg += f"for key:{sub_key}."
                    result_error_msg += f"Expected type ={expected_type}\n"
                else:
                    res_dict[sub_key] = default_if_absent
        else:
            # try convert first
            try:
                res_dict[sub_key] = expected_type(config_dict[sub_key])
            except ValueError:
                result_flag = False
                result_error_msg += "type error for key:"
                result_error_msg += f"{sub_key}. Expected type ={expected_type}\n"
        return (result_flag, result_error_msg if not result_flag else "")

    def _check_global_section(self, pipeline_config: dict,
                              processed_config: dict) -> tuple[bool, str]:
        """ check global section for valid inputs according to the design doc

        Args:
            pipeline_config (dict): given pipeline_config
            processed_config (dict): processed pipeline config. Will be modified in-place

        Returns:
            tuple[bool, str]: first variable is a boolean indicator if the check passed, 
                second variable is the str of the error message combined. 
        """
        try:
            result_flag = True
            result_error_msg = ""
            processed_section = {}
            sec_key = SECT_KEY_GLOBAL
            if sec_key not in pipeline_config:
                return (False, f"No global section defined for pipeline {self.pipeline_name}")
            global_config = pipeline_config[sec_key]
            error_prefix = f"Error in section:{sec_key} "

            sub_key_list = [
                    SUBSECT_KEY_PIPE_NAME,
                    SUBSECT_KEY_DOCKER_REG,
                    SUBSECT_KEY_DOCKER_IMG,
                    SUBSECT_KEY_ARTIFACT_PATH,
                ]
            default_list = [
                None,
                DEFAULT_DOCKER_REGISTRY,
                DEFAULT_STR,
                DEFAULT_STR,
            ]
            # all expected_types are string
            for sub_key, default in zip(sub_key_list, default_list):
                flag, error = self._check_individual_config(
                        sub_key=sub_key,
                        config_dict=global_config,
                        res_dict=processed_section,
                        default_if_absent=default,
                        error_prefix=error_prefix
                    )
                result_flag = result_flag and flag
                result_error_msg += error

            # Prepare to return
            processed_config[sec_key] = processed_section
            return (result_flag, result_error_msg)
        except (LookupError, IndexError, KeyError)  as e:
            err_msg = f"Error in parsing pipeline_config global section for {self.pipeline_name},"
            err_msg += f"exception msg is {e}"
            self.logger.warning(err_msg)
            return (False, "Parsing global section, unexpected error occur")

    def _check_stages_section(self, pipeline_config: dict,
                              processed_config: dict) -> tuple[bool, str]:
        """ check stages section. validate the stages and jobs relationship are 
        valid as per design doc

        Args:
            pipeline_config (dict): given pipeline_config
            processed_config (dict): processed pipeline config. Will be modified in-place

        Returns:
            tuple[bool, str]: first variable is a boolean indicator if the check passed, 
            second variable is the str of the error message combined. 
        """
        try:
            result_flag = True
            result_error_msg = ""

            # First, check if there is stages defined. If no, used default stages
            sec_key = SECT_KEY_STAGES
            processed_section = {}
            flag, error = self._check_individual_config(
                    sec_key,
                    pipeline_config,
                    processed_section,
                    default_if_absent=DEFAULT_STAGES,
                    expected_type=list
                )
            result_flag = result_flag and flag
            result_error_msg += error
            # Second check, assign jobs to stages, validate each stages have at least one job
            # and each job are assigned to a valid stages
            stage_list = processed_section[sec_key]
            jobs_section = pipeline_config[SECT_KEY_JOBS]
            flag, error, processed_stages = self._check_stages_jobs_relationship(
                    stage_list,
                    jobs_section
                )
            result_flag = result_flag and flag
            result_error_msg += error
            # Third check, for each stage, verify the dependencies are correct
            for stage, job_list in processed_stages.items():
                flag, error, dependency_dict = self._check_jobs_dependencies(
                    stage, job_list, jobs_section)
                result_flag = result_flag and flag
                result_error_msg += error
                processed_stages[stage] = dependency_dict

            processed_config[sec_key] = processed_stages
            return (result_flag, result_error_msg)

        except (LookupError, IndexError, KeyError) as e:
            err_msg = f"Error in parsing pipeline_config stage section for {self.pipeline_name},"
            err_msg += f"exception msg is {e}"
            self.logger.warning(err_msg)
            return (False, "Parsing stage section, unexpected error occur")

    def _check_stages_jobs_relationship(
        self,
        stage_list: list[str],
        jobs_dict: dict
    )-> tuple[bool, str, collections.OrderedDict]:
        """ check the stages jobs relationship to ensure each stages have at least one job 
        and each job are assigned to a valid stages

        Args:
            stage_list (list[str]): list of stage name
            jobs_dict (dict): dictionary of jobs(key) and jobs config(value)

        Returns:
            tuple[bool, str, list[dict]]: tuple of three return value
            first indicate if the check passed or failed
            second is a list of error message
            third is the resulting list of stage dictionary of format 
            [
                {stage1}:{job sets},
                ...
                {stagen}:{job sets},
            ]
        """
        try:
            result_flag = True
            result_error_msg = ""
            stage2jobs = {stage: set() for stage in stage_list}
            for job, config in jobs_dict.items():
                if JOB_SUBKEY_STAGE not in config:
                    result_flag = False
                    result_error_msg += f"Error in section:jobs job:{job} No stage key defined\n"
                    continue
                job_stage = config[JOB_SUBKEY_STAGE]
                if job_stage not in stage_list:
                    result_flag = False
                    result_error_msg += f"Error in section:jobs job:{job} stage value {job_stage}"
                    result_error_msg += " defined does not exist in stages list\n"
                    continue
                stage2jobs[job_stage].add(job)
            # Check all stage has jobs
            for stage, job_list in stage2jobs.items():
                if len(job_list) == 0:
                    result_flag = False
                    result_error_msg += f"Error in section:stages stage:{stage} No job defined for this stage\n" # pylint: disable=line-too-long
            new_stage_jobs_list = collections.OrderedDict()
            for stage in stage_list:
                new_stage_jobs_list[stage]=stage2jobs[stage]
            if not result_flag:
                new_stage_jobs_list = collections.OrderedDict()
            return (result_flag, result_error_msg, new_stage_jobs_list)
        except (LookupError, IndexError, KeyError) as e:
            err_msg = f"Error in checking stages jobs relationship for {self.pipeline_name},"
            err_msg += f"exception msg is {e}"
            self.logger.warning(err_msg)
            return (False, "checking stages jobs relationship, unexpected error occur\n", {})

    def _check_jobs_dependencies(self, stage_name:str,
                                 job_list: list|set,
                                 jobs_dict: dict) -> tuple[bool, str, dict]:
        """ check dependencies for the jobs within the same stage. 
            no jobs should depends on jobs not defined in current stage
            no cycle allowed for the group of jobs

        Args:
            stage_name:str name of the stage checking on 
            job_list (list | set): iterable of jobs within same stage
            jobs_dict (dict): dictionary of jobs(key) and jobs config(value)

        Returns:
            tuple[bool, str, dict]: tuple of three return value
            first indicate if the check passed or failed
            second is a list of error message
            third is the resulting job dependency of format 
            {
                # job_graph is the adjancy list representation of the graph
                'job_graph':{
                    'job_1':['<required_by>'],
                    # rest of dependencies
                },
                # job_group is the topological sorted list of job
                'job_groups':[
                    ['<job_1>'],
                    ['<job_2>', '<job_3>'],
                ]
            }
        """
        try:
            result_flag = True
            result_error_msg = ""
            result_dict = {}
            adjacency_list = {job:[] for job in job_list}
            need_key = JOB_SUBKEY_NEEDS
            for job in job_list:
                if job not in jobs_dict:
                    result_flag = False
                    result_error_msg += f"Error in stage:{stage_name}-Job not found in jobs_dict error for job:{job}\n" # pylint: disable=line-too-long
                    continue
                job_config = jobs_dict[job]
                if need_key not in job_config:
                    continue
                job_needs = job_config[need_key]
                if not isinstance(job_needs, list):
                    result_flag = False
                    result_error_msg += f"Error in stage:{stage_name}-Job needs not in list format"
                    result_error_msg += f" for job:{job} and needs:{job_needs}\n"
                    continue
                for need in job_needs:
                    if need == job:
                        result_flag = False
                        result_error_msg += f"Error in stage:{stage_name}-Self cycle error detected for job {job}" # pylint: disable=line-too-long
                        continue
                    if need not in adjacency_list:
                        result_flag = False
                        result_error_msg += f"Error in stage:{stage_name}-Job:{job} depends on "
                        result_error_msg += f"job:{need} outside of this stage\n"
                        continue
                    adjacency_list[need].append(job)
            if result_flag:
                flag, error_msg, order = self._topo_sort(stage_name, adjacency_list)
                result_flag = result_flag and flag
                result_error_msg += error_msg
            if result_flag:
                result_dict[STAGE_SUBKEY_JOB_GRAPH] = adjacency_list
                # TODO - update here after update the toposort method to separate group of orders
                result_dict[STAGE_SUBKEY_JOB_ORDER] = [order]
            return (result_flag, result_error_msg, result_dict)
        except (LookupError, IndexError, KeyError) as e:
            err_msg = f"stage:{stage_name}-Error in checking jobs dependency for "
            err_msg += f"{self.pipeline_name} and job_list {job_list}, exception msg is {e}"
            self.logger.warning(err_msg)
            return (
                    False,
                    f"stage:{stage_name}-checking jobs dependency for job_list{job_list}, unexpected error occur\n", # pylint: disable=line-too-long
                    {}
                )

    # TODO - Update to separate groups of jobs that can be executed independently
    def _topo_sort(
            self,
            stage_name:str,
            adjacency_list:dict,
            entire_list:list=None
        )->tuple[bool, str, list]:
        """ performed topological sort based on the nodes in adjacency_list and entire_list

        Args:
            stage_name:str name of the stage checking on 
            adjacency_list (dict): graph representation of given nodes
            entire_list (list, optional): List of all nodes to be sorted, 
                if provided will use this. Defaults to None.

        Returns:
            tuple[bool, str, list]: tuple of three return value
            first indicate if the sort passed or failed
            second is a list of error message
            third is resulted sorted list
        """
        result_flag = True
        result_error_msg = ""
        node2depend_cnt = collections.defaultdict(int)
        # initialize the node2depend_cnt dict if entire_list is supplied
        if entire_list is not None:
            for node in entire_list:
                node2depend_cnt[node] = 0

        # fill the depend_cnt based on adjacency list graph
        # recall for each key value pairs in adjacency list
        # the key is required by the value, key need to finish first
        for node, required_by in adjacency_list.items():
            if node not in node2depend_cnt:
                node2depend_cnt[node] = 0
            # Then for each value in required_by, we add the depend_cnt by 1
            for req in required_by:
                node2depend_cnt[req] += 1

        order = []
        queue = collections.deque()
        visited = set()
        for node, depend_cnt in node2depend_cnt.items():
            # depend_cnt == 0 means this node is not waiting on other node
            # and can be scheduled to start
            if depend_cnt == 0:
                queue.append(node)
                order.append(node)
                visited.add(node)
        # clean up
        for node in visited:
            node2depend_cnt.pop(node)

        # bfs
        self.logger.debug(queue)
        while queue:
            curr = queue.popleft()
            if curr not in adjacency_list:
                continue
            for required_by in adjacency_list[curr]:
                if required_by in visited:
                    continue
                node2depend_cnt[required_by] -= 1
                if node2depend_cnt[required_by] == 0:
                    queue.append(required_by)
                    order.append(required_by)
                    visited.add(required_by)
                    node2depend_cnt.pop(required_by)

        # check result
        self.logger.debug(node2depend_cnt)
        if len(node2depend_cnt) != 0:
            result_flag = False
            result_error_msg = f"stage:{stage_name}-Cycle error detected for jobs:{list(node2depend_cnt.keys())}\n" # pylint: disable=line-too-long
            return (result_flag, result_error_msg, [])
        return (result_flag, result_error_msg, order)


    def _check_jobs_section(self, pipeline_config: dict,
                            processed_config: dict) -> tuple[bool, str]:
        """ check jobs section, validate and filled the required field for each job

        Args:
            pipeline_config (dict): given pipeline_config
            processed_config (dict): processed pipeline config. Will be modified in-place

        Returns:
            tuple[bool, str]: first variable is a boolean indicator if the check passed, 
            second variable is the str of the error message combined. 
        """
        try:
            result_flag = True
            result_error_msg = ""
            sec_key = SECT_KEY_JOBS
            processed_section = {}
            if sec_key not in pipeline_config:
                return (False, f"No global section defined for pipeline {self.pipeline_name}")
            job_configs = pipeline_config[sec_key]
            error_prefix = f"Error in section:{sec_key} "
            # All global values should be available in processed config when called
            # as prepared by previous section
            global_docker_reg = processed_config[SECT_KEY_GLOBAL][SUBSECT_KEY_DOCKER_REG]
            global_docker_img = processed_config[SECT_KEY_GLOBAL][SUBSECT_KEY_DOCKER_IMG]
            global_upload_path = processed_config[SECT_KEY_GLOBAL][SUBSECT_KEY_ARTIFACT_PATH]
            self.logger.debug(job_configs)
            for job, config in job_configs.items():
                job_error_prefix = error_prefix + f"job:{job} "
                processed_job = {}
                # top level key-values pair
                sub_key_list = [
                    JOB_SUBKEY_STAGE,
                    JOB_SUBKEY_ALLOW,
                    JOB_SUBKEY_NEEDS,
                    SUBSECT_KEY_DOCKER_REG,
                    SUBSECT_KEY_DOCKER_IMG,
                    SUBSECT_KEY_ARTIFACT_PATH,
                    JOB_SUBKEY_SCRIPTS,
                ]
                default_list = [
                    None,
                    DEFAULT_FLAG_JOB_ALLOW_FAIL,
                    DEFAULT_LIST,
                    global_docker_reg if global_docker_reg != "" else None,
                    global_docker_img if global_docker_img != "" else None,
                    global_upload_path,
                    None
                ]
                expected_type = [
                    str,
                    bool,
                    list,
                    str,
                    str,
                    str,
                    list,
                ]     
                for sub_key, default, etype in zip(sub_key_list, default_list, expected_type):        
                    flag, error = self._check_individual_config(
                        sub_key=sub_key,
                        config_dict=config,
                        res_dict=processed_job,
                        default_if_absent=default,
                        expected_type=etype,
                        error_prefix=job_error_prefix
                    )
                    result_flag = result_flag and flag
                    result_error_msg += error
                # Check artifacts
                if JOB_SUBKEY_ARTIFACT in config:
                    if processed_job[SUBSECT_KEY_ARTIFACT_PATH] == DEFAULT_STR:
                        result_flag = False
                        result_error_msg += job_error_prefix + "no artifact upload path defined\n"
                    artifact_dict = config[JOB_SUBKEY_ARTIFACT]
                    artifact_config = {}
                    # Check flag upload on success
                    flag, error = self._check_individual_config(
                        sub_key=ARTIFACT_SUBKEY_ONSUCCESS,
                        config_dict=artifact_dict,
                        res_dict=artifact_config,
                        default_if_absent=DEFAULT_FLAG_ARTIFACT_UPLOAD_ONSUCCESS,
                        expected_type=bool,
                        error_prefix=job_error_prefix
                    )
                    result_flag = result_flag and flag
                    result_error_msg += error
                    # Check flag required path
                    flag, error = self._check_individual_config(
                        sub_key=ARTIFACT_SUBKEY_PATH,
                        config_dict=artifact_dict,
                        res_dict=artifact_config,
                        expected_type=list,
                        error_prefix=job_error_prefix
                    )
                    result_flag = result_flag and flag
                    result_error_msg += error
                    processed_job[JOB_SUBKEY_ARTIFACT] = artifact_config
                # Update processed job info
                processed_section[job] = processed_job
            if result_flag:
                processed_config[sec_key] = processed_section
            else:
                processed_config[sec_key] = {}
            self.logger.debug(result_error_msg)
            return (result_flag, result_error_msg)
        except (LookupError, IndexError, KeyError) as e:
            self.logger.warning(f"Error in parsing job sections, exception msg is {e}\n"
                                )
            return (False, "Parsing jobs section, unexpected error occur")

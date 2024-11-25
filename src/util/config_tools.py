""" config_tools module provide all class and method required to further 
validate and process the content of pipeline_configuration 
"""
import collections
import util.constant as c
from util.model import (ValidationResult)
from util.common_utils import (get_logger, UnionFind, TopoSort)

logger = get_logger("util.config_tools")

# pylint: disable=logging-fstring-interpolation
# pylint: disable=too-few-public-methods

class ConfigChecker:
    """ ConfigChecker class performing validation and processing for 
    pipeline configurations.
    """

    def __init__(self, pipeline_name: str = c.DEFAULT_STR, file_name: str = c.DEFAULT_STR,
                 log_tool=logger) -> None:
        """ Default Constructor

        Args:
            pipeline_name (str, optional): pipeline_name to identify the config. 
                Can be changed later by validate_config method. Defaults to empty string. 
            file_name (str, optional): file_name to where the config is loaded from. 
                Can be changed later by validate_config method. Defaults to empty string. 
            log_tool (logging.Logger, optional): log tool to be used by this class. 
                Defaults to logger.
        """
        self.logger = log_tool
        self.pipeline_name = pipeline_name
        self.file_name = file_name

    def validate_config(self,
                        pipeline_name: str,
                        pipeline_config: dict,
                        file_name: str = c.DEFAULT_STR,
                        error_lc: bool = False
                        ) -> ValidationResult:
        """ validate the pipeline configuration file. 

        Args:
            pipeline_name (str): pipeline_name to identify the config
            pipeline_config (dict): pipeline_configuration to be validated
            file_name (str, optional): file_name to where the config is loaded from.
                Defaults to empty string. 
            error_lc (bool, optional): boolean flag indicate if lines and columns
                information available for error tracking, Defaults to False
        Returns:
            ValidationResult: see corresponding model for information hold
        """
        self.pipeline_name = pipeline_name
        self.file_name = file_name
        result_flag = True
        result_error_msg = ""
        processed_pipeline_config = {}
        # First check global section
        global_flag, global_error = self._check_global_section(
                pipeline_config,
                processed_pipeline_config,
                error_lc
            )
        # Next check stages section
        stage_flag, stage_error = self._check_stages_section(
                pipeline_config,
                processed_pipeline_config,
                error_lc
            )
        # Third check jobs section
        job_flag, job_error = self._check_jobs_section(
                pipeline_config,
                processed_pipeline_config,
                error_lc
            )
        result_flag = global_flag and stage_flag and job_flag
        result_error_msg += global_error + stage_error + job_error

        validation_res = ValidationResult(
                valid=result_flag,
                error_msg=result_error_msg,
                pipeline_config=processed_pipeline_config if result_flag else {}
            )
        return validation_res

    def _check_individual_config(self, sub_key: str,
                                 config_dict: dict,
                                 res_dict: dict,
                                 default_if_absent: any = None,
                                 expected_type: any = str,
                                 error_prefix: str = c.DEFAULT_STR,
                                 error_lc: bool = False) -> tuple[bool, str]:
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
            error_lc (bool, optional): boolean flag indicate if lines and columns
                information available for error tracking, Defaults to False
        Returns:
            tuple[bool, str]: First boolean indicates if the individual config check is successful
                              Second string return error message if any
        """
        result_flag = True
        result_error_msg = error_prefix
        if sub_key not in config_dict:
            err_msg = ""
            if error_lc and hasattr(config_dict, 'lc'):
                err_msg = f"{self.file_name}:{config_dict.lc.line}:{config_dict.lc.col} "
            if default_if_absent is None:
                result_flag = False
                result_error_msg = err_msg + result_error_msg
                result_error_msg += "key not found error for subkey:"
                result_error_msg += f"{sub_key}\n"
            else:
                if not isinstance(default_if_absent, expected_type):
                    result_flag = False
                    result_error_msg = err_msg + result_error_msg
                    result_error_msg += "type error for default value"
                    result_error_msg += f"{default_if_absent}:"
                    result_error_msg += f"for key:{sub_key}."
                    result_error_msg += f"Expected type ={expected_type}\n"
                else:
                    res_dict[sub_key] = default_if_absent
        else:
            # try convert first
            try:
                element = config_dict[sub_key]
                res_dict[sub_key] = expected_type(element)
            except ValueError:
                result_flag = False
                if error_lc:
                    if element is not None and hasattr(element, 'lc'):
                        result_error_msg = f"{self.file_name}:{element.lc.line}:{element.lc.col} "
                    else:
                        result_error_msg = f"{self.file_name}:{config_dict.lc.line}:{config_dict.lc.col} "  # pylint: disable=line-too-long
                    result_error_msg += f"pipeline:{self.pipeline_name}"
                result_error_msg += "type error for key:"
                result_error_msg += f"{sub_key}. Expected type ={expected_type}\n"
        return (result_flag, result_error_msg if not result_flag else "")

    def _check_global_section(self, pipeline_config: dict,
                              processed_config: dict,
                              error_lc: bool = False) -> tuple[bool, str]:
        """ check global section for valid inputs according to the design doc

        Args:
            pipeline_config (dict): given pipeline_config
            processed_config (dict): processed pipeline config. Will be modified in-place
            error_lc (bool, optional): boolean flag indicate if lines and columns
                information available for error tracking, Defaults to False
        Returns:
            tuple[bool, str]: first variable is a boolean indicator if the check passed, 
                second variable is the str of the error message combined. 
        """
        try:
            result_flag = True
            result_error_msg = ""
            processed_section = {}
            sec_key = c.KEY_GLOBAL
            if sec_key not in pipeline_config:
                return (False, f"No global section defined for pipeline {self.pipeline_name} in file {self.file_name}\n") # pylint: disable=line-too-long
            global_config = pipeline_config[sec_key]
            error_prefix = f"Pipeline:{self.pipeline_name} from file:{self.file_name}. "
            error_prefix += f"Error in section:{sec_key} "
            # Check pipeline name & artifact upload path
            sub_key_list = [
                    c.KEY_PIPE_NAME,
                    c.KEY_ARTIFACT_PATH,
                ]
            default_list = [
                None,
                c.DEFAULT_STR,
            ]
            # all expected_types are string
            for sub_key, default in zip(sub_key_list, default_list):
                flag, error = self._check_individual_config(
                        sub_key=sub_key,
                        config_dict=global_config,
                        res_dict=processed_section,
                        default_if_absent=default,
                        error_prefix=error_prefix,
                        error_lc=error_lc
                    )
                result_flag = result_flag and flag
                result_error_msg += error

            # Check docker section
            docker_config = {}
            if c.KEY_DOCKER in global_config:
                docker_config = global_config[c.KEY_DOCKER]
            processed_section[c.KEY_DOCKER] = {}
            sub_key_list = [c.KEY_DOCKER_REG, c.KEY_DOCKER_IMG]
            default_list = [c.DEFAULT_DOCKER_REGISTRY, c.DEFAULT_STR]
            # all expected_types are string
            for sub_key, default in zip(sub_key_list, default_list):
                flag, error = self._check_individual_config(
                            sub_key=sub_key,
                            config_dict=docker_config,
                            res_dict=processed_section[c.KEY_DOCKER],
                            default_if_absent=default,
                            error_prefix=error_prefix,
                            error_lc=error_lc
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
                              processed_config: dict,
                              error_lc: bool = False) -> tuple[bool, str]:
        """ check stages section. validate the stages and jobs relationship are 
        valid as per design doc

        Args:
            pipeline_config (dict): given pipeline_config
            processed_config (dict): processed pipeline config. Will be modified in-place
            error_lc (bool, optional): boolean flag indicate if lines and columns
                information available for error tracking, Defaults to False
        Returns:
            tuple[bool, str]: first variable is a boolean indicator if the check passed, 
            second variable is the str of the error message combined. 
        """
        try:
            result_flag = True
            result_error_msg = ""

            # First, check if there is stages defined. If no, used default stages
            processed_section = {}
            flag, error = self._check_individual_config(
                    c.KEY_STAGES,
                    pipeline_config,
                    processed_section,
                    default_if_absent=c.DEFAULT_STAGES,
                    expected_type=list,
                    error_lc=error_lc
                )
            result_flag = result_flag and flag
            result_error_msg += error

            # Check for duplicate stage name
            if result_flag and c.KEY_STAGES in pipeline_config:
                stage_set = set()
                for stage in pipeline_config[c.KEY_STAGES]:
                    if stage in stage_set:
                        err_msg = ""
                        if error_lc and hasattr(pipeline_config[c.KEY_STAGES], 'lc'):
                            e = pipeline_config[c.KEY_STAGES]
                            err_msg = f"{self.file_name}:{e.lc.line}:{e.lc.col} "
                        err_msg += "Duplicate Key Error for stage in stages list\n"
                        result_flag = False
                        result_error_msg += err_msg

            # Next check, assign jobs to stages, validate each stages have at least one job
            # and each job are assigned to a valid stages
            stage_list = processed_section[c.KEY_STAGES]
            jobs_section = pipeline_config[c.KEY_JOBS]
            flag, error, processed_stages = self._check_stages_jobs_relationship(
                    stage_list,
                    jobs_section,
                    error_lc
                )
            result_flag = result_flag and flag
            result_error_msg += error

            # Next check, for each stage, verify the dependencies are correct
            for stage, job_list in processed_stages.items():
                flag, error, dependency_dict = self._check_jobs_dependencies(
                    stage, job_list, jobs_section, error_lc)
                result_flag = result_flag and flag
                result_error_msg += error
                processed_stages[stage] = dependency_dict

            processed_config[c.KEY_STAGES] = processed_stages
            return (result_flag, result_error_msg)

        except (LookupError, IndexError, KeyError) as e:
            err_msg = f"Error in parsing pipeline_config stage section for {self.pipeline_name},"
            err_msg += f"exception msg is {e}"
            self.logger.warning(err_msg)
            return (False, "Parsing stage section, unexpected error occur")

    def _check_stages_jobs_relationship(
        self,
        stage_list: list[str],
        jobs_dict: dict,
        error_lc: bool = False
    )-> tuple[bool, str, collections.OrderedDict]:
        """ check the stages jobs relationship to ensure each stages have at least one job 
        and each job are assigned to a valid stages

        Args:
            stage_list (list[str]): list of stage name
            jobs_dict (dict): dictionary of jobs(key) and jobs config(value), 
                will have lc property if passed directly from yaml
            error_lc (bool, optional): boolean flag indicate if lines and columns
                information available for error tracking, Defaults to False

        Returns:
            tuple[bool, str, list[dict]]: tuple of three return value
            first indicate if the check passed or failed
            second is a list of error message
            third is the resulting list of stage dictionary of format 
            [{stage1}:{job sets},... {stagen}:{job sets},]
        """
        try:
            result_flag = True
            result_error_msg = ""
            stage2jobs = {stage: set() for stage in stage_list}
            for job, config in jobs_dict.items():
                if c.JOB_SUBKEY_STAGE not in config:
                    result_flag = False
                    err = ""
                    if error_lc:
                        err = f"{self.file_name}:{config.lc.line}:{config.lc.col} "
                    err += f"Error in section:jobs job:{job} No stage key defined\n"
                    result_error_msg += err
                    continue
                job_stage = config[c.JOB_SUBKEY_STAGE]
                if job_stage not in stage_list:
                    result_flag = False
                    err = ""
                    if error_lc and hasattr(job_stage, 'lc'):
                        err = f"{self.file_name}:{job_stage.lc.line}:{job_stage.lc.col} "
                    err += f"Error in section:jobs job:{job} stage value {job_stage}"
                    err += " defined does not exist in stages list\n"
                    result_error_msg += err
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
                                 jobs_dict: dict,
                                 error_lc: bool = False) -> tuple[bool, str, dict]:
        """ check dependencies for the jobs within the same stage. 
            no jobs should depends on jobs not defined in current stage
            no cycle allowed for the group of jobs

        Args:
            stage_name:str name of the stage checking on 
            job_list (list | set): iterable of jobs within same stage
            jobs_dict (dict): dictionary of jobs(key) and jobs config(value)
                will have lc property if passed directly from yaml
            error_lc (bool, optional): boolean flag indicate if lines and columns
                information available for error tracking, Defaults to False

        Returns:
            tuple[bool, str, dict]: tuple of three return value
            first indicate if the check passed or failed
            second is a list of error message
            third is the resulting job dependency 

        """
        try:
            result_flag = True
            result_error_msg = ""
            result_dict = {}
            adjacency_list = {job:[] for job in job_list}
            need_key = c.JOB_SUBKEY_NEEDS
            for job in job_list:
                if job not in jobs_dict:
                    result_flag = False
                    result_error_msg += f"Error in stage:{stage_name}-Job not found in jobs_dict error for job:{job}\n" # pylint: disable=line-too-long
                    continue
                job_config = jobs_dict[job]
                if need_key not in job_config:
                    continue
                job_needs = job_config[need_key]
                # Check if job_needs is in list
                if not isinstance(job_needs, list):
                    result_flag = False
                    err = ""
                    if error_lc and hasattr(job_needs, 'lc'):
                        err = f"{self.file_name}:{job_needs.lc.line}:{job_needs.lc.col} "
                    err += f"Error in stage:{stage_name}-Job needs not in list format"
                    err += f" for job:{job} and needs:{job_needs}\n"
                    result_error_msg += err
                    continue
                # Check for self pointing
                for need in job_needs:
                    if need == job:
                        result_flag = False
                        err = ""
                        if error_lc and hasattr(job_needs, 'lc'):
                            err = f"{self.file_name}:{job_needs.lc.line}:{job_needs.lc.col} "
                        err += f"Error in stage:{stage_name}-Self cycle error detected for job {job}" # pylint: disable=line-too-long
                        result_error_msg += err
                        continue
                    if need not in adjacency_list:
                        result_flag = False
                        err = ""
                        if error_lc and hasattr(job_needs, 'lc'):
                            err = f"{self.file_name}:{job_needs.lc.line}:{job_needs.lc.col} "
                        err += f"Error in stage:{stage_name}-Job:{job} depends on "
                        err += f"job:{need} outside of this stage\n"
                        result_error_msg += err
                        continue
                    adjacency_list[need].append(job)
            if result_flag:
                flag, error_msg, group_orders = self._group_n_sort(stage_name,
                                                                   adjacency_list,
                                                                   job_list)
                result_flag = result_flag and flag
                result_error_msg += error_msg
            if result_flag:
                result_dict[c.KEY_JOB_GRAPH] = adjacency_list
                result_dict[c.KEY_JOB_ORDER] = group_orders
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

    def _group_n_sort(
            self,
            stage_name:str,
            adjacency_list:dict,
            entire_list:list=[]
        )->tuple[bool, str, list]:
        """ performed topological sort based on the nodes in adjacency_list and entire_list

        Args:
            stage_name:str name of the stage checking on 
            adjacency_list (dict): graph representation of given nodes
            entire_list (list, optional): List of all nodes to be sorted, 
                if provided will use this. Defaults to empty list.

        Returns:
            tuple[bool, str, list]: tuple of three return value
            first indicate if the sort passed or failed
            second is a list of error message
            third is resulted sorted list
        """
        result_flag = True
        result_error_msg = ""

        # First do the grouping using UnionFind()
        uf = UnionFind()
        for node in entire_list:
            uf.insert(node)

        # recall for each key value pairs in adjacency list
        # the key is required by the value, key need to finish first
        for node, required_by in adjacency_list.items():
            for req in required_by:
                uf.add_edge(node, req)

        job_groups = uf.get_separated_groups()
        group_orders = []
        topo_sorter = TopoSort(adjacency_list)
        for group in job_groups:
            no_cycle, error , order = topo_sorter.get_topo_order(group)
            result_flag = result_flag and no_cycle
            if not no_cycle:
                result_error_msg += f"stage:{stage_name} " + error
            else:
                group_orders.append(order)
        return (result_flag, result_error_msg, group_orders)

    def _check_jobs_section(self, pipeline_config: dict,
                            processed_config: dict,
                            error_lc: bool = False) -> tuple[bool, str]:
        """ check jobs section, validate and filled the required field for each job

        Args:
            pipeline_config (dict): given pipeline_config
            processed_config (dict): processed pipeline config. Will be modified in-place
            error_lc (bool, optional): boolean flag indicate if lines and columns
                information available for error tracking, Defaults to False

        Returns:
            tuple[bool, str]: first variable is a boolean indicator if the check passed, 
            second variable is the str of the error message combined. 
        """
        try:
            result_flag = True
            result_error_msg = ""
            sec_key = c.KEY_JOBS
            processed_section = {}
            if sec_key not in pipeline_config:
                return (False, f"No {sec_key} section defined for pipeline {self.pipeline_name}")
            job_configs = pipeline_config[sec_key]
            error_prefix = f"{sec_key}:"
            # All global values should be available in processed config when called
            # as prepared by previous section
            global_docker_reg = processed_config[c.KEY_GLOBAL][c.KEY_DOCKER][c.KEY_DOCKER_REG]
            global_docker_img = processed_config[c.KEY_GLOBAL][c.KEY_DOCKER][c.KEY_DOCKER_IMG]
            global_upload_path = processed_config[c.KEY_GLOBAL][c.KEY_ARTIFACT_PATH]
            for job, config in job_configs.items():
                job_error_prefix = error_prefix + f"{job} "
                # if error_lc and hasattr(config, 'lc'):
                #     job_error_prefix = f"{self.file_name}:{config.lc.line}:{config.lc.col} "
                processed_job = {}
                # top level key-values pair
                sub_key_list = [
                    c.JOB_SUBKEY_STAGE,
                    c.JOB_SUBKEY_ALLOW,
                    c.JOB_SUBKEY_NEEDS,
                    c.KEY_ARTIFACT_PATH,
                    c.JOB_SUBKEY_SCRIPTS,
                ]
                default_list = [
                    None,
                    c.DEFAULT_FLAG_JOB_ALLOW_FAIL,
                    c.DEFAULT_LIST,
                    global_upload_path,
                    None
                ]
                expected_type = [
                    str,
                    bool,
                    list,
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
                        error_prefix=job_error_prefix,
                        error_lc=error_lc
                    )
                    result_flag = result_flag and flag
                    result_error_msg += error
                # Check docker section
                docker_config = {}
                if c.KEY_DOCKER in config:
                    docker_config = config[c.KEY_DOCKER]
                processed_job[c.KEY_DOCKER] = {}
                sub_key_list = [c.KEY_DOCKER_REG, c.KEY_DOCKER_IMG]
                default_list = [
                    global_docker_reg if global_docker_reg != "" else None,
                    global_docker_img if global_docker_img != "" else None,
                ]
                # all expected_types are string
                for sub_key, default in zip(sub_key_list, default_list):
                    flag, error = self._check_individual_config(
                                sub_key=sub_key,
                                config_dict=docker_config,
                                res_dict=processed_job[c.KEY_DOCKER],
                                default_if_absent=default,
                                error_prefix=job_error_prefix,
                                error_lc=error_lc
                            )
                    result_flag = result_flag and flag
                    result_error_msg += error

                # Check artifacts
                if c.JOB_SUBKEY_ARTIFACT in config:
                    if processed_job[c.KEY_ARTIFACT_PATH] == c.DEFAULT_STR:
                        result_flag = False
                        element = config[c.JOB_SUBKEY_ARTIFACT]
                        err = ""
                        if error_lc and hasattr(element, 'lc'):
                            err = f"{self.file_name}:{element.lc.line}:{element.lc.col} "
                        err += job_error_prefix + "no artifact upload path defined\n"
                        result_error_msg += err
                    artifact_dict = config[c.JOB_SUBKEY_ARTIFACT]
                    artifact_config = {}
                    # Check flag upload on success
                    flag, error = self._check_individual_config(
                        sub_key=c.ARTIFACT_SUBKEY_ONSUCCESS,
                        config_dict=artifact_dict,
                        res_dict=artifact_config,
                        default_if_absent=c.DEFAULT_FLAG_ARTIFACT_UPLOAD_ONSUCCESS,
                        expected_type=bool,
                        error_prefix=job_error_prefix,
                        error_lc=error_lc
                    )
                    result_flag = result_flag and flag
                    result_error_msg += error
                    # Check flag required path
                    flag, error = self._check_individual_config(
                        sub_key=c.ARTIFACT_SUBKEY_PATH,
                        config_dict=artifact_dict,
                        res_dict=artifact_config,
                        expected_type=list,
                        error_prefix=job_error_prefix,
                        error_lc=error_lc
                    )
                    result_flag = result_flag and flag
                    result_error_msg += error
                    processed_job[c.JOB_SUBKEY_ARTIFACT] = artifact_config
                # Update processed job info
                processed_section[job] = processed_job
            if result_flag:
                processed_config[sec_key] = processed_section
            else:
                processed_config[sec_key] = {}
            return (result_flag, result_error_msg)
        except (LookupError, IndexError, KeyError) as e:
            self.logger.warning(f"Error in parsing job sections, exception msg is {e}\n"
                                )
            return (False, "Parsing jobs section, unexpected error occur")

""" 
Provide the common utility functions used by all other modules
"""
import os
import re
import collections
import logging
import yaml
from dotenv import dotenv_values


def get_logger(logger_name='', log_level=logging.DEBUG, log_file='../debug.log') -> logging.Logger:
    """_summary_

    Args:
        logger_name (str, optional): _description_. Defaults to ''.
        log_level (_type_, optional): _description_. Defaults to logging.DEBUG.
        log_file (str, optional): _description_. Defaults to 'debug.log'.

    Returns:
        logging.Logger: _description_
    """
    # Retrieve logger and set log level
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    # create console handler and set level to Warning
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)

    # create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    # add file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)

    return logger


def get_env() -> dict:
    """Retrieve the env variables from the environment and .env file. Perform further processing if necessary.

    Returns:
        dict: dictionary of env values in key=value pairs
    """
    file_config = dotenv_values(".env")
    env_config = {key: os.getenv(key) for key in os.environ.keys()}
    # Merge dictionaries, .env file takes priority
    config = {**env_config, **file_config}

    return config

class UnionFind:
    """ UnionFind Class to Find Separated Group of Related Nodes(jobs)
    """
    def __init__(self):
        """ Constructor, Initialize the required variables
        """
        self.parents = {}

    def insert(self, x):
        """ Insert a new node

        Args:
            x (any): node of any type
        """
        if x in self.parents:
            return
        self.parents[x] = None

    def find(self, x) -> any:
        """ Find and return x's root
        update x's and all non-root nodes' parent along the find

        Args:
            x (any): node of any type

        Returns:
            any: x's parent
        """
        if x not in self.parents:
            return None
        root = x
        while self.parents[root] is not None:
            root = self.parents[root]

        #Update each parent along the chain to compress the search time later
        curr = x
        while curr != root:
            ori_parent = self.parents[curr]
            self.parents[curr] = root
            curr = ori_parent
        return root

    def is_connected(self, x, y) -> bool:
        """ Check if x and y is connected

        Args:
            x (any): node of any type
            y (any): node of any type

        Returns:
            bool: True if connected
        """
        #self to self is connected
        if x == y:
            return True
        root_x = self.find(x)
        root_y = self.find(y)
        # If either x or y not exist
        if root_x is None or root_y is None:
            return False
        return root_x == root_y

    def add_edge(self, x, y):
        """ add connection between x and y. 
        Basically group them together

        Args:
            x (any): node of any type
            y (any): node of any type
        """
        self.insert(x)
        self.insert(y)
        root_x = self.find(x)
        root_y = self.find(y)
        #Very Important to avoid self-pointing at root
        if root_x != root_y:
            self.parents[root_x] = root_y

    def get_separated_groups(self) -> list[list]:
        """ Return a list of separated nodes

        Returns:
            list[list]: list of separated nodes
        """
        root2nodes = collections.defaultdict(list)
        for node in self.parents:
            self.find(node)

        for node, parent in self.parents.items():
            if parent is None:
                root2nodes[node].append(node)
            else:
                root2nodes[parent].append(node)
        return sorted(root2nodes.values())

class TopoSort:
    """ class provide topological sort order 
    """
    def __init__(self, adjacency_list:dict):
        """ Constructor, Initialize the dependency count 
        map from the adjacency list provided
        
        Args:
            adjacency_list (dict): graph representation of given nodes
        """
        self.adjacency_list = adjacency_list
        self.node2depend_cnt = self.get_cnt_map(adjacency_list)

    def get_cnt_map(self, adjacency_list:dict) -> dict:
        """ Construct the dependency count map

        Args:
            adjacency_list (dict): graph representation of given nodes

        Returns:
            dict: the dependency count map
        """
        node2depend_cnt = collections.defaultdict(int)

        # fill the depend_cnt based on adjacency list graph
        # recall for each key value pairs in adjacency list
        # the key is required by the value, key need to finish first
        for node, required_by in adjacency_list.items():
            if node not in node2depend_cnt:
                node2depend_cnt[node] = 0
            # Then for each value in required_by, we add the depend_cnt by 1
            for req in required_by:
                node2depend_cnt[req] += 1
        return node2depend_cnt

    def get_topo_order(self, node_list:list)->tuple[bool, str, list]:
        """ performed topological sort based on the nodes in adjacency_list and node_list

        Args:
            node_list (list): list of node grouped together

        Returns:
            tuple[bool, str, list]: tuple of three return value
            first indicate if the sort passed or failed
            second is a list of error message
            third is resulted sorted list
        """
        result_flag = True
        result_error_msg = ""
        order = []
        queue = collections.deque()
        visited = set()
        for node in node_list:
            # depend_cnt == 0 means this node is not waiting on other node
            # and can be scheduled to start
            if self.node2depend_cnt[node] == 0:
                queue.append(node)
                order.append(node)
                visited.add(node)

        # bfs
        while queue:
            curr = queue.popleft()
            if curr not in self.adjacency_list:
                continue
            for required_by in self.adjacency_list[curr]:
                if required_by in visited:
                    continue
                self.node2depend_cnt[required_by] -= 1
                if self.node2depend_cnt[required_by] == 0:
                    queue.append(required_by)
                    order.append(required_by)
                    visited.add(required_by)

        # Check all node in the order
        cycle_list = []
        for node in node_list:
            if self.node2depend_cnt[node] != 0:
                cycle_list.append(node)
        if len(cycle_list) != 0:
            result_flag = False
            result_error_msg = f"Cycle error detected for jobs:{sorted(cycle_list)}\n"
            return (result_flag, result_error_msg, [])
        return (result_flag, result_error_msg, order)

class MongoHelper:
    """MongoHelper class to provide helper functions for MongoDB operations"""

    ## PipelineHistory
    @staticmethod
    def build_match_filter(repo_url: str, pipeline_name: str = None) -> dict:
        """Builds the match filter for a MongoDB aggregation pipeline."""
        match_filter = {"repo_url": repo_url}
        if pipeline_name:
            match_filter["pipelines." + pipeline_name] = {"$exists": True}
        return match_filter

    @staticmethod
    def build_aggregation_pipeline(match_filter: dict, pipeline_name: str = None, stage_name: str = None, job_name: str = None, run_number: int = None) -> list:
        """Builds the aggregation pipeline based on stage, job, and run number filters."""
        pipeline = [
            {"$match": match_filter},
            # {"$project": {"pipelines": 1}},
            {"$addFields": {"pipelines_array": {"$objectToArray": "$pipelines"}}},
            {"$unwind": "$pipelines_array"}]
        if pipeline_name:
            pipeline += [{"$match": {"pipelines_array.k": pipeline_name}}]
        pipeline.append({
            "$addFields": {
                "pipelines_array.v.job_run_history": {
                    "$map": {
                        "input": "$pipelines_array.v.job_run_history",
                        "as": "history_id",
                        "in": {"$toObjectId": "$$history_id"}
                    }
                }
            }
        })
        pipeline.append({
            "$lookup": {
                "from": "jobs_history",
                "localField": "pipelines_array.v.job_run_history",
                "foreignField": "_id",
                "as": "job_details"
            }
        })
        pipeline.append({"$unwind": "$job_details"})
        
        if run_number is not None:
            pass
        if stage_name:
            pass
        if job_name:
            pass
        return pipeline

    @staticmethod
    def build_projection(stage_name: str = None, job_name: str = None) -> dict:
        """Builds the projection stage for MongoDB aggregation based on stage and job fields."""
        projection_fields = {
            "pipeline_name": "$pipelines_array.k",
            "run_number": "$job_details.run_number",
            "git_commit_hash": "$job_details.git_commit_hash",
            "status": "$job_details.status",
            "start_time": "$job_details.start_time",
            "completion_time": "$job_details.completion_time"
        }
        if stage_name:
            pass
        if job_name:
            pass
        return projection_fields

    ## ConfigOverrides
    @staticmethod
    def build_nested_dict(overrides):
        """
        Build a nested dictionary from multiple key=value strings.

        Args:
            overrides (list): List of override strings in the form 'key=value'.

        Returns:
            dict: A nested dictionary.
        """
        updates = {}
        for override in overrides:
            key, value = override.split('=', 1)
            keys = key.split('.')
            nested_update = updates
            for k in keys[:-1]:
                nested_update = nested_update.setdefault(k, {})
            nested_update[keys[-1]] = value
        return updates

    @staticmethod
    def apply_overrides(config, updates):
        """
        Recursively apply updates to a configuration dictionary.

        Args:
            config (dict): The original dictionary.
            updates (dict): New key-value pairs to apply.

        Returns:
            dict: The updated dictionary.
        """
        for key, value in updates.items():
            if isinstance(value, dict):
                config[key] = MongoHelper.apply_overrides(config.get(key, {}), value)
            else:
                config[key] = value
        return config

class DryRun:
    """DryRun class to handle message output formatting for cid pipeline, to print plain text
    or YAML format."""
    def __init__(self, config_dict: dict):
        self.config = config_dict
        self.global_dict = config_dict.get("global")
        self.jobs_dict = config_dict.get("jobs")
        self.stages_order = config_dict.get('stages')
        self.dry_run_msg = ""
        self.yaml_output_msg = ""

        self.global_msg = ""
        self.stage_msg = ""

        self._build_dry_run_msg()

    def get_plaintext_format(self) -> str:
        """return dry run message in plain text format.

        Returns:
            str: dry run message ordered by stages
        """
        return self.dry_run_msg

    def get_yaml_format(self) -> str:
        """return dry run message with yaml format.

        Returns:
            str: valid yaml dry run message
        """
        global_yaml_output = self._parse_global(self.global_msg)
        jobs_yaml_output = self._parse_jobs(self.stage_msg)

        self.yaml_output_msg = global_yaml_output + jobs_yaml_output
        return self.yaml_output_msg

    def _parse_global(self, text:str) -> str:
        """Given the plain text that is build when running the _build_dry_run_msg(),
        this function purpose is to convert the text into valid yaml. This result
        will be return as string to get_yaml_format() method.

        Args:
            text(str): global section of the config file

        Returns:
            str: yaml format of the global section of the config file
        """
        global_dict = {}

        # Find global settings
        global_match = re.search(r'===== \[INFO\] Global =====\s*(.+?)(?======|\Z)',
                                 text, re.DOTALL)
        if global_match:
            global_text = global_match.group(1)

            # Parse global attributes
            attr_pairs = re.findall(r'(\w+): (\'[^\']*\'|\[.*?\]|\{.*?\}|[^\s,]+)', global_text)

            for key, value in attr_pairs:
                if value.startswith("{"):
                    global_dict[key] = eval(value)
                else:
                    global_dict[key] = value.strip("'")

        yaml_output = yaml.dump({'global': global_dict}, sort_keys=False)
        return yaml_output

    def _parse_jobs(self, text:str) -> str:
        """Given the plain text that is build when running the _build_dry_run_msg(),
        this function purpose is to convert the text into valid yaml. This result
        will be return as string to get_yaml_format() method.

        Args:
            text(str): jobs section of the config file

        Returns:
            str: yaml format of the jobs section of the config file
        """
        # Initialize dictionary to hold all jobs
        jobs_dict = {}

        # Split by stages using regex
        stage_blocks = re.split(r'===== \[INFO\] Stages: \'(.+?)\' =====', text)

        for i in range(1, len(stage_blocks), 2):
            stage_name = stage_blocks[i]
            job_text = stage_blocks[i + 1]

            # Split each job line
            job_lines = re.findall(r'Running job: "(.+?)", (.+)', job_text)

            for job_name, attributes in job_lines:
                # Dictionary to hold job attributes
                job_dict = {'stage': stage_name}

                # Parse attributes
                attr_pairs = re.findall(r'(\w+): (\'[^\']*\'|\[.*?\]|\{.*?\}|[^\s,]+)', attributes)

                for key, value in attr_pairs:
                    if value.startswith("[") or value.startswith("{"):
                        job_dict[key] = eval(value)
                    elif value.lower() == "true":
                        job_dict[key] = True
                    elif value.lower() == "false":
                        job_dict[key] = False
                    else:
                        job_dict[key] = value.strip("'")

                # Add job to the jobs dictionary
                jobs_dict[job_name] = job_dict

        yaml_output = yaml.dump({'jobs': jobs_dict}, sort_keys=False)
        return yaml_output


    def _build_dry_run_msg(self):
        """The purpose of this function is to convert the config_dict to plain text of
        the dry_run message. This adheres to the stages order that the config file may have.
        """
        # Loop through the keys in the global section
        global_msg = "\n===== [INFO] Global =====\n"
        for key in self.global_dict:
            global_msg += f"{key}: {self.global_dict[key]}, "
        global_msg += "\n"
        self.global_msg = global_msg
       # Loop through the stages with order
        stage_msg = ""
        for stage in self.stages_order:
            stage_msg += f"\n===== [INFO] Stages: '{stage}' =====\n"
            #build, test doc, deploy, etc..
            # to retrieve the job of the stages, need to loop through
            # the dict and run the job given the defined order.
            job_groups = self.stages_order[stage]['job_groups']
            for job_group in job_groups:
                for job in job_group:
                    job_msg = self._format_job_info_msg(job, self.jobs_dict[job])
                    stage_msg += job_msg

        self.stage_msg = stage_msg

        self.dry_run_msg += global_msg
        self.dry_run_msg += stage_msg

    def _format_job_info_msg(self, name:str, job:dict) -> str:
        """Format the output message for user (plain text version). This function is
        used by _build_dry_run_msg().

        Args:
            name (str): job name
            job (dict): key-value of the job, such as "stages:<value>, scripts:<value>, etc"

        Returns:
            str: dry run message
        """
        formatted_msg = f'Running job: "{name}"'
        for key, value in job.items():
            formatted_msg += f', {key}: {value}'
        formatted_msg += "\n"

        return formatted_msg

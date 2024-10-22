""" 
Provide the common utility functions used by all other modules
"""
import collections
import logging
from dotenv import dotenv_values


def get_logger(logger_name='', log_level=logging.DEBUG, log_file='debug.log') -> logging.Logger:
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
    # create console handler and set level to info
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

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
    """ Retrieve the env variables from the environment. Perform further processing if necessary

    Returns:
        dict: dictionary of env values in key=value pairs
    """
    config = dotenv_values(".env")
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

class ConfigOverrides:
    """ConfigOverrides Class to handle building and applying nested dictionary overrides."""

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
                config[key] = ConfigOverrides.apply_overrides(config.get(key, {}), value)
            else:
                config[key] = value
        return config

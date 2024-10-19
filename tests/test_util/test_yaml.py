# For code walk on 15th Oct only, delete/modify after
import os
import pprint
import yaml
from util.config_tools import ConfigChecker

local_valid_config = os.path.join(os.path.dirname(__file__), 'test_data/valid_config.yml')
print(local_valid_config)
data = {}
with open(local_valid_config, 'r', encoding='utf-8') as file:
    data = yaml.safe_load(file)
pprint.pprint(data)

checker = ConfigChecker(pipeline_name='valid_pipeline')
result_dict = checker.validate_config('valid_pipeline', data)
pprint.pprint(result_dict)

local_cycle_config = os.path.join(os.path.dirname(__file__), 'test_data/cycle_config.yml')
with open(local_cycle_config, 'r', encoding='utf-8') as file:
    cycle_data = yaml.safe_load(file)
pprint.pprint(cycle_data)
result_dict = checker.validate_config('cycle_pipeline', cycle_data)
pprint.pprint(result_dict)
This readme file explains how the tests are organized within the test folder.

## Organization of Folder and File Structure

- Each test package corresponds to a single package under src directory.
- For each modules inside the package, a corresponding single test file is created for unit test.
- For integration tests involving more than two modules, a separate test file is created.

## Organization of Unit Test

- Classes, Functions or Features required by multiple modules are placed in conftest.py file
- Classes, Functions or Features required by the same module are initialize in the setUp method of respective test class.

## List of Integration Test

### cli.cmd_pipeline and Controller

test_module: tests/test_cli/test_cmd_pipeline.py

test class: class TestPipelineRun

### ConfigChecker and YamlParser

test_module: tests/test_util/test_yaml_parser.py

test methods involved integration tests:

- test_parse_yaml_file_valid
- test_parse_yaml_file_cycle_detection
- test_parse_yaml_file_invalid_config

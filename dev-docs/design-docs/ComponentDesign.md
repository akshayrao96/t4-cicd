# Component Design

## Overview of Main Component Classes

## Descriptions for Each Components

### CLI Module

### Controller Module

### RepoManager Module

### Container(DockerManager) Module

### Db_mongo(MongoAdapter) Module

### Db_artifact(S3Client) Module

### Config_tool(ConfigChecker) Module

### YamlParser Module

### Common_utils Module

### Other Module

## Example Sequence Diagram

<img src="../images/SeqPipelineRun.jpg" alt="System Design" width="1000" height="1500">

## Suplement Information

### Pydantic Model vs Dict

- pydantic model is used whenever applicable
- dictionary is used for raw pipeline configuration extracted from yaml files. This is to preserve the line and column information for error tracings.

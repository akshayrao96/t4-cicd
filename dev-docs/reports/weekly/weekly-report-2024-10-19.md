# Week 6 (Oct 13 - Oct 19)

  

## Summary

This sprint we focus on meeting the Requirement - Iteration 2 for our first code walk. We did the meeting on Monday 10/14 instead of Tuesday to make sure the code works. and on the 10/18 to discuss updated design decision based on feedback.

We added [Issue #62](https://github.com/CS6510-SEA-F24/t4-cicd/issues/62) to track the feedback from other teams, Professor, and from our observation what the other team did well.

Following are notes from meeting:
- Design Docs are created to centralize our design decision and be the discussion points during the weekly meeting discussion.
- We took a step back to redefine our high level design diagram to add the local/server design and agree on an approach.
- Archive/Delete no longer relevant / outdated issues from GitHub tracker. This is to help us focus on the new design. So you may see some carry over tasks that got deleted/renamed.
- added several use cases that we defined and want to prioritize as a team to achieve. Ideally to have 2 out of 4 use cases are delivered. The use cases is defined from the new system_integration_diagram_*.png that is added below the #Design Updates section.

This week meeting chairperson & report writer - Jason

Next week meeting chairperson - Chin

# Completed tasks

| Task | Weight | Assignee |
| ------------------------------------------------------ | --------- | -------- |
| [Config] Implement Config Checker for pipeline content validation with job cycle detection [#38](https://github.com/CS6510-SEA-F24/t4-cicd/issues/38) | M - 2/3 days | Chin |
| [Design] Update High Level Design Diagram to incorporate the local/server design. This should include defining REST API. [#64](https://github.com/CS6510-SEA-F24/t4-cicd/issues/64) | M - 2/3 days | Jason -> Chin |

# Carry over tasks

| Task | Weight       | Assignee    |
| ------------------------------------------------------------------------------------------------------------------------- | ------------ | ----------- |
| [CLI] define & implement cid pipeline --dry-run [#33](https://github.com/CS6510-SEA-F24/t4-cicd/issues/33)                                                                          | M - 2/3 days | Jason       |
| [Yaml] Resolve Pyyaml silently overwrite duplicate keys instead of reporting it [#45](https://github.com/CS6510-SEA-F24/t4-cicd/issues/45)                                          | S - 1 day    | Lin -> Chin |
| [RepoManager] Add flexible method to extract any yaml file given the absolute path [#56](https://github.com/CS6510-SEA-F24/t4-cicd/issues/56)                                       | S - 1 day    | Chin        |
| [Design] Update High Level Design Diagram to incorporate the local/server design. This should include defining REST API. [#64](https://github.com/CS6510-SEA-F24/t4-cicd/issues/64) | M - 2/3 days | Chin        |
| [RepoManager] refactor RepoManager to separate it with FileManager [#68](https://github.com/CS6510-SEA-F24/t4-cicd/issues/68)                                                       | S - 1 day    | Lin         |
| [CLI] Update CLI documentation [#67](https://github.com/CS6510-SEA-F24/t4-cicd/issues/67)                                                                                       | S - 1 day    | Akshay      |


# New tasks / Backlog

| Task                                                                                                                | Weight     | Assignee |
| ------------------------------------------------------------------------------------------------------------------- | ---------- | -------- |
| [SystemDesign] Standardize and document the error handling and logging behaviour #41                                | M - 2/3 days | TBD      |
| [CLI] Update CLI documentation [#67](https://github.com/CS6510-SEA-F24/t4-cicd/issues/67)                           | S - 1 day  | Akshay   |
| Initial design for Data Storage Schemes                                                                             | S - 1 day | Chin     |
| L4.1.Show summary all past pipeline runs for a repository[#55](https://github.com/CS6510-SEA-F24/t4-cicd/issues/55) | S - 1 day | TBD      |
| Implement use case 1 - get & set working repo                                                                       | S - 1 day | Akshay   |
| Implement use case 2 - Validate Pipeline Configurations                                                             | S - 1 day | Chom     |
| Implement use case 3 - dry run command                                                                              | S - 1 day | Jason    |
| Implement use case 4 - change config values via cli                                                                 | S - 1 day | Lin      |

  

# What worked this week?
- Jason: the code walk opens up new perspective on how well we have done as a team up to this point. 

# What did not work this week?
- Jason: spent more time to redesigning the components because it's not working as we planned, such as Controller singleton.
- Jason: I have emergency issues that took me away from this project for a day.


# Design updates
Local / Server design that describes the high level architecture of the current components we have.
![High level design](../../images/week6/High%20Level%20System%20Design%20v0.2.png)

divide the sequence diagram into several use cases for each devs to pick up and execute.
![System Integration](../../images/week6/system_integration_diagram_phase2_v0.1.drawio.png)
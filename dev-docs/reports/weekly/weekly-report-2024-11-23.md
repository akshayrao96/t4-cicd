# Week 11 (Nov 17 - Nov 24)

# Summary

On Tuesday, 19 November, the team reviewed DB reports and made the demo video for an end to end run. 
On Friday, 22 November, discussions focused on :
- Reviewing PRs for repository management and artifact upload to S3 
- Updating project developer documentation and splitting tasks accordingly
- Identifying unnecessary code/stubs and planning refactoring for codebase
- Publishing of the CLI tool to PyPI
- Fixing any bugs during user testing. 

One of the main sharings during the meeting, 
As we are learning while developing, there are cases when we have developed the codes in the less effective/efficient way, later on we 
discover new methods/ways which make our life easier. The hard choice to made is whether we can afford to spend the time and go back to 
refactor previous codes. One example is the adoption of Pydantic Model replacing the dictionary, this eliminate the use of magic keyword 
in the dictionary, and help validate the content of the dictionary in the required types and values. While we try our best to develop new code
based on Pydantic Model as much as we can, there are still cases where we cant afford to spend time and effort to refactor old codes to be consistent 
with the use of Pydantic model style. 

The other example is the consideration to use pytest.fixture in our test cases. In theory, pytest.fixture shared throughout the modules/packages
can help to adhere to DRY principle when the test_inputs/mock_outputs are repetitive. However, use of pytest.fixture is not compatible with 
our current style of patching/mocking the methods in isolation tests, and we dont have the required time and effort to refactor the test cases
to use pytest.fixture. Hence we decided to leave the test cases as they were in existing style. 

The team also prioritized tasks on the status board to ensure key features are completed this final coming week.

# Completed tasks

| Task                                                                                                                          | Weight     | Assignee |
|-------------------------------------------------------------------------------------------------------------------------------|------------|----------|
| [UC1-CLI&RepoManager] Options for Branch & Commit For Local Repo[ #121](https://github.com/CS6510-SEA-F24/t4-cicd/issues/121) | M - 3 days | Akshay   |
| [UC6] Show pipeline run summary, stage summary, job summary[ #143](https://github.com/CS6510-SEA-F24/t4-cicd/issues/143)                             | M - 2/3 day   | Lin            |
| [Customer Req] Pipeline run with custom Docker Registry & Java Repository[ #117](https://github.com/CS6510-SEA-F24/t4-cicd/issues/117)               | M - 2/3 days  | Chin           |
| [UC1, UC2, UC3] Integrate the usecases from set repo, check config, up to dry run[ #84](https://github.com/CS6510-SEA-F24/t4-cicd/issues/84)         | S - 1 day     | Chin           |
| [Customer Req] Pipeline run with sample JavaScript Repository[ #147](https://github.com/CS6510-SEA-F24/t4-cicd/issues/147)         | S - 1 day     | Chin           |

# Carry over tasks
| Task                                                                                                                                                 | Weight        | Assignee       |
|------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|----------------|
| [Customer Req] Installing CLI as independent app[ #116](https://github.com/CS6510-SEA-F24/t4-cicd/issues/116)                                        | S - 1 day     | Chin           |
| [CLI] add tests and remaining feature for Report[ #141](https://github.com/CS6510-SEA-F24/t4-cicd/issues/141)                                        | S - 1 day     | Jason          |
| [UC1, UC2, UC4] Integrate usecases from set repo, check config and override config[ #88](https://github.com/CS6510-SEA-F24/t4-cicd/issues/88)        | S - 1 day     | Akshay -> Chin |
| [UC5 - Controller & Docker] Implement the methods required to run, stop, cancel pipeline [ #17](https://github.com/CS6510-SEA-F24/t4-cicd/issues/17) | L/XL - 2 week | Chin           |
| [UC2 - Config] Output Format Modification and Clean Up[ #80](https://github.com/CS6510-SEA-F24/t4-cicd/issues/80)               | S - 1 day    | Akshay -> Chin |
| [Project Submission] Project Documentation for Final Report[ #124](https://github.com/CS6510-SEA-F24/t4-cicd/issues/124)                             | M - 2/3 days  | Akshay         |
| [Project Submission] Final Integration Testing[ #155](https://github.com/CS6510-SEA-F24/t4-cicd/issues/125)                     | M - 2/3 days | Chin, Jason    |


# New tasks / Backlog

| Task                                                                                                                            | Weight       | Assignee       |
|---------------------------------------------------------------------------------------------------------------------------------|--------------|----------------|

| [Project Submission] Code Refactoring for better quality and style[ #125](https://github.com/CS6510-SEA-F24/t4-cicd/issues/125) | M - 2/3 days | Lin            |

# What worked this week?


# What did not work this week?
- One of our team member was down due to flu, less productivity
- Changing requirements previously resulted in codes and features that was developed but no significant use, taking some time to clean it up before final submission and packaging. 

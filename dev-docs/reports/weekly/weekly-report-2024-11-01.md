# Week 8 (Oct 26 - Nov 2)

# Summary

This sprint, we continue to focus on integrating different use cases and meeting requirements for our upcoming demo. Brief status updates were discussed on 10 / 29, followed by a detailed meeting on 11 / 1 to cover ongoing work and targets for the 11 / 5 demo.

Following are notes from meeting:

- Reviewed and addressed all open pull requests, noting necessary changes team is clear on changes to be made.
- Discussed the intricacies of integrating use cases together.
- The trickiest parts were handling scope of cloning(which branches / commits to clone), and approach to handling commits and branch histories of the same repository. Additional research is required.
- Made sure team knows which parts they are handling, and expectations for the demo

This week meeting chairperson & report writer - Akshay

Next week meeting chairperson -

# Completed tasks

| Task           | Weight    | Assignee    |
|----------------|-----------|-------------|


# Carry over tasks

| Task                                                                                                                                                   | Weight        | Assignee |
|--------------------------------------------------------------------------------------------------------------------------------------------------------|---------------| -------- |
| [UC1 - CLI & RepoManager] Options for Branch & Commit[  # 83](https://github.com/CS6510-SEA-F24/t4-cicd/issues/83)                                     | M - 2/3 days  | Akshay   |
| [Pytest] improve test coverage for cmd & controller[  # 82](https://github.com/CS6510-SEA-F24/t4-cicd/issues/82)                                       | M - 2/3 days  | Lin      |
| [UC5] MongoAdapter methods for docker run operation[  # 90](https://github.com/CS6510-SEA-F24/t4-cicd/issues/90)                                       | M - 2/3 days  | Lin      |
| [UC2 Config] Save validated config to MongoDB[  # 76](https://github.com/CS6510-SEA-F24/t4-cicd/issues/76)                                             | S - 1 days    | Lin      |
| [CLI] implement cid pipeline dry - run missing features[  # 89](https://github.com/CS6510-SEA-F24/t4-cicd/issues/89)                                   | M - 2/3 days  | Jason    |
| [UC3, UC5 CLI] Update cid pipeline run commands[  # 85](https://github.com/CS6510-SEA-F24/t4-cicd/issues/85)                                           | M - 2/3 days  | Jason    |
| [UC5 - Controller & Docker] Implement the methods required to run, stop, cancel pipeline[  # 17] (https://github.com/CS6510-SEA-F24/t4-cicd/issues/17) | L/XL - 2 week | Chin     |
| [UC5 - Python Repo Sample] Create Sample Repo with cicd configuration for testing[  # 87](https://github.com/CS6510-SEA-F24/t4-cicd/issues/87)                      | M - 2/3 days | Chin     |
| [UC5 - Controller & Docker] Implement first version of DockerManager class to run and log the pipeline[# 99] (https://github.com/CS6510-SEA-F24/t4-cicd/issues/99) | L/XL - 2 week | Chin     |

# New tasks / Backlog

| Task                                                                                                                                                                | Weight       | Assignee |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------| -------- |
| [SystemDesign] Standardize and document the error handling and logging behaviour[  # 41](https://github.com/CS6510-SEA-F24/t4-cicd/issues/41)                       | L - 1 week   | Lin      |
| [UC6] Show summary all past pipeline runs for a repository[  # 55](https://github.com/CS6510-SEA-F24/t4-cicd/issues/55)                                             | L - 1 week   | Lin      |
| [UC2 - Config] Output Format Modification and Clean Up[  # 80](https://github.com/CS6510-SEA-F24/t4-cicd/issues/80)                                                 | S - 1 day    | Akshay   |
| [UC1, UC2, UC3] Integrate the usecases from set repo, check config, up to dry run[  # 84] (https://github.com/CS6510-SEA-F24/t4-cicd/issues/84)                     | S - 1 day    | Jason    |
| [UC1, UC2, UC4] Integrate usecases from set repo, check config and override config[  # 88] (https://github.com/CS6510-SEA-F24/t4-cicd/issues/88)                    | S - 1 day    | Akshay   |
| [UC5 - Java Repo Sample] Create A Sample Repository with Java Project that with the cicd configuration[  # 86](https://github.com/CS6510-SEA-F24/t4-cicd/issues/86) | M - 2/3 days | Akshay   |


# What worked this week?

- Akshay: Discussions on implementations rather than design. Our team is at the point where we all know what we need to do.
- Akshay: Shorter meetings
- Chin: Playing around with Python Docker SDK to get the basis idea of what is required to code the DockerManager class. Plan for future addition of different container run strategy (like Kubernetes) by designing an interface for ContainerManager.
- Jason: finishing up dry-run features that adheres to stages order and refactoring code.

# What did not work this week?


# Design updates

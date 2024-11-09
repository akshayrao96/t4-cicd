# Week 9 (Nov 3 - Nov 9)

# Summary
This week, we met on Monday for a team code walk in preparation for the demo. On 11/8, we aligned on the option proposed during Tuesday's 1on1, choosing the DB + report approach. We will also work on new features, including:
- Installing as an independent app
- Running a pipeline with a Java repo
- Uploading artifacts to a datastore

For the final delivery, we have identified requirements we believe we can or cannot complete. 
The feature list details can be viewed [here](https://docs.google.com/document/d/1oesRDCpEncrD0_QPSlQgghg0l__P-bS8_qZtxCVQn0c/edit?tab=t.0).

Meeting notes:
- The team reviewed the latest pull request, focusing on the set/get repo and Docker implementation.
- We discussed approaches to handling edge cases in the set/get repo.
- We aligned on the demo for next week and distributed the new use cases among team members.

This week meeting chairperson & report writer - Lin

Next week meeting chairperson - Jason

# Completed tasks

| Task           | Weight    | Assignee    |
|----------------|-----------|-------------|
| [UC5] MongoAdapter methods for docker run operation[  # 90](https://github.com/CS6510-SEA-F24/t4-cicd/issues/90)                                       | M - 2/3 days  | Lin      |
| [CLI] implement cid pipeline dry - run missing features[  # 89](https://github.com/CS6510-SEA-F24/t4-cicd/issues/89)                                   | M - 2/3 days  | Jason    |
| [UC5 - Controller & Docker] Implement first version of DockerManager class to run and log the pipeline[# 99] (https://github.com/CS6510-SEA-F24/t4-cicd/issues/99) | L/XL - 2 week | Chin     |
| [UC5 - Python Repo Sample] Create Sample Repo with cicd configuration for testing[  # 87](https://github.com/CS6510-SEA-F24/t4-cicd/issues/87)                      | M - 2/3 days | Chin     |
| [Project] - Add code documentation generation to main repo[  # 115](https://github.com/CS6510-SEA-F24/t4-cicd/issues/115)                      | XS | Chin     |


# Carry over tasks

| Task                                                                                                                                                   | Weight        | Assignee |
|--------------------------------------------------------------------------------------------------------------------------------------------------------|---------------| -------- |
| [UC6] Show summary all past pipeline runs for a repository[  # 55](https://github.com/CS6510-SEA-F24/t4-cicd/issues/55)                                             | L - 1 week   | Lin     |
| [UC1 - CLI & RepoManager] Options for Branch & Commit[  # 83](https://github.com/CS6510-SEA-F24/t4-cicd/issues/83)                                     | M - 2/3 days  | Akshay   |
| [UC3, UC5 CLI] Update cid pipeline run commands[  # 85](https://github.com/CS6510-SEA-F24/t4-cicd/issues/85)                                           | M - 2/3 days  | Jason    |
| [UC5 - Controller & Docker] Implement the methods required to run, stop, cancel pipeline[  # 17] (https://github.com/CS6510-SEA-F24/t4-cicd/issues/17) | L/XL - 2 week | Chin     |
| [Customer Req] Pipeline run with custom Docker Registry & Java Repository[  # 117] (https://github.com/CS6510-SEA-F24/t4-cicd/issues/117) | M - 2/3 days  | Chin     |
| [UC4, UC5 Controller] run_pipeline continuous improvement [  # 111](https://github.com/CS6510-SEA-F24/t4-cicd/issues/111) | M - 2/3 days  | Chin     |



# New tasks / Backlog

| Task                                                                                                                                                                | Weight       | Assignee |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------| -------- |
| [SystemDesign] Standardize and document the error handling and logging behaviour[  # 41](https://github.com/CS6510-SEA-F24/t4-cicd/issues/41)                       | L - 1 week   | Lin      |
| [UC2 - Config] Output Format Modification and Clean Up[  # 80](https://github.com/CS6510-SEA-F24/t4-cicd/issues/80)                                                 | S - 1 day    | Akshay   |
| [UC1, UC2, UC3] Integrate the usecases from set repo, check config, up to dry run[  # 84] (https://github.com/CS6510-SEA-F24/t4-cicd/issues/84)                     | S - 1 day    | Jason    |
| [UC1, UC2, UC4] Integrate usecases from set repo, check config and override config[  # 88] (https://github.com/CS6510-SEA-F24/t4-cicd/issues/88)                    | S - 1 day    | Akshay   |
| [UC5 - Java Repo Sample] Create A Sample Repository with Java Project that with the cicd configuration[  # 86](https://github.com/CS6510-SEA-F24/t4-cicd/issues/86) | M - 2/3 days | Akshay   |
| [Customer Req] Installing CLI as independent app[  # 116] (https://github.com/CS6510-SEA-F24/t4-cicd/issues/116) | S | Chin     |

# What worked this week?
- list down requirement that is implemented and not yet implemented. This help during our weekly meeting prioritize for the upcoming weeks (and for Theo to review).
- Chin - we have certainty on the requirements we have to complete and the remaining demo schedule, this can help us plan the work, phase it evenly across next 3 weeks, and avoid unbalance distribution or burn out. 

# What did not work this week?

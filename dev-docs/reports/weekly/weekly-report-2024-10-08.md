# Week 4 (Oct 1 - Oct 8)

## Summary

Meeting on 1st and 4th October to monitor and tackle issues. Following are notes from meeting:

- Clarified direction for the CLI with proper naming conventions. Focused on making sure we can read different pipelines and repositories.
- Ensured that the Click API triggers function calls directly, not YAML.
- Brainstormed a high-level **Controller class** and how it interfaces with the different components.
- Discussed the data store architecture and how the controller interfaces with **MongoDB** and **MySQL**.
- Breaking down issues into smaller, specific and deliverable tasks. We previously had tasks that were too generic and vague.
- Team-specific practice of having a development branch before pushing to the main

This week meeting chairperson & report writer - Akshay

Next week meeting chairperson - Peihsuan Lin

# Completed tasks

| Task                     | Weight     | Assignee |
| ------------------------ | ---------- | -------- |
| #2 Initial Project Setup | S - 1 days | Chin     |
| #25 Add sample interaction CRUD functions with MongoDB | M - 2/3 days | Chin     |
| #24 Create Barebone CLI Interface Structure | S - 1 days | Jason |
| #29 Creating Docker Runner with Python API call | XS - 2-3 hours | Akshay | 
| #20 Create functions with associated class to read the files in the given Github repository, locate the target yml file and extract its content ready for parsing | M - 2/3 days | Peihsuan |

# Carry over tasks

| Task                                                                                                                                                                  | Weight       | Assignee |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | -------- |
| #4 Update High Level System Design & Tech Stack Selection                                                                                                             | S - 1 days   | Akshay   |
| #6 Design the first controller class and add initial set of commands to trigger the first workflow                                                                    | M - 2/3 days | Jason    |
| #10 Create functions with associated classes to run a predefined docker container with preset scripts, and capture the output from the docker container run           | M - 2/3 days | Akshay   |
| #27 Add sample interaction CRUD functions with MySQL                                                                                                                  | M - 2/3 days | Chin     |
| Initial design for Data Storage Schemes                                                                                                                               | S - 1 days   | Chin     |

# New tasks / Backlog

| Task | Weight | Assignee |
| ---- | ------ | -------- |
|      |        |          |

# What worked this week?

- Akshay : Team meetings tend to clarify a lot of confusion surrounding the design.
- Chin : Narrowed down the scope of tasks when realized the assigned task is too big for one week.
- Peihsuan: Implement basic functionality for cloning repositories and finding and parsing YAML files.
  
# What did not work this week?

- Akshay : Issues I created were too vague. Moving forward, I'll have smaller issues stemming from current issues
- Akshay : Focused too much on the underlying architecture rather than implementing
- Akshay : Time management
- Jason : The task that I define for CLI [#6](https://github.com/orgs/CS6510-SEA-F24/projects/8/views/1?pane=issue&itemId=81403046&issue=CS6510-SEA-F24%7Ct4-cicd%7C6) is too big. It took a while to break it into steps and finally start working on the implementation.

# Design updates


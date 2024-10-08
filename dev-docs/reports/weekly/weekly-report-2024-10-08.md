# Week 4 (Oct 1 - Oct 8)

## Summary

Meeting on 1 October to monitor and tackle issues. Following are notes from meeting:

- Clarified direction for the CLI with proper naming conventions. Focused on making sure we can read different pipelines and repositories.
- Ensured that the Click API triggers function calls directly, not YAML.
- Brainstormed a high level **Controller class** and how it interfaces with the different components.
- Discussed the data store architecture and how the controller interfaces with **MongoDB** and **MySQL**.
- Breaking down issues into smaaller,specific and deliverable tasks. We previously had tasks that were too generic and vague.
- Team specific practice of having a development branch before pushing to main

This week meeting chairperson & report writer - Akshay
Next week meeting chairperson - 

# Completed tasks

| Task                     | Weight     | Assignee |
| ------------------------ | ---------- | -------- |
| #2 Initial Project Setup | S - 1 days | Chin     |

# Carry over tasks

| Task                                                                                                                                                                  | Weight       | Assignee |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | -------- |
| #4 Update High Level System Design & Tech Stack Selection                                                                                                             | S - 1 days   | Akshay   |
| #6 Define CLI commands/args available for client to use                                                                                                               | S - 1 days   | Jason    |
| #6 Design the first controller class and add initial set of commands to trigger the first workflow                                                                    | M - 2/3 days | Jason    |
| Create functions with associated class to read the files in the given Github repository, locate the target yml file and extract its content ready for parsing         | M - 2/3 days | Peihsuan |
| #10 Create functions with associated classes to run a predefined docker container with preset scripts, and capture the output from the docker container run           | M - 2/3 days | Akshay   |
| #8 Create two functions with associated classes to create and read data into MySQL server (for blob object storage) and MongoDB server (for other documents and logs) | M - 2/3 days | Chin     |
| #9 Create two functions with associated classes to create and read data into the MongoDB server (for other documents and logs)                                        | M - 2/3 days | Chin     |
| Initial design for Data Storage Schemes                                                                                                                               | S - 1 days   | Chin     |

# New tasks

| Task | Weight | Assignee |
| ---- | ------ | -------- |
|      |        |          |

# What worked this week?

- Akshay : Team meetings tend to clarify a lot of confusion surrounding the design.

# What did not work this week?

- Akshay : Issues I created were too vague. Moving forward, I'll have smaller issues stemming from current issues
- Akshay : Focused too much on the underlying architecture rather than implenting
- Akshay : Time management

# Design updates


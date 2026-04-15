![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)

# Containerized App Exercise

Build a containerized app that uses machine learning. See [instructions](./instructions.md) for details.


## APP Description: CollegeMaxxing 

We are the AI service that sue to help every applicant to fully analyze their odds/chance/potential to get into the university they want, and give professtional feedback based on their credential including(personal essay, sat score, gpa, mock interview response created by us, and more!)

## Github

[Github Link](https://github.com/swe-students-spring2026/4-containers-fantastic_five)

## Developers

[Blake Chang](https://github.com/louisvcarpet)



## Environment Variables

This app **does** require .env file, which is your own LLM api keys and mongodb urls.

Below is the env.example file: 


``` PIPENV_IGNORE_VIRTUALENVS=1
OPENAI_API_KEY= 
MONGO_URI=mongodb:
MONGO_DBNAME=

SECRET_KEY=dev
```

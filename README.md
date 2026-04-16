![ML Client Workflow](https://github.com/swe-students-spring2026/4-containers-fantastic_five/actions/workflows/ml-client.yml/badge.svg)
![Web App Workflow](https://github.com/swe-students-spring2026/4-containers-fantastic_five/actions/workflows/web-app.yml/badge.svg)

# Containerized App Exercise

Build a containerized app that uses machine learning. See [instructions](./instructions.md) for details.

## APP Description: CollegeMaxxing

CollegeMaxxing is a containerized application that helps students analyze their college application profile and better understand their chances of admission. Users can upload a personal essay, enter academic information such as GPA and SAT score, complete mock interview responses, and receive AI-generated feedback about their application strengths, missing elements, suggested edits, and overall applicant profile.

This project is made up of three connected subsystems:

- a machine learning client
- a Flask web app
- a MongoDB database

## Github

[Github Link](https://github.com/swe-students-spring2026/4-containers-fantastic_five)

## Developers

[Blake Chang](https://github.com/louisvcarpet)
[Sarya Sadi](https://github.com/saryassadi)

## Project Structure

```text
4-containers-fantastic_five/
├── compose.yaml
├── instructions.md
├── README.md
├── Pipfile
├── Pipfile.lock
├── settings.json
├── machine-learning-client/
└── web-app/
```

## System Architecture

This application uses three containers:

1. **MongoDB**
   - stores users, uploaded content, sessions, and analysis results

2. **Machine Learning Client**
   - processes student application data
   - performs AI or LLM-based analysis
   - writes analysis results and metadata to MongoDB

3. **Web App**
   - built with Flask
   - allows users to sign up, log in, create sessions, upload essays, complete interview flows, and view saved results
   - reads and writes data from MongoDB

## Environment Variables

This app **does** require a `.env` file for API keys and MongoDB configuration.

Create a file named `.env` in the root of the project.

Example `.env` file:

```env
PIPENV_IGNORE_VIRTUALENVS=1
OPENAI_API_KEY=your_openai_api_key_here
MONGO_URI=mongodb://mongodb:27017/appdb
MONGO_DBNAME=appdb
SECRET_KEY=dev
```

### Notes

- `OPENAI_API_KEY` is required for the AI analysis features
- `MONGO_URI` points to the MongoDB container when running with Docker Compose
- `MONGO_DBNAME` is the name of the MongoDB database used by the application
- `SECRET_KEY` is used by Flask for session management

## Prerequisites

Before running the project, make sure you have installed:

- Docker
- Docker Compose
- Python 3
- pip or pipenv
- Git

## How to Run the Full Project

### 1. Clone the repository

```bash
git clone https://github.com/swe-students-spring2026/4-containers-fantastic_five.git
cd 4-containers-fantastic_five
```

### 2. Create the `.env` file

Create a `.env` file in the root directory using the example in the Environment Variables section above.

### 3. Start all containers

```bash
docker compose up --build
```

### 4. Open the web app

Visit:

```text
http://localhost:5001
```

### 5. Stop the containers

```bash
docker compose down
```

## Docker Compose Services

The `compose.yaml` file starts the following services:

- `mongodb` on port `27017`
- `ml-client`
- `web-app` on port `5001:5000`

This allows all parts of the application to run together with one command.

## Local Development

### Machine Learning Client

```bash
cd machine-learning-client
pipenv install
pipenv run python CMagent.py
```

### Web App

```bash
cd web-app
pip install -r requirements.txt
python app.py
```

## Testing

This project uses `pytest` and `coverage` for automated testing.

### Machine Learning Client Tests

```bash
cd machine-learning-client
pytest
coverage run -m pytest
coverage report -m
```

### Web App Tests

```bash
cd web-app
pytest
coverage run -m pytest
coverage report -m
```

Both subsystems are expected to maintain at least **80% code coverage**.

## Code Quality

Code in both subsystems is expected to follow:

- `PEP 8`
- `black`
- `pylint`

Linting and formatting checks are run through GitHub Actions.

## Continuous Integration

This project uses GitHub Actions workflows for both major subsystems:

- one workflow for the machine learning client
- one workflow for the web app

These workflows automatically run linting, tests, and coverage checks after code is merged into `main`, and can also be configured to run on pull requests.

## Database Setup

MongoDB runs inside its own Docker container.

No manual starter data import is required for the base version of this project. Users and sessions are created by the application while it is running.

## Important Notes

- Do not commit your real `.env` file to GitHub
- only commit example configuration if needed
- make sure all teammates contribute using their own GitHub accounts
- use feature branches and pull requests when making changes

## Course Instructions Reference

For the full project expectations, see:

[instructions.md](./instructions.md)
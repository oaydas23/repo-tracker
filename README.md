# Flask GitHub API Integration

This is a Flask-based Python application that integrates with the GitHub API to perform various operations. It includes features such as user authentication, recording and displaying commits, managing artifacts, and interacting with a PostgreSQL database, all while utilizing Docker.

## Prerequisites

To run this application, make sure you have the following installed:

- Docker

## Installation

1. Clone the repository: `git clone <repository-url>`
2. Navigate to the project directory: `cd <project-directory>`

### GitHub Token

1. Obtain a personal access token from GitHub with the necessary permissions.

## Usage

To run the Flask application, first change the environment variables in .env file:

```
export HOST=HOSTNAME
export DATABASE=DATABASE
export USER=USER
export PASSWORD=PASSWORD
export TOKEN=TOKEN
```

Then execute the following command:

```bash
docker compose up
```

The application will start running on http://localhost:1000/.

##  Endpoints

- `/` (GET): Renders the home page.
- `/login` (GET, POST): Handles user login functionality.
- `/logout` (GET): Logs out the user and redirects to the login page.
- `/register` (GET, POST): Handles user registration functionality.
- `/artifact` (GET, POST): Manages artifacts and displays them.
- `/commit` (GET, POST): Records and displays GitHub commits.

##  Copyright

© 2023 by Resolute Building Intelligence LLC. All Rights Reserved.
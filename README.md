# CPLite: Personalized Learning for Competitive Programmers

CPLite is a platform designed to provide personalized, adaptive learning paths for competitive programmers. It integrates real-time performance analytics fetched from Codeforces, utilizes AI for tailored recommendations and progress summaries, and includes instructor-driven mentorship tools.

## Table of Contents

- [CPLite: Personalized Learning for Competitive Programmers](#cplite-personalized-learning-for-competitive-programmers)
  - [Table of Contents](#table-of-contents)
  - [How to Run](#how-to-run)
    - [Prerequisites](#prerequisites)
    - [Setup and Installation](#setup-and-installation)
    - [Running the Application](#running-the-application)
    - [Usage](#usage)
  - [Directory Structure](#directory-structure)
  - [Technology Stack](#technology-stack)
  - [Architecture](#architecture)
  - [Subsystem Overview](#subsystem-overview)
    - [Supporting Services](#supporting-services)
    - [Infrastructure](#infrastructure)
    - [Report](#report)

---

## How to Run

### Prerequisites

Before you begin, ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (Usually included with Docker Desktop)

### Setup and Installation

1.  **Clone the Repository:**

    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```

2.  **Set up environment variables**

    This project requires several environment variables for database access, authentication, and third-party integrations.

    detailed setup instructions: [Environment Variables Setup](ENVIRONMENT_SETUP.md)

3.  **Build Docker Images (Optional but Recommended):**
    While `docker-compose up` can build images, building them explicitly first can sometimes help debug issues.

    ```bash
    docker-compose build
    ```

4.  **Run the Application:**
    ```bash
    docker-compose up -d
    ```
    The `-d` flag runs the containers in detached mode (in the background).

### Running the Application

Once the containers are running (after `docker-compose up -d`), you should be able to access the application:

**Frontend:** Open your web browser and navigate to `http://localhost:3000`

To view logs for a specific service:

```bash
docker logs <service_name>
# Example: docker logs cplite-recommendation-service-1
```

To stop the application:

```bash
docker-compose down
```

To stop the application and clear the databases:

```bash
docker-compose down -v
```

### Usage

1. Access the frontend URL (e.g., http://localhost:3000).
2. Click the "Login with Google" button.
3. Authenticate via the Google OAuth flow.
4. If it's your first time, you may be prompted to set up your profile and link your Codeforces handle.
5. Explore the dashboard based on your role (Learner or Mentor).
   - Learners: View progress, recommendations, assigned tasks, summaries.
   - Mentors: View learner analytics, assign/manage tasks, override recommendations.

## Directory Structure

```bash

.
├── ai_service
│   ├── ai_service.log
│   ├── api
│   │   └── routes.py
│   ├── core
│   │   └── config.py
│   ├── database
│   │   └── connection.py
│   ├── Dockerfile
│   ├── main.py
│   ├── models
│   │   └── user_stats.py
│   ├── requirements.txt
│   ├── schemas
│   │   └── user_stats.py
│   └── services
│       ├── ai_recommendations.py
│       └── stats_summary.py
├── codeforces_service
│   ├── api
│   │   └── routes.py
│   ├── core
│   │   └── config.py
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   ├── services
│   │   └── codeforces.py
│   └── utils
│       └── messaging.py
├── cplite-frontend
│   ├── Dockerfile
│   ├── eslint.config.js
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── public
│   │   └── vite.svg
│   ├── README.md
│   ├── src
│   │   ├── App.css
│   │   ├── App.jsx
│   │   ├── assets
│   │   │   └── react.svg
│   │   ├── components
│   │   │   ├── ProfileCheck.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── contexts
│   │   │   └── AuthContext.jsx
│   │   ├── index.css
│   │   ├── main.jsx
│   │   └── pages
│   │       ├── Dashboard.jsx
│   │       ├── LearnerDashboard.jsx
│   │       ├── LearnerStats.jsx
│   │       ├── Login.jsx
│   │       ├── MentorDashboard.jsx
│   │       ├── MentorStats.jsx
│   │       └── ProfileSetup.jsx
│   └── vite.config.js
├── docker-compose.yml
├── docs
│   └── Project3_7.pdf
├── nginx
│   └── nginx.conf
├── notification-service
│   ├── controllers
│   │   ├── contest_controller.py
│   │   └── notification_controller.py
│   ├── db
│   │   └── database.py
│   ├── Dockerfile
│   ├── __init__.py
│   ├── main.py
│   ├── models
│   │   ├── contest.py
│   │   └── notification.py
│   ├── requirements.txt
│   ├── schemas
│   │   ├── contest_schema.py
│   │   └── notification_schema.py
│   ├── services
│   │   ├── consumer.py
│   │   ├── contest_service.py
│   │   └── notification_service.py
│   └── utils
│       └── messaging.py
├── README.md
├── recommendation_service
│   ├── api.py
│   ├── cron
│   │   ├── crontab.dev
│   │   ├── crontab.prod
│   │   ├── Dockerfile
│   │   ├── entrypoint.sh
│   │   └── run_job.sh
│   ├── data
│   ├── Dockerfile
│   ├── main.py
│   ├── recommendation_service_api.log
│   ├── recommendation_service.log
│   └── requirements.txt
├── task-service
│   ├── controllers
│   │   └── tasks_assigned_controller.py
│   ├── db
│   │   └── database.py
│   ├── Dockerfile
│   ├── __init__.py
│   ├── main.py
│   ├── models
│   │   └── tasks_assigned.py
│   ├── requirements.txt
│   ├── schemas
│   │   └── tasks_assigned_schema.py
│   ├── services
│   │   └── task_service.py
│   ├── task_service.log
│   └── utils
│       ├── auth_middleware_service.py
│       └── messaging.py
├── testing
│   ├── auth_tokens.csv
│   ├── locustfile.py
│   ├── notification_e2e_test.py
│   ├── notification_perf_rabbitmq_20250418_195207.json
│   ├── simple_token_collector.py
│   └── token_collector.py
├── try.json
├── try.py
└── user-service
    ├── config.py
    ├── controllers
    │   ├── auth_controller.py
    │   ├── learner_mentor_controller.py
    │   ├── service_token_controller.py
    │   └── user_controller.py
    ├── database.py
    ├── Dockerfile
    ├── main.py
    ├── models
    │   ├── __init__.py
    │   ├── learner_mentor_model.py
    │   └── user_model.py
    ├── requirements.txt
    ├── schemas
    │   ├── learner_mentor_schemas.py
    │   ├── service_token_schemas.py
    │   └── user_schemas.py
    ├── services
    │   ├── auth_service.py
    │   ├── learner_mentor_service.py
    │   └── user_service.py
    └── utils
        ├── auth_strategies.py
        └── jwt_handler.py

```

## Technology Stack

- **Backend:** Python, FastAPI
- **Frontend:** React, Vite, Tailwind CSS
- **Database:** PostgreSQL
- **Messaging:** RabbitMQ
- **AI:** Google Gemini API
- **API Gateway:** Nginx
- **Containerization:** Docker
- **Authentication:** Google OAuth2, JWT

## Architecture

CPLite is composed of several microservices, each responsible for a specific domain. Services communicate asynchronously through RabbitMQ and are exposed to clients via an Nginx API Gateway. Major microservices are implemented in the MCS(MVC) pattern including data models, controllers for routing and services for core logic for easier maintenance and independent evolution of each component.

## Subsystem Overview

1. **User & Relationship Management**

- **Role:** Handles identity, authentication, and user roles.
- **Features:** OAuth2 (Google), JWT-based auth, RBAC, mentor-learner linkages, Codeforces handle management.

2. **Task & Recommendation System**

- **Role:** Personalized learning delivery.
- **Features:** AI-generated and mentor-assigned tasks, tracked deadlines, Cron-managed workflows.

3. **LLM Summary Generator**

- **Role:** Weekly progress insights.
- **Features:** Generates summaries (rating, topics, attempts), saves to DB, triggered via scheduler.

4. **Notification System**

- **Role:** Real-time user alerts.
- **Features:** RabbitMQ-based contest/task notifications including task-of-the-day.

5. **Discussion Forum (Planned)**

- **Role:** Peer-based learning and support.
- **Planned Features:** Threads, comments, tagging, mentor moderation.

6. **Frontend Interface**

- **Role:** React-based UI for learners and mentors.
- **Features:** Dashboards, AI recs, task views, role-specific routing via context.

7. **API Gateway (Nginx)**

- **Role:** Reverse proxy and load balancer.
- **Features:** Traffic routing, rate limiting, health checks, and security headers.

8. **(Future)**

- Gamification UI (Badges, Points).
- Discussion Forum.

---

### Supporting Services

- **Codeforces Service:** Fetches Codeforces data and metadata.
- **AI Service:** Connects to Gemini API, generates recs/summaries.
- **Orchestration Service:** Cron-based task that coordinates weekly learning workflows.
- **Task Service:** Manages task lifecycle, mentor overrides, and status updates.

---

### Infrastructure

- **Docker**: Containerized services.
- **PostgreSQL**: Persistent storage.
- **RabbitMQ**: Asynchronous messaging.

---

### Report

The report can be found in the `docs` directory. It contains detailed information about the architecture, design decisions, and implementation details of the CPLite system.

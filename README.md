# Personalised Spotify Wrapped Data Pipeline

This project implements an automated data pipeline to extract, transform, and analyze personal Spotify listening history, culminating in a personalized "Spotify Wrapped" style dashboard.

The pipeline is fully containerized using Docker and orchestrated by Apache Airflow. It extracts "recently played" data from the Spotify API, stages it in a PostgreSQL database, and uses dbt (Data Build Tool) to transform the raw data into analytics-ready views.

---

## Architecture

The project leverages a modern data stack running entirely within Docker containers:

- **Orchestration**: Apache Airflow is used to schedule and manage the entire ETL workflow, from data extraction to transformation.
- **Containerization**: Docker and Docker Compose are used to define, build, and run the multi-container application (Airflow, PostgreSQL).
- **Data Storage**: A PostgreSQL database serves as both the metadata backend for Airflow and the data warehouse for storing raw and transformed Spotify data.
- **Data Transformation**: dbt (Data Build Tool) is used to execute SQL-based transformations, converting raw JSON data into clean, aggregated views and tables for analysis.
- **CI/CD (Optional)**: The project structure is compatible with CI/CD tools like GitHub Actions for automated testing and deployment.

---

## Prerequisites

- Docker Desktop installed and running.
- A Spotify account with API credentials (Client ID, Client Secret).

---

## Setup and Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-repository-name>
```


## 2. Get Spotify Credentials

Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) and create a new application.

In your app settings, add the following Redirect URI:

http://127.0.0.1:8888/callback

yaml
Copy
Edit

Note your **Client ID** and **Client Secret**.

---

## 3. Create `.env` File

Create a `.env` file in the project root to store your secrets. Populate it with the following, replacing the placeholder values:

```env
# Airflow Admin Login
AIRFLOW_ADMIN_PASSWORD=your_airflow_password

# PostgreSQL Password
PG_PASSWORD=your_db_password

# SMTP Settings for Email (using Gmail example)
SMTP_PASSWORD=your_16_character_google_app_password

# Airflow Webserver Secret Key
AIRFLOW_WEBSERVER_SECRET_KEY=your_generated_secret_key
```
Generate a secret key using:
```bash
python3 -c 'import secrets; print(secrets.token_hex(16))'
```

## 4. Build and Start the Services
Run the following command to build the Docker images and start all services in the background:

```bash
docker-compose up -d --build
```

# Set Up Airflow

## 1. Access Airflow UI
1. Go to: http://localhost:8080
2. Login with:
     * Username: admin
     * Password: your AIRFLOW_ADMIN_PASSWORD

## 2. Get Spotify Refresh Token
Run the following locally to generate your refresh token:

```bash
python3 get_refresh_token.py
```
## 3. Add Airflow Variables
In the Airflow UI:
1. Go to Admin → Variables
2. Create the following:
```pgsql
  SPOTIFY_CLIENT_ID:	Your Spotify Client ID
  SPOTIFY_CLIENT_SECRET:	Your Spotify Client Secret
  SPOTIFY_REFRESH_TOKEN:	The refresh token you generated
```
## 4. Add Airflow Connection
In the Airflow UI: Go to Admin → Connections and create a new connection:

```pgsql
Connection Id: postgres_conn  
Connection Type: Postgres  
Host: postgres  
Schema: airflow  
Login: airflow  
Password: Your PG_PASSWORD  
Port: 5432
```

# Create Initial Database Table
Connect to PostgreSQL using a client like pgAdmin:

  * Host: localhost
  * Port: 5433
  * User/DB: airflow
  * Password: your PG_PASSWORD

Run the following SQL to create the staging table:

```sql
CREATE TABLE raw_spotify_songs (
    played_at_ts TIMESTAMPTZ,
    played_at_ms BIGINT,
    track_id VARCHAR(255),
    track_name TEXT,
    artist_id VARCHAR(255),
    artist_name TEXT,
    album_id VARCHAR(255),
    album_name TEXT,
    duration_ms INT,
    raw_json JSONB,
    PRIMARY KEY (track_id, played_at_ts)
);
```
# Usage
## Run the Data Pipeline
1. In the Airflow UI, find the spotify_pipeline DAG.
2. Enable it using the toggle switch.
3. Manually trigger it using the ▶️ play button.
4. This will extract your recent listening history and run the dbt transformations.

## Generate and Email the Dashboard
1. Once spotify_pipeline has completed successfully, find the email_spotify_dashboard DAG.
2. Enable and trigger it.
3. This will query the transformed data, generate the dashboard image, and email it to you.

# Project Structure
```bash
spotify_wrapped_project/
├── dags/
│   ├── __init__.py
│   ├── songs_dag.py
│   └── email_dashboard_dag.py
├── dbt_project/ 
│   ├── models/
│   ├── macros/
│   └── dbt_project.yml
├── include/
│   ├── __init__.py
│   └── spotify_utils.py
├── .env
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

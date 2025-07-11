from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# Import your custom functions from the 'include' directory
from include.spotify_utils import refresh_spotify_token, get_spotify_songs, load_songs_to_db

# Define default arguments for the DAG
default_args = {
    'owner': 'Thomas Trainor-Gilham',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id='spotify_pipeline',
    default_args=default_args,
    description='A DAG to extract Spotify data and run dbt.',
    schedule_interval=timedelta(hours=3),
    start_date=days_ago(1),
    catchup=False,
) as dag:

    # Task to refresh the Spotify API token
    task_refresh_token = PythonOperator(
        task_id='refresh_spotify_token',
        python_callable=refresh_spotify_token,
    )

    # Task to get recently played songs
    task_get_songs = PythonOperator(
        task_id='get_spotify_songs',
        python_callable=get_spotify_songs,
        # Pass the Airflow connection ID to the function
        op_kwargs={'postgres_conn_id': 'postgres_conn'},
    )

    # Task to load song data into the database
    task_load_songs = PythonOperator(
        task_id='load_songs_to_db',
        python_callable=load_songs_to_db,
        op_kwargs={'postgres_conn_id': 'postgres_conn'},
    )

    # Task to run your dbt models
    task_dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command="""
        cd /opt/airflow/dbt_project && dbt run --vars '{ "start_date": "{{ data_interval_start.strftime('%Y-%m-%d') }}", "end_date": "{{ data_interval_end.strftime('%Y-%m-%d') }}" }'
        """,
    )

    # Define the task pipeline
    task_refresh_token >> task_get_songs >> task_load_songs >> task_dbt_run

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

# Import the new function
from include.spotify_utils import generate_dashboard_image

# Define a constant for the image path to ensure consistency
IMAGE_PATH = "/opt/airflow/dags/temp/spotify_wrapped.png"

default_args = {
    'owner': 'Your Name', # Change this
    'depends_on_past': False,
    'email_on_failure': True, # Set to True to get error emails
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id='email_spotify_dashboard',
    default_args=default_args,
    description='A DAG to generate and email a weekly Spotify dashboard.',
    schedule_interval=timedelta(weeks=1),
    start_date=days_ago(7),
    catchup=False,
) as dag:

    generate_dashboard_task = PythonOperator(
        task_id='generate_dashboard',
        python_callable=generate_dashboard_image,
        op_kwargs={
            'postgres_conn_id': 'postgres_conn', # Your Airflow connection ID
            'output_path': IMAGE_PATH,
        }
    )

    send_email_task = EmailOperator(
        task_id='send_email_dashboard',
        to='thomastrainorgilham@gmail.com', # Change this to your email
        subject='Your Weekly Spotify Wrapped!',
        html_content="""
        <h2>Hey There!</h2>
        <p>Here is your Spotify Wrapped for the past week.</p>
        <img src="cid:spotify_wrapped.png">
        """,
        files=[IMAGE_PATH], # Attach the generated file
    )

    generate_dashboard_task >> send_email_task
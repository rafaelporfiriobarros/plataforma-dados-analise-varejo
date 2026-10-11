from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    "mercado_analytics_monthly",
    start_date=datetime(2026, 1, 1),
    schedule=None, 
    catchup=False,
    default_args=default_args,
    tags=["portfolio", "analytics", "monthly"],
) as dag:
    health = BashOperator(
        task_id="check_postgres",
        bash_command="pg_isready -h postgres -p 5432 -U postgres -d mercado_analytics",
    )
    pipeline = BashOperator(
        task_id="run_incremental_pipeline",
        bash_command=(
            "cd /opt/project && PYTHONPATH=src LOAD_TO_POSTGRES=true "
            "INCREMENTAL_LOAD=true python run_pipeline.py"
        ),
    )
    health >> pipeline

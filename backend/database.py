from google.cloud import bigquery
from backend.config import settings

client = bigquery.Client(project=settings.PROJECT_ID)

def execute_query(query, params=None):
    """Executes a BigQuery query."""
    job = client.query(query, job_config=bigquery.QueryJobConfig(query_parameters=params or []))
    return job.result()

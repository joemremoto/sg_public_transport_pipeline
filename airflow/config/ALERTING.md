# Airflow Alerting Configuration

## Email Configuration (Optional)

To enable email alerts for DAG failures, update the following in `docker-compose.yml`:

```yaml
AIRFLOW__SMTP__SMTP_HOST: smtp.gmail.com
AIRFLOW__SMTP__SMTP_STARTTLS: 'true'
AIRFLOW__SMTP__SMTP_SSL: 'false'
AIRFLOW__SMTP__SMTP_USER: your-email@gmail.com
AIRFLOW__SMTP__SMTP_PASSWORD: your-app-password
AIRFLOW__SMTP__SMTP_PORT: 587
AIRFLOW__SMTP__SMTP_MAIL_FROM: your-email@gmail.com
```

Then in your DAG's `default_args`, enable:

```python
'email': ['your-email@example.com'],
'email_on_failure': True,
'email_on_retry': False,
```

## Slack Webhook (Recommended)

For Slack notifications, add this to your DAG:

```python
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

def task_fail_slack_alert(context):
    slack_msg = f"""
    :red_circle: Task Failed.
    *Task*: {context.get('task_instance').task_id}
    *Dag*: {context.get('task_instance').dag_id}
    *Execution Time*: {context.get('execution_date')}
    *Log Url*: {context.get('task_instance').log_url}
    """
    
    failed_alert = SlackWebhookOperator(
        task_id='slack_alert',
        http_conn_id='slack_webhook',
        message=slack_msg,
    )
    return failed_alert.execute(context=context)

# Then add to default_args:
'on_failure_callback': task_fail_slack_alert,
```

## Current Configuration

For this project, alerting is configured via DAG default_args:
- Retries: 2 attempts with 5-minute delay
- Execution timeout: 2 hours
- Email alerts: Disabled by default (can be enabled per environment)
- Log retention: Available in Airflow UI for 30 days

## Monitoring in Airflow UI

Access the Airflow UI at http://localhost:8080 to:
- View DAG run history
- Check task logs
- Monitor execution times
- Set up manual alerts
- View task dependencies

## Production Recommendations

For production deployments:
1. Enable email or Slack notifications
2. Set up external monitoring (Datadog, Grafana)
3. Configure alerting for:
   - DAG failures
   - Tasks taking longer than expected
   - Data quality test failures
   - BigQuery quota issues
4. Set up log aggregation (Cloud Logging, ELK stack)

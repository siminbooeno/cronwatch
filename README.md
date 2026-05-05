# cronwatch

Lightweight cron job monitor that alerts on missed or failed executions via webhook or email.

## Installation

```bash
pip install cronwatch
```

## Usage

Wrap your cron command with `cronwatch` to start monitoring it:

```bash
cronwatch --name "daily-backup" --schedule "0 2 * * *" -- /usr/local/bin/backup.sh
```

Or configure jobs in a YAML file:

```yaml
# cronwatch.yml
jobs:
  daily-backup:
    schedule: "0 2 * * *"
    command: /usr/local/bin/backup.sh
    alert:
      webhook: https://hooks.slack.com/services/your/webhook/url
      email: ops@example.com
    grace_period: 10m
```

Then run:

```bash
cronwatch --config cronwatch.yml
```

cronwatch will send an alert if a job fails, exits with a non-zero status, or does not start within the configured grace period.

## Alerts

Supported notification channels:

- **Webhook** — POST a JSON payload to any URL (Slack, PagerDuty, custom endpoints)
- **Email** — SMTP-based email alerts

## Configuration

| Option | Description | Default |
|---|---|---|
| `schedule` | Cron expression for expected run time | required |
| `grace_period` | How long to wait before alerting on a missed run | `5m` |
| `retries` | Number of retries before marking a job as failed | `0` |

## License

MIT
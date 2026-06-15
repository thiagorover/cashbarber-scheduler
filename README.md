# cashbarber-scheduler

Automated barbershop appointment scheduler built with Python and GitHub Actions, with Telegram notifications.

## The problem

Getting a Saturday appointment at my barbershop is surprisingly competitive. The schedule opens every Sunday at midnight for the following Saturday, and by the time I remembered to book, the best slots were already gone.

So I automated it.

## How it works

Every Sunday at 00:01 (BRT), a scheduled trigger fires, logs into the barbershop platform, checks if an appointment already exists for the upcoming Saturday, and books one if it doesn't. Either way, I get a Telegram notification telling me what happened. The whole thing runs in under 15 seconds.

```
[cron-job.org triggers at 00:01 BRT]
         |
[Dispatches the GitHub Actions workflow]
         |
[Logs in via API -> gets a fresh session token]
         |
[Checks for an existing appointment]
         |
   +-----------+-----------+
   |                       |
[Already booked]      [No appointment yet]
   |                       |
[Telegram: confirms]  [Tries to book preferred time]
                           |
                  +--------+--------+
                  |                 |
            [Success]         [Slot unavailable]
                  |                 |
          [Telegram: booked] [Telegram: alert + site link]
```

## Stack

- **Python 3.13** — core script
- **requests** — HTTP calls to the barbershop and Telegram APIs
- **GitHub Actions** — workflow execution environment
- **cron-job.org** — external scheduler that triggers the workflow reliably
- **Telegram Bot API** — notifications
- **GitHub Secrets** — secure credential storage

## Why an external scheduler?

GitHub Actions' native `cron` is best-effort and can be delayed by several minutes under load. For this use case timing is critical, since the schedule opens at an exact moment and slots fill fast, so an external trigger from cron-job.org fires the workflow precisely at 00:01 BRT via the GitHub API.

## Configuration

All sensitive data is stored as GitHub Secrets. No credentials are hardcoded.

| Secret | Description |
|---|---|
| `CASHBARBER_EMAIL` | Account email |
| `CASHBARBER_PASSWORD` | Account password |
| `CASHBARBER_TENANT` | Barbershop identifier in the platform |
| `CASHBARBER_BRANCH_ID` | Branch ID |
| `CASHBARBER_BARBER_ID` | Barber ID |
| `CASHBARBER_SERVICES` | Comma-separated service IDs |
| `CASHBARBER_START_TIME` | Appointment start time (HH:MM) |
| `CASHBARBER_END_TIME` | Appointment end time (HH:MM) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token for notifications |
| `TELEGRAM_CHAT_ID` | Telegram chat ID that receives the messages |

## Key decisions

**No browser automation.** Instead of Playwright or Puppeteer, the script calls the API directly, which is lighter, faster, and more reliable.

**Fresh token on every run.** Rather than storing a static auth token that would eventually expire, the script logs in before each execution and uses the session token returned in the response header. This removed the need for any manual token renewal.

**Safe by design.** Before attempting to book, the script always checks for existing appointments. If one already exists, it exits without making any API call to create a new one.

**Resilient network handling.** Every external request is wrapped in error handling. Failures are classified by severity: a login or booking failure aborts the run, while a notification failure is logged and ignored, since it should never bring down the main task.

**Human-readable notifications.** Dates returned by the API in machine format are converted to a friendly format before being sent to Telegram.

## Notifications

The script reports back through Telegram in every scenario:

- Appointment successfully booked
- An appointment already existed for the target date
- Preferred time unavailable (with a link to pick another slot manually)
- Login, connection, or scheduling errors

## Running locally

Install dependencies (same on every platform):

```bash
pip install requests
```

Set the environment variables, then run the script.

**Linux / macOS:**

```bash
export CASHBARBER_EMAIL=your@email.com
export CASHBARBER_PASSWORD=yourpassword
export CASHBARBER_TENANT=yourtenant
export CASHBARBER_BRANCH_ID=0000
export CASHBARBER_BARBER_ID=0000
export CASHBARBER_SERVICES=00000,00000
export CASHBARBER_START_TIME=10:20
export CASHBARBER_END_TIME=11:20
export TELEGRAM_BOT_TOKEN=your_bot_token
export TELEGRAM_CHAT_ID=your_chat_id

python src/agendar.py
```

**Windows PowerShell:**

```powershell
$env:CASHBARBER_EMAIL="your@email.com"
$env:CASHBARBER_PASSWORD="yourpassword"
$env:CASHBARBER_TENANT="yourtenant"
$env:CASHBARBER_BRANCH_ID="0000"
$env:CASHBARBER_BARBER_ID="0000"
$env:CASHBARBER_SERVICES="00000,00000"
$env:CASHBARBER_START_TIME="10:20"
$env:CASHBARBER_END_TIME="11:20"
$env:TELEGRAM_BOT_TOKEN="your_bot_token"
$env:TELEGRAM_CHAT_ID="your_chat_id"

python src/agendar.py
```

## Author

Thiago Henrique Rover
[LinkedIn](https://www.linkedin.com/in/thiago-henrique-rover-97b8b3ba/) · [GitHub](https://github.com/thiagorover)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

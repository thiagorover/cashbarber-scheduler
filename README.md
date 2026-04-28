# cashbarber-scheduler

Automated barbershop appointment scheduler built with Python and GitHub Actions.

## The problem

Getting a Saturday appointment at my barbershop is surprisingly competitive. The schedule opens every Sunday at midnight for the following Saturday — and by the time I remembered to book, the best slots were already gone.

So I automated it.

## How it works

Every Sunday at 00:01 (BRT), a GitHub Actions workflow wakes up, logs into the barbershop platform, checks if an appointment already exists for the upcoming Saturday, and books one if it doesn't. The whole thing runs in under 15 seconds.

```
[GitHub Actions triggers at 00:01 BRT]
         ↓
[Logs in via API → gets a fresh token]
         ↓
[Checks for existing appointments]
         ↓
[Books if none found → exits silently if already scheduled]
```

## Stack

- **Python 3.13** — core script
- **requests** — HTTP calls to the barbershop API
- **GitHub Actions** — scheduling and execution
- **GitHub Secrets** — secure credential storage

## Configuration

All sensitive data is stored as GitHub Secrets. No credentials are hardcoded.

| Secret | Description |
|---|---|
| `CASHBARBER_EMAIL` | Account email |
| `CASHBARBER_PASSWORD` | Account password |
| `CASHBARBER_TENANT` | Barbershop identifier in the platform |
| `CASHBARBER_BRANCH_ID` | Branch ID |
| `CASHBARBER_USER_ID` | User ID |
| `CASHBARBER_SERVICES` | Comma-separated service IDs |
| `CASHBARBER_START_TIME` | Appointment start time (HH:MM) |
| `CASHBARBER_END_TIME` | Appointment end time (HH:MM) |

## Key decisions

**No browser automation.** Instead of Playwright or Puppeteer, the script calls the API directly — lighter, faster, and more reliable.

**Fresh token on every run.** Rather than storing a static auth token that would eventually expire, the script logs in before each execution and uses the session token returned in the response header.

**Safe by design.** Before attempting to book, the script always checks for existing appointments. If one already exists, it exits without making any API calls to create a new one.

## Running locally

```bash
pip install requests

export CASHBARBER_EMAIL=your@email.com
export CASHBARBER_PASSWORD=yourpassword
export CASHBARBER_TENANT=yourtenant
export CASHBARBER_BRANCH_ID=0000
export CASHBARBER_USER_ID=0000
export CASHBARBER_SERVICES=00000,00000
export CASHBARBER_START_TIME=11:00
export CASHBARBER_END_TIME=12:00

python src/agendar.py
```

## License

MIT

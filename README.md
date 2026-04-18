# 🔐 Pwned Robot

A production-ready Telegram bot that checks whether email addresses have been exposed in known data breaches, powered by the [Have I Been Pwned](https://haveibeenpwned.com) (HIBP) API v3.

Premium subscribers receive **daily automatic monitoring** with instant Telegram alerts when a new breach is detected for their accounts. The bot supports **Italian and English** — each user can choose their preferred language with `/language`.

Stay updated on newly disclosed breaches: [@HIBP_updates](https://t.me/HIBP_updates)

---

## Features

| | Free | Premium |
|---|:---:|:---:|
| Breach & paste check | ✅ | ✅ |
| First 5 breaches listed | ✅ | ✅ |
| Full breach list (unlimited) | — | ✅ |
| Exposed data categories per breach | — | ✅ |
| Paste source details | — | ✅ |
| Daily email monitoring (up to 5 emails) | — | ✅ |
| Instant alert on new breach | — | ✅ |
| Higher rate limit (30 req/min vs 5) | — | ✅ |
| Italian / English UI | ✅ | ✅ |

---

## Commands

### Public

| Command | Description |
|---|---|
| `/start` | Welcome menu with quick-action buttons |
| `/check <email>` | Check an email for breaches and pastes |
| `/stats` | Personal check history and statistics |
| `/subscribe` | Premium plan info + Stars payment |
| `/updates` | Open the breach news Telegram channel |
| `/language` | Switch between Italian and English |
| `/privacy` | Privacy policy |
| `/help` | Full command reference |
| `/cancel` | Cancel current operation |

### Premium

| Command | Description |
|---|---|
| `/monitor <email>` | Add an email to daily automatic monitoring |
| `/unmonitor <email>` | Remove an email from monitoring |
| `/mymonitors` | List all actively monitored emails |

### Admin

| Command | Description |
|---|---|
| `/adminstats` | Global bot statistics |
| `/setpremium <telegram_id>` | Grant Premium to a user |
| `/revokepremium <telegram_id>` | Revoke Premium from a user |

---

## Architecture

```
pwned_robot/
├── main.py          # Entry point, handler registration, job scheduler
├── config.py        # Pydantic v2 settings loaded from .env
├── models.py        # SQLAlchemy ORM models (6 tables)
├── database.py      # Async DB manager — CRUD + monitoring operations
├── handlers.py      # Telegram command, callback, and payment handlers
├── hibp_client.py   # Async HIBP API v3 client with Redis caching
├── scheduler.py     # Daily monitoring job (08:00 UTC)
├── security.py      # Input validation, encryption, audit logging
├── strings.py       # All UI strings — Italian and English
├── database.sql     # MySQL DDL — create tables and indexes
├── requirements.txt
└── setup_service.sh # Automated Linux systemd installer
```

### Tech Stack

| Layer | Technology |
|---|---|
| Bot framework | python-telegram-bot 21.5 (async) |
| HTTP client | aiohttp 3.10 |
| Database | MySQL 5.7+ / MariaDB 10.3+ via SQLAlchemy 2.0 (async) |
| MySQL driver | aiomysql 0.2 (async) |
| Cache | Redis — breach results cached for 24 h |
| Job scheduler | APScheduler (bundled via PTB `[all]`) |
| Settings | Pydantic v2 / pydantic-settings |
| Encryption | Fernet (AES-128) via `cryptography` |
| i18n | `strings.py` — `t(key, lang, **kwargs)` helper |

### Data Flow

```
Telegram User
      │
      ▼
handlers.py ──→ security.py (validate + sanitize input)
      │
      ▼
database.py ──→ rate limit check
      │
      ▼
hibp_client.py ──→ Redis cache (hit?) ──→ HIBP API v3
      │
      ▼
database.py ──→ persist result + audit log
      │
      ▼
Telegram User  (strings.py → response in user's language)
```

---

## Database Schema

Six tables, all `InnoDB` with foreign-key constraints and covering indexes.

| Table | Purpose |
|---|---|
| `users` | Telegram profiles, language preference, premium status |
| `breach_checks` | Every email check performed |
| `breach_details` | Breach metadata per check result |
| `monitored_emails` | Premium daily monitoring registrations |
| `audit_logs` | Immutable security and compliance audit trail |
| `rate_limit_records` | Sliding-window rate limiting per user/endpoint |

### ER Diagram

```
users (1)──────────(N) breach_checks (1)──(N) breach_details
  │
  ├──────────────(N) monitored_emails
  ├──────────────(N) audit_logs
  └──────────────(N) rate_limit_records
```

---

## Setup

### Prerequisites

- Python 3.11+
- MySQL 5.7+ or MariaDB 10.3+
- Redis 6+
- [HIBP API key](https://haveibeenpwned.com/API/Key)
- Telegram bot token from [@BotFather](https://t.me/BotFather)

### Install

```bash
git clone https://github.com/garboh/pwned_robot.git
cd pwned_robot

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
nano .env
```

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `TELEGRAM_TOKEN` | ✅ | — | Bot token from BotFather |
| `TELEGRAM_ADMIN_IDS` | ✅ | — | Comma-separated admin Telegram IDs (get yours from [@userinfobot](https://t.me/userinfobot)) |
| `DB_HOST` / `DB_PORT` | ✅ | `localhost` / `3306` | MySQL host and port |
| `DB_USER` / `DB_PASSWORD` / `DB_NAME` | ✅ | — | MySQL credentials |
| `HIBP_API_KEY` | ✅ | — | HaveIBeenPwned API key |
| `REDIS_HOST` / `REDIS_PORT` | | `localhost` / `6379` | Redis connection |
| `MAX_REQUESTS_PER_MINUTE` | | `5` | Free-tier rate limit |
| `ENABLE_CACHE` | | `true` | Enable Redis caching |
| `CACHE_EXPIRATION` | | `86400` | Cache TTL in seconds |
| `WEBHOOK_URL` | | — | Enables webhook mode instead of long-polling |

> ⚠️ Never commit `.env` to version control.

### Create Database

```bash
mysql -u root -p < database.sql
```

### Run

```bash
python main.py
```

---

## Deploy as a System Service (Linux)

`setup_service.sh` installs the bot as a **systemd** service that starts on boot and restarts on failure:

```bash
sudo bash setup_service.sh
```

Edit the variables at the top of the script to match your server paths before running.

```bash
sudo journalctl -u pwned_robot -f        # live logs
sudo systemctl restart pwned_robot       # restart
sudo systemctl status  pwned_robot       # status
```

---

## Premium Subscription

Premium is purchased directly inside Telegram via **Telegram Stars** — no external payment provider needed.

**Flow:**
1. User sends `/subscribe`
2. Bot shows benefits + **⭐ Subscribe with Stars** button
3. User pays **500 Stars** (~$6.50) for one year
4. Bot activates Premium automatically on successful payment

Admins can also grant/revoke Premium manually:

```
/setpremium <telegram_id>
/revokepremium <telegram_id>
```

**What Premium unlocks:**
- Daily monitoring of up to 5 email addresses (checked at 08:00 UTC, notified only on new breaches)
- Full breach list with exposed data categories and affected account counts
- Paste source details
- Rate limit raised to 30 req/min

**Stay informed:** follow [@HIBP_updates](https://t.me/HIBP_updates) for real-time breach news.

---

## Internationalisation

All user-facing text lives in [`strings.py`](strings.py) under two top-level keys: `"it"` and `"en"`.

```python
from strings import t

t("welcome", lang="it", name=" Francesco", badge="⭐")
t("check_no_breach", lang="en", email="user@example.com")
```

To add a new language, add a matching key block to `STRINGS` in `strings.py` — no changes to handlers required.

---

## Security

| Protection | Implementation |
|---|---|
| SQL injection | SQLAlchemy ORM — parameterized queries only |
| XSS | `html.escape()` on all user input before rendering |
| Input validation | RFC 5322 email regex + injection pattern detection |
| Hardcoded secrets | All credentials loaded from `.env` via Pydantic |
| Access control | `@require_admin` decorator validates `TELEGRAM_ADMIN_IDS` |
| Rate limiting | Sliding-window via `rate_limit_records` table |
| Sensitive data | Fernet (AES-128) encryption available for fields at rest |
| Audit trail | Every sensitive action logged to `audit_logs` |
| Suspicious activity | Automatic detection and logging of injection attempts |

---

## Monitoring & Logs

```bash
# Live log stream
tail -f pwned_robot.log

# Errors only
grep ERROR pwned_robot.log

# Key DB metrics
mysql -u pwned_user -p pwned_robot -e "
  SELECT COUNT(*) AS active_users  FROM users          WHERE active = 1;
  SELECT COUNT(*) AS premium_users FROM users          WHERE premium = 1;
  SELECT COUNT(*) AS total_checks  FROM breach_checks;
  SELECT COUNT(*) AS monitored     FROM monitored_emails WHERE active = 1;
"
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m "feat: add my feature"`
4. Push and open a Pull Request

---

## License

GNU General Public License v2.0 — see [LICENSE](LICENSE) for details.

---

## Disclaimer

This bot queries data from HaveIBeenPwned.com for informational purposes only. We are not responsible for the accuracy of the breach data or for any consequences arising from its use. Always handle user data responsibly and in compliance with applicable privacy laws.

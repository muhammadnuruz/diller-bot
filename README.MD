# Diller Bot

**Description:**
This project is a telegram bot with an integrated system with Sales Doctor. The bot manages users, dealers, orders, public broadcasts, and supports internal queries for product search.

## Features

* User and dealer management
* Cart and order system
* Subscription and admin permissions
* View orders
* Broadcast and forward messages
* Inline query for product search and sending

## Tech Stack

* Python 3.11+
* Aiogram
* PostgreSQL
* SQLAlchemy / Alembic
* Redis (for FSM / caching)

## Installation

1. Clone repository:

```bash
git clone https://github.com/muhammadnuruz/diller-bot.git
cd diller-bot
```

2. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables:

```bash
DRIVER=postgresql+asyncpg
TOKEN=
DB_NAME=
DB_USER=_
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

## Database

### Create migration

```bash
alembic revision --autogenerate -m "add new model"
```

### Apply migration

```bash
alembic upgrade head
```

## Usage

### Run bot

```bash
python bot/main.py
```

### Run backend

```bash
uvicorn main:app --reload
```

## For Developers

* FSM states are defined in `bot/states.py`.
* Broadcasts are managed via `active_broadcasts` dictionary.
* Inline queries for product search are in `bot/handlers/inline.py`.
* Admin commands: broadcast, forward, statistics.

## For HR / Non-Technical

* Telegram bot allows users to order products, view order history, and receive broadcast messages.
* Admins can send messages to all users, track delivery stats, and manage user permissions.
* Dealers can integrate API credentials to access product categories and orders.

## Contribution

1. Fork the repository
2. Create a branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m "Description"`
4. Push to the branch: `git push origin feature-name`
5. Create a Pull Request

## License

MIT License © \[Muhammad Nur]

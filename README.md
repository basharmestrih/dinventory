# Telegram Digital Products Bot

Structured Telegram bot built with `aiogram` for selling digital products.

## Features

- Arabic-only translations for now
- Main menu with:
  - Buy
  - Profile
  - Purchase history
  - Wallet
  - Support
  - API link
- Clean modular router structure

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and add your bot token.
4. Run the bot:

```bash
python main.py
```

## Payment Webhooks

Enable the local webhook server in `.env`:

```bash
ZENO_WEBHOOK_ENABLED=true
ZENO_WEBHOOK_HOST=0.0.0.0
ZENO_WEBHOOK_PORT=8080
```

Point ngrok at the port and configure Zeno to send checkout events to:

```text
https://your-ngrok-domain.ngrok-free.app/webhooks/zeno
```

Configure Fawaterk to send invoice events to:

```text
https://your-ngrok-domain.ngrok-free.app/webhooks/fawaterk
```

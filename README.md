# 🤖 HET - Your Smart Telegram Bot

Welcome to **HET**, a powerful and easy-to-use Telegram bot platform. Whether you're a developer or just starting out, this guide will help you get your bot up and running in minutes!

---

## 🌟 What is HET?
HET is a specialized system designed to run Telegram bots efficiently. It handles:
- **Fast Messages**: Responds instantly to users.
- **Multiple Languages**: Supports English, Russian, and Uzbek out of the box.
- **Scheduled Tasks**: Can perform actions at specific times automatically.
- **Easy Setup**: Designed to run anywhere using Docker.

---

## 🚀 Quick Start Guide

Setting up HET is as easy as 1-2-3! Follow these steps to get started.

### Step 1: Get the Code
Clone this project to your computer:
```bash
git clone https://github.com/ystdn-exp/het_uz_telegram_bot.git
cd het_uz_telegram_bot
```

### Step 2: Setup your Settings (.env)
We use a special file called `.env` to store your bot's "secrets" (like passwords and tokens).

1.  **Copy the template**:
    ```bash
    cp .env.example .env
    ```
2.  **Open `.env`** in any text editor.
3.  **Add your Bot Token**: Get one from [@BotFather](https://t.me/botfather) and paste it next to `TELEGRAM_BOT_TOKEN=`.
4.  **Add Secret Keys**: For `SECRET_KEY` and `WEBHOOK_SECRET_KEY`, just type any random long string of letters and numbers.

### Step 3: Setup Connection (ngrok)
To allow Telegram to talk to your bot while you are developing it on your computer, we use a tool called **ngrok**.

1.  **Sign up**: Go to [ngrok.com](https://ngrok.com) and create a free account.
2.  **Get your Token**: Once logged in, go to the [Your Authtoken](https://dashboard.ngrok.com/get-started/your-authtoken) page.
3.  **Copy the code**: Copy your "Authtoken".
4.  **Paste it**: In your `.env` file, paste it next to `NGROK_AUTHTOKEN=`.

### Step 4: Run the Bot!
Choose your preferred mode:

#### A. Polling Mode (Easiest for Local Development)
No ngrok required! Use this to test the bot quickly.
-   **Linux/Mac**: `make polling-up`
-   **Windows**: `docker-compose -f docker-compose.polling.yaml up -d`

#### B. Webhook Mode (Advanced)
Requires ngrok properly configured in `.env`.
-   **Linux/Mac**: `make dev-up`
-   **Windows**: `docker-compose -f docker-compose.dev.yaml up -d`

Wait a few seconds... and your bot is alive! 🎉

---

## 💻 Commands Reference

If you are on **Windows** (or don't have `make` installed), use these direct `docker-compose` commands:

| Action | Linux/Mac (Make) | Windows (Direct Command) |
| :--- | :--- | :--- |
| **Start (Polling)** | `make polling-up` | `docker-compose -f docker-compose.polling.yaml up -d` |
| **Stop (Polling)** | `make polling-down` | `docker-compose -f docker-compose.polling.yaml down` |
| **Restart (Polling)** | `make polling-restart` | `docker-compose -f docker-compose.polling.yaml down && docker-compose -f docker-compose.polling.yaml up -d` |
| **Start (Dev/Webhook)** | `make dev-up` | `docker-compose -f docker-compose.dev.yaml up -d` |
| **Stop (Dev/Webhook)** | `make dev-down` | `docker-compose -f docker-compose.dev.yaml down` |
| **Restart (Dev/Webhook)** | `make dev-restart` | `docker-compose -f docker-compose.dev.yaml down && docker-compose -f docker-compose.dev.yaml up -d` |

> [!TIP]
> **Windows Users**: If you see "file not found" errors when running containers, ensure your files have Linux line endings (LF). You can fix this by running:
> `git add --renormalize .`

---

## 🛠 Troubleshooting
-   **Bot not responding?** Check your `TELEGRAM_BOT_TOKEN` in the `.env` file.
-   **Ngrok error?** Make sure your `NGROK_AUTHTOKEN` is correct.
-   **Still stuck?** Try restarting everything. On Windows: `docker-compose -f docker-compose.polling.yaml down && docker-compose -f docker-compose.polling.yaml up -d`

---

## 🏗 For Developers
HET is built with modern tech:
- **FastAPI**: The web engine.
- **Aiogram 3**: The Telegram bot framework.
- **PostgreSQL**: The database for saving data.
- **Redis**: For fast temporary storage.

For more technical details, check out the `src/` folder and `docker-compose` files.

# 🚀 Deploying Calm Space to Railway

## Prerequisites

- A [Railway](https://railway.app) account (free tier works)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Git installed locally

---

## Step 1 — Create a Telegram Bot

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **BOT_TOKEN** it gives you (looks like `123456789:ABCDef...`)
4. Keep BotFather open — you'll need it again in Step 5

---

## Step 2 — Push the Code to GitHub (or use Railway CLI)

### Option A — GitHub (recommended)

```bash
cd Lesson_3_mini_apps
git init
git add .
git commit -m "Initial commit — Calm Space mini app"
```

Create a new **private** repository on GitHub, then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/calm-space.git
git push -u origin main
```

### Option B — Railway CLI (no GitHub needed)

```bash
npm install -g @railway/cli   # or: brew install railway
railway login
railway init                  # creates a new project
railway up                    # deploys current directory
```

---

## Step 3 — Create a Railway Project

1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click **New Project → Deploy from GitHub repo** (Option A)  
   *or* your project is already created if you used `railway init` (Option B)
3. Select the repository

Railway will detect `requirements.txt` automatically via **Nixpacks** and install dependencies.

---

## Step 4 — Set Environment Variables

In the Railway dashboard, open your service → **Variables** tab → **Raw Editor**, and paste:

```dotenv
BOT_TOKEN=your_bot_token_here
APP_BASE_URL=https://your-app.up.railway.app
DATABASE_URL=sqlite:///./anxiety_app.db
INIT_DATA_MAX_AGE=3600
SKIP_INIT_DATA_VALIDATION=false
```

> ⚠️ Leave `APP_BASE_URL` as a placeholder for now — you'll fill it in after Railway assigns a domain (Step 5).

**Variable descriptions:**

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Token from @BotFather |
| `APP_BASE_URL` | ✅ | Your Railway public URL (see Step 5) |
| `DATABASE_URL` | optional | Defaults to SQLite. Use a Postgres URL for Railway's managed DB |
| `INIT_DATA_MAX_AGE` | optional | Seconds before initData expires (default: 3600) |
| `SKIP_INIT_DATA_VALIDATION` | optional | `false` in production, `true` for local dev only |

---

## Step 5 — Assign a Public Domain

1. In Railway: open your service → **Settings** → **Networking**
2. Click **Generate Domain** → Railway gives you a URL like  
   `https://calm-space-production-abc1.up.railway.app`
3. Copy that URL
4. Go back to **Variables** and update:
   ```
   APP_BASE_URL=https://calm-space-production-abc1.up.railway.app
   ```
   Railway will automatically redeploy with the new value.

---

## Step 6 — Register the WebApp URL with Telegram

Back in **@BotFather**:

```
/setmenubutton
```

1. Select your bot
2. Enter the URL: `https://calm-space-production-abc1.up.railway.app/app`
3. Enter the button text: `🌿 Open Calm Space`

This adds a persistent **Menu Button** in every chat with the bot.

> Optionally also run `/setdomain` and enter the same base URL so Telegram trusts it as a WebApp origin.

---

## Step 7 — Verify the Deployment

```bash
# Health check
curl https://calm-space-production-abc1.up.railway.app/health
# Expected: {"status":"ok","timestamp":"..."}

# Frontend
curl -I https://calm-space-production-abc1.up.railway.app/
# Expected: HTTP/2 200
```

Or simply open the URL in a browser — you should see the Calm Space UI.

---

## Step 8 — Test End-to-End in Telegram

1. Open your bot in Telegram
2. Send `/start`
3. Tap **🌿 Open Calm Space**
4. The Mini App should open, load your user, and all 5 screens should work

---

## Upgrading to Postgres (optional but recommended for production)

1. In Railway dashboard: **New** → **Database** → **PostgreSQL**
2. Once provisioned, click the Postgres service → **Variables** → copy `DATABASE_URL`
3. Set it as `DATABASE_URL` on your app service
4. Redeploy — SQLModel will auto-create all tables on startup

---

## Redeployment

Every `git push` to `main` triggers an automatic redeploy.  
Manual redeploy: Railway dashboard → **Deploy** → **Redeploy**.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Bot doesn't respond | Check `BOT_TOKEN` is set correctly in Variables |
| WebApp opens blank | Verify `APP_BASE_URL` ends without a trailing slash |
| 401 on all API calls | `SKIP_INIT_DATA_VALIDATION` must be `false` in prod; open the app through Telegram, not a browser |
| DB resets on redeploy | Switch from SQLite to Railway Postgres (SQLite is ephemeral on Railway's filesystem) |
| Port errors | Don't hardcode a port — Railway injects `$PORT` automatically |

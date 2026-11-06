# discord_ig_bridge

Two-way relay between one Instagram group chat and one Discord channel.

- **IG → Discord:** polls the IG chat every 15–21.5s (random, capped at 220/hr) and reposts through a webhook with the sender's IG name + profile pic.
- **Discord → IG:** a burner IG account sends `[name] message` into the group chat.

> Uses `instagrapi` (unofficial Instagram API). Use a **burner** IG account — automation can get it flagged.

## Setup

### 1. Discord
1. Developer Portal → create a bot → enable **Message Content Intent** → invite it to your server.
2. Channel → Settings → Integrations → **Create Webhook** → copy URL.
3. Developer Mode on → right-click the channel → **Copy Channel ID**.

### 2. Config
Copy `.env.example` to `.env` and fill in everything except `IG_THREAD_ID`.

### 3. Install

**Windows (PowerShell)**
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux (dudbox)**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Find the IG thread ID
```bash
python find_thread.py
```
Enter any verification code Instagram asks for. Copy the group chat's ID into `IG_THREAD_ID` in `.env`.

### 5. Run
```bash
python relay.py
```

## Moving to dudbox
Copy `.env` and `ig_session.json` over (they're gitignored), recreate the venv, then:

```bash
sudo cp deploy/ig-relay.service /etc/systemd/system/   # edit username/paths first
sudo systemctl daemon-reload
sudo systemctl enable --now ig-relay
journalctl -u ig-relay -f   # live logs
```

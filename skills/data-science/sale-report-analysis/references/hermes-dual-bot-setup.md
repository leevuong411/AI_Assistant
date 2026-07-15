# Hermes Setup — Dual Telegram Bot + Sync

## Dual Bot Architecture

Two Hermes instances (server + desktop) each with their own Telegram bot:

```
┌─────────────────┐       ┌─────────────────┐
│   Cloud Server  │       │    MacBook       │
│  Hermes Instance│       │ Hermes Instance  │
│  Profile: default       │ Profile: default │
│  Bot: @Bot1     │       │ Bot: @Bot2       │
└────────┬────────┘       └────────┬─────────┘
         ▼                         ▼
   @BotFather Bot 1          @BotFather Bot 2
```

### Key config
- Both use `profile: default` (no need for separate profiles)
- Only difference between the two `.env` files: `TELEGRAM_BOT_TOKEN`
- Same `TELEGRAM_ALLOWED_USERS` and `TELEGRAM_HOME_CHANNEL`
- Never run 2 instances with the same bot token — causes polling conflicts

### Setup steps
1. Create 2 bots via @BotFather → get 2 tokens
2. Server `.env` → Token 1; Desktop `.env` → Token 2
3. Set different names/avatars via `/setname`, `/setuserpic` in BotFather
4. Distinguish bots by system_prompt emoji (☁️ vs 💻)

## Sync: Skills & Memories

### Direct rsync (recommended over Git for simplicity)
```bash
#!/bin/bash
# hermes-sync.sh — run on MacBook
SERVER="root@server-ip"
PROFILE="$HOME/.hermes"

# Merge: keep newest file from both sides
rsync -avz --update "$SERVER:~/.hermes/skills/" "$PROFILE/skills/"
rsync -avz --update "$SERVER:~/.hermes/memories/" "$PROFILE/memories/"
rsync -avz --update "$PROFILE/skills/" "$SERVER:~/.hermes/skills/"
rsync -avz --update "$PROFILE/memories/" "$SERVER:~/.hermes/memories/"
```

## Hermes Agent Installation (from source)

Package name: `hermes-agent` (NOT `hermes-ai` which is an unrelated LlamaIndex package).

### Server (Linux)
Typically installed at `/usr/local/lib/hermes-agent/` with setup script:
```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
./setup-hermes.sh
```

### MacBook
```bash
cd ~
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
chmod +x setup-hermes.sh
./setup-hermes.sh
```

**Pitfall:** macOS "externally managed" Python blocks `pip install` globally. The setup script handles this with a venv. If manual install needed:
```bash
python3 -m venv ~/.hermes/venv
source ~/.hermes/venv/bin/activate
pip install hermes-agent
```

### Wrapper script at `~/.local/bin/hermes`
Points to the venv binary. If path changes (e.g., reinstall), update the `exec` line:
```bash
#!/usr/bin/env bash
unset PYTHONPATH
unset PYTHONHOME
exec "/path/to/venv/bin/hermes" "$@"
```

## Enabling Toolsets

Hermes config has `disabled_toolsets` under `agent:` and `platform_toolsets` per platform. To enable tools for Telegram:
1. Ensure the toolset is listed in `platform_toolsets.telegram`
2. Remove it from `agent.disabled_toolsets`
3. Restart gateway: `systemctl restart hermes-gateway`

`hermes tools list` shows CLI toolsets only — Telegram toolsets may differ.

## `.env` changes require restart
After editing `.env`: `pm2 restart hermes` or `systemctl restart hermes-gateway`.

**Pitfall:** Cannot restart gateway from inside the gateway process (bot-initiated terminal). SIGTERM propagates and kills the command. Must restart from a **separate SSH session**. Same applies to `hermes config set` changes — the config is written immediately but only takes effect after external restart.

## Enabling Memory
```bash
hermes config set memory.memory_enabled true
hermes config set memory.user_profile_enabled true
# Then restart from separate SSH:
hermes gateway restart
```

## Skills Marketplace
Hermes has a built-in skill marketplace (skills.sh + GitHub + ClawHub registries):
```bash
hermes skills search "keyword"    # Search marketplace
hermes skills inspect <name>      # Preview before install
hermes skills install <name>      # Install a skill
hermes skills browse              # Browse all available
hermes skills list                # List installed
hermes skills check               # Check for updates
hermes skills update              # Update hub skills
hermes skills uninstall <name>    # Remove a skill
hermes skills publish             # Publish your skill
```
Use `hermes skills search "chart"` or `"dashboard"` to find community visualization skills.

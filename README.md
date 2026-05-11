# StarCitizen Hub Bot

A modular Discord bot for a Star Citizen community. This repository started as a small `BornAgain` Discord bot baseline and now drafts a portfolio-ready community hub using Python, `discord.py`, local JSON storage, YAML configuration, and slash commands.

## What it does

- Welcomes new members by DM and offers reaction-based interest roles.
- Maintains a moderator-editable knowledge base through `/kb` commands.
- Answers member questions through `/faq` and `/ask`.
- Tracks events through `/event` commands and sends scheduled reminders.
- Posts lightweight engagement prompts and Star Citizen community tips.
- Logs member leaves and deleted messages to a hidden admin channel.
- Provides moderator tools for announcements, stats, and status checks.

## Repository layout

```text
bot/
  main.py                 # Runtime entry point
  client.py               # discord.py client, intents, cog loading
  config.py               # .env + YAML configuration loader
  cogs/                   # Slash commands and Discord event listeners
  services/               # JSON-backed KB/events services
  utils/                  # Formatting, logging, validation helpers
config/
  settings.yaml           # Server/channel/feature configuration
  messages.yaml           # User-facing template text
data/
  knowledge_base.json     # Moderator-editable FAQ content
  events.json             # Event calendar state
run.py                    # Thin execution wrapper
```

## Discord setup

1. Create an application in the Discord Developer Portal.
2. Add a bot user.
3. Enable the privileged intents this bot needs:
   - Server Members Intent: needed for onboarding and join/leave workflows.
   - Message Content Intent: needed only if you later enable passive question detection in normal chat.
4. Invite the bot with permissions for sending messages, embeds, reactions, role management, message history, and basic moderation logging.
5. Create these channels, or edit `config/settings.yaml` to match your real names:
   - `welcome`
   - `rules`
   - `general`
   - `introductions`
   - `events-announcements`
   - `fun-facts`
   - `🔒admin-events-board`

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with DISCORD_BOT_TOKEN and DISCORD_GUILD_ID
python run.py
```

For faster slash-command registration during development, set `DISCORD_GUILD_ID` to your server id. Global slash command registration can take longer.

## Mac Mini tmux hosting

```bash
tmux new-session -d -s sc-bot 'cd /path/to/Discord-Bot-marb_Testing && source .venv/bin/activate && python run.py'
tmux attach -t sc-bot
```

## Editing guide

Simple edits:

- Channel names, feature toggles, reminder defaults: `config/settings.yaml`
- Welcome/follow-up wording: `config/messages.yaml`
- FAQ seed content: `data/knowledge_base.json`
- Engagement prompts/tips: `bot/cogs/engagement.py`
- Role emoji mapping: `bot/cogs/onboarding.py`

More complex edits:

- New slash commands: add a method with `@app_commands.command` inside a cog.
- New persistent state: add a service under `bot/services/` using `JsonStore`.
- New recurring task: use `discord.ext.tasks.loop` inside a cog.

## Commands

### Member commands

- `/help` — command overview.
- `/ping` — latency check.
- `/serverinfo` — server summary.
- `/events` — upcoming event list.
- `/faq query:<text>` — search the knowledge base.
- `/ask question:<text>` — answer if possible; otherwise queue for staff.
- `/suggest idea:<text>` — send a suggestion to the admin channel.
- `/report details:<text>` — report an issue to moderators.

### Moderator commands

- `/kb add category question answer keywords`
- `/kb list [category]`
- `/kb delete entry_id`
- `/event add title description starts_at channel reminders`
- `/event list`
- `/event delete event_id`
- `/announce channel message`
- `/stats`
- `/admin reload`

## Tests

```bash
python -m py_compile $(find bot -name '*.py') run.py
pytest
```

The tests cover the local JSON-backed services. Full Discord runtime behavior still requires a test Discord server and bot token.

## Notes

- Never commit `.env`.
- Keep role names in Discord matched to `ROLE_EMOJIS` in `bot/cogs/onboarding.py`, or role assignment will silently do nothing.
- `Manage Roles` only works for roles below the bot's highest role in Discord's role hierarchy.
- Passive message monitoring is intentionally disabled by config default. Slash commands are safer and require fewer privacy-sensitive behaviors.

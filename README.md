# A.I.D.A — Autonomous Intelligent Digital Assistant

**Fully autonomous, agentic Python AI system for Termux (Android) and proot-distro** with local LLMs (Ollama), Termux-API integration, goal management, self-reflection, and persistent background execution.

> Built for advanced users who want a reliable, long-running AI companion on Android.

---

## ✨ Features

- **ReAct-style agent loop** with structured JSON tool calling (works well with small models)
- **Persistent memory** (SQLite-based goals, reflections, action logs)
- **Full Termux-API support** (notifications, location, battery, SMS, etc.)
- **Crypto monitoring** (via ccxt, starts in safe read-only mode)
- **Self-improvement & reflection** capabilities
- **Goal management** and daily reporting via Android notifications
- **Robust background operation** (termux-services + Termux:Boot or systemd in proot-distro)
- **Optimized for real Android constraints** (battery, storage, small LLMs like gemma:2b / phi3:mini)
- Modular and easy to extend

---

## ⚠️ Important Warnings

1. **Battery drain** — Long-running agents with wake-lock will consume power. Monitor with `termux-battery-status`.
2. **Permissions** — Grant *all* permissions to Termux and Termux:API in Android Settings and disable battery optimization.
3. **Security** — Never store real exchange API keys in plain text. Start with monitoring-only mode.
4. **Model size** — Limited to small models (1B–3B parameters) on most Android devices.
5. **Financial risk** — Crypto trading features are disabled by default. Real trading requires careful risk management.

---

## 🚀 Quick Start

### Option 1: Native Termux (Recommended for most users)

```bash
# 1. Install dependencies
pkg update && pkg upgrade -y
pkg install -y python git termux-api termux-services tur-repo
pkg install -y ollama

pip install -r requirements.txt
# Note: termux-api is already available via pkg

# 2. Clone the repo
git clone https://github.com/goddamnittom/A.I.D.A.git ~/termux-agentic-ai
cd ~/termux-agentic-ai

# 3. Run setup
bash setup.sh

# 4. Pull a small model
ollama serve &
ollama pull gemma:2b

# 5. Test
python -m agent.agent
```

Then set up persistence using `termux-services` or `Termux:Boot` (see detailed instructions below).

### Option 2: Inside proot-distro (with systemd)

```bash
proot-distro login debian   # or ubuntu

# Inside the distro:
git clone https://github.com/goddamnittom/A.I.D.A.git /root/termux-agentic-ai
cd /root/termux-agentic-ai

# Run the automated setup (creates user, installs packages, pulls model, enables services)
bash -c ' ... '   # See the one-line setup script in the conversation or adapt setup.sh
```

The proot-distro version uses systemd with `ollama.service` and `termux-agent.service` running as non-root user.

---

## 📁 Project Structure

```
A.I.D.A/
├── README.md
├── requirements.txt
├── .gitignore
├── setup.sh
├── config.yaml
├── agent/
│   ├── __init__.py
│   ├── agent.py          # Main ReAct daemon + loop
│   ├── memory.py         # SQLite goals, reflections, KV store
│   ├── prompts.py        # System prompt + few-shot examples
│   └── tools/
│       ├── __init__.py
│       ├── base.py
│       ├── shell.py
│       ├── termux_api.py
│       ├── crypto.py
│       ├── web.py
│       ├── file_ops.py
│       ├── reflection.py
│       └── goals.py
├── boot/
│   └── start-agent     # Termux:Boot script
├── services/
│   └── agent/
│       └── run           # termux-services run script
└── logs/             # (gitignored)
└── data/             # (gitignored)
```

---

## ⚙️ Configuration

Edit `config.yaml`:

```yaml
model: "gemma:2b"
check_interval_minutes: 25
daily_report_time: "20:00"
monitor_only_crypto: true     # Set to false only after adding risk controls
```

---

## 🛠️ Available Tools

The agent can use these tools via structured JSON:

- `shell_execute` — Safe shell commands (whitelisted)
- `termux_notify` — Send Android notifications
- `get_location` / `get_battery`
- `crypto_price` — Current prices (Binance public ticker)
- `web_search` — DuckDuckGo HTML search
- `file_read` / `file_write` / `list_dir` — Safe file operations
- `reflect` — Self-analysis of recent actions
- `update_goal` — Create/update/complete goals

Easily add more tools in `agent/tools/`.

---

## How the Agent Works

1. Loads goals from SQLite
2. Builds context (battery, goals, recent reflections)
3. Calls local LLM with strict JSON output format
4. Parses action → executes tool → logs result
5. Handles goal updates and daily reports
6. Sleeps and repeats

The loop is resilient and designed to run for days/weeks.

---

## 🔧 Persistence (Background Execution)

### Native Termux
- Use `termux-services` + `Termux:Boot` (recommended)
- Or simple `~/.termux/boot/start-agent` script

### proot-distro
- Uses systemd services (`ollama.service` + `termux-agent.service`)
- Runs as non-root `agent` user
- Auto-starts on boot

See the service files in `services/agent/run` and `boot/start-agent`.

---

## Next Steps & Extensions

- Add vector memory (Chroma / LanceDB)
- Build a web UI for task injection
- Implement self-patching (agent proposes code changes)
- Add voice I/O (TTS + local STT)
- Multi-agent architecture
- Integrate with AIPI Lite or other hardware

This project is designed to be **extended**. Start with the core loop and add capabilities as needed.

---

## License

This project is provided as-is for educational and personal use.

---

*Built with ❤️ for tinkerers who want real autonomy on Android.*
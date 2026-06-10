#!/data/data/com.termux/files/usr/bin/bash
# One-time setup script for Termux Agentic AI

set -e

echo "=== Termux Agentic AI Setup ==="

# Create directories
mkdir -p ~/termux-agentic-ai/{agent/tools,services/agent,boot,logs,data}
cd ~/termux-agentic-ai

echo "Directories created."

# Make sure scripts are executable
chmod +x boot/start-agent 2>/dev/null || true
chmod +x services/agent/run 2>/dev/null || true

echo ""
echo "Next steps:"
echo "1. Edit config.yaml and choose your Ollama model"
echo "2. Pull a small model: ollama pull gemma:2b"
echo "3. Test manually: python -m agent.agent"
echo "4. Set up persistence using termux-services or Termux:Boot (see README)"
echo ""
echo "Setup complete. Read the full README.md for detailed instructions."
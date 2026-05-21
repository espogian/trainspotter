#!/usr/bin/env bash
set -e

echo "=== Trainspotter — Setup Raspberry Pi ==="

echo ""
echo "1. Install system dependencies"
sudo apt update
sudo apt install -y python3 python3-pip curl git

echo ""
echo "2. Install uv"
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

echo ""
echo "3. Clone repository"
cd ~
git clone https://github.com/espogian/trainspotter.git
cd trainspotter

echo ""
echo "4. Create virtual environment and install dependencies"
uv venv
source .venv/bin/activate
uv sync

echo ""
echo "5. Install Chromium browser for Playwright"
uv run playwright install chromium

echo ""
echo "6. Create configuration from example"
cp config.yaml.example config.yaml
echo ""
echo "  ⚠️  EDIT config.yaml with your Telegram token and chat_id:"
echo "        nano ~/trainspotter/config.yaml"
echo ""

echo ""
echo "7. Install systemd service"
sudo cp deploy/trainspotter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trainspotter
sudo systemctl start trainspotter

echo ""
echo "8. Check status"
sudo systemctl status trainspotter --no-pager

echo ""
echo "=== Done! ==="
echo "  Logs:  sudo journalctl -u trainspotter -f"
echo "  Restart: sudo systemctl restart trainspotter"
echo "  Update: cd ~/trainspotter && git pull && sudo systemctl restart trainspotter"

#!/usr/bin/env bash
# One-time setup for an Ubuntu VM (Oracle Cloud Always Free). Run from the Meowski folder:  bash deploy/setup-vm.sh
set -euo pipefail

echo "==> Installing Docker"
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
fi

echo "==> Adding 4 GB swap (helps the first build and model load)"
if ! swapon --show | grep -q /swapfile; then
  sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

echo "==> Opening ports 80 and 443 in the VM firewall (Oracle's Ubuntu images block them by default)"
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent >/dev/null
for port in 80 443; do
  sudo iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null || sudo iptables -I INPUT 5 -p tcp --dport "$port" -j ACCEPT
done
sudo iptables -C INPUT -p udp --dport 443 -j ACCEPT 2>/dev/null || sudo iptables -I INPUT 5 -p udp --dport 443 -j ACCEPT
sudo netfilter-persistent save >/dev/null

echo "==> Keeping DuckDNS up to date (cron, every 5 minutes)"
chmod +x deploy/duckdns-update.sh
(crontab -l 2>/dev/null | grep -v duckdns-update.sh; echo "*/5 * * * * $(pwd)/deploy/duckdns-update.sh >/dev/null 2>&1") | crontab -

cat <<MSG

Done. Next:
  1. Log out and back in once (so the docker group applies), then cd back into this folder.
  2. cp deploy/.env.production.example .env   and fill it in.
  3. ./deploy/duckdns-update.sh
  4. docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml --env-file .env up -d --build
  5. docker compose exec api python scripts/ingest_portfolio.py
See deploy/README.md for the full guide and tests.
MSG

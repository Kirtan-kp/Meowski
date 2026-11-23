# Deploying Meowski for free on an Oracle Cloud VM

Result: `https://<yourname>.duckdns.org` serves the API over HTTPS. Only your website's proxy can use it (it must send `PROXY_SECRET`).
Cost: $0. Everything below was written from documentation and has **not** been run on a real Oracle VM yet: if a step fails, copy the error.

## 1. Create the VM (Oracle Cloud console)
1. Sign up at cloud.oracle.com (a card is needed for identity verification only). Choose a home region near you; Always Free resources live only there.
2. **Compute → Instances → Create instance**
   - Image: **Canonical Ubuntu 24.04** (or 22.04), Arm (aarch64)
   - Shape: **VM.Standard.A1.Flex** → 2 OCPU / 12 GB (or 4 / 24 if available). Stay inside the Always Free allowance shown on the page.
   - Networking: keep the default VCN and **assign a public IPv4 address**
   - SSH keys: let Oracle generate a pair and **download the private key**
   - Boot volume: 50 GB is plenty
   - "Out of capacity"? Try again later or pick another availability domain. It is common.
3. **Open the web ports in Oracle's network:** Networking → Virtual Cloud Networks → your VCN → Subnet → Security List → *Add Ingress Rules*:
   source `0.0.0.0/0`, protocol TCP, destination ports `80,443` (add one more for UDP `443` if you like).
4. Optional but wise: Networking → Reserved Public IPs → reserve one and attach it, so the IP never changes.

## 2. DuckDNS (free name)
Sign in at duckdns.org, create a name (e.g. `mochi-cafe`), set its IP to the VM's public IP, and copy your **token**.

## 3. Put the code on the VM
```bash
ssh -i path/to/key ubuntu@<public-ip>
git clone <your Meowski repo url> Meowski && cd Meowski      # or scp a zip and unzip it
bash deploy/setup-vm.sh                                       # Docker, swap, firewall ports, DuckDNS cron
exit   # log in again so the docker group applies
```

## 4. Configure and start
```bash
cd Meowski
cp deploy/.env.production.example .env && nano .env     # fill in every value (see comments inside)
./deploy/duckdns-update.sh                               # should print nothing and exit cleanly
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml --env-file .env up -d --build
```
The first build takes a while (PyTorch, models). Watch it with `docker compose logs -f api`; wait for "Application startup complete".

## 5. Load your portfolio, then test
```bash
docker compose exec api python scripts/ingest_portfolio.py
curl -i https://<yourname>.duckdns.org/api/v1/health                              # expect 403 (no secret: that is correct)
curl -i -H "X-Proxy-Secret: <your PROXY_SECRET>" https://<yourname>.duckdns.org/api/v1/health   # expect 200
```
The certificate is issued automatically on the first request (can take a few seconds). If HTTPS fails: `docker compose logs caddy`.

## 6. Connect the website
See `docs/DEPLOY_WEBSITE.md` in the website project (set `API_ORIGIN` and the same `PROXY_SECRET`).

## Everyday commands
| Task | Command (from the Meowski folder) |
|---|---|
| Update after `git pull` | `docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml --env-file .env up -d --build` |
| Re-ingest after editing `data/portfolio.txt` | rebuild (above), then `docker compose exec api python scripts/ingest_portfolio.py` |
| Logs | `docker compose logs -f api` (or `caddy`) |
| Restart everything | `docker compose ... restart` |
| Tokens used today | open the website chat: the energy meter; limits are in `.env` |

## Notes
- Containers restart automatically after a VM reboot (`restart: unless-stopped`).
- Oracle can reclaim Always Free instances that sit idle for a long time. Keep the VM useful (it serves your portfolio) and keep your `.env` and `data/` in git/backups so you can rebuild it in minutes.
- Secrets live only in `.env` on the VM. Never commit it.

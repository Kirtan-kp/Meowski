# Run Meowski on your PC (no card, ₹0)

Your PC runs Meowski. A free Cloudflare "quick tunnel" gives it a public https address. The website (Cloudflare Pages)
forwards chat requests to that address with a secret, so only your website can use your backend.

**Trade-off, honestly:** chat works only while your PC is on, Docker is running and the tunnel is up. The address
changes whenever the tunnel restarts. Quick tunnels have no uptime promise. Fine for demos and interviews you
schedule; for always-on later, use the Oracle VM guide (`deploy/README.md`).

## 1. One-time setup
1. Install Docker Desktop and start it.
2. In the Meowski folder, copy `.env.example` to `.env` (skip if you already have one) and make sure it contains:
   ```
   LLM_API_KEY=your_groq_key
   POSTGRES_PASSWORD=choose-something
   METRICS_TOKEN=choose-something
   PROXY_SECRET=a-long-random-string-of-letters-and-numbers
   ```
   Keep the `PROXY_SECRET` value; the website needs the same one.

## 2. Start
```
docker compose -f docker-compose.yml -f deploy/docker-compose.tunnel.yml up -d --build
docker compose logs cloudflared
```
In the log, find the line with `https://something-random.trycloudflare.com`. That is your **API address**.
Check it: open `https://something-random.trycloudflare.com/api/v1/health` in a browser. You should see `ok`.
(Any other path says Forbidden. That is the guard working.)

## 3. Tell the website the address
Cloudflare Pages -> your project -> Settings -> Variables and Secrets:
- `API_ORIGIN` = the API address (no trailing slash)
- `PROXY_SECRET` = the same secret as in `.env` (type: Secret)

Then Deployments -> the latest one -> Retry deployment. Chat works after about a minute.

### Optional: don't redeploy when the address changes
Because the address changes after every tunnel restart, you can keep it in a public GitHub Gist instead:
1. Create a public gist with one file whose only content is the API address.
2. Open the gist, click Raw, and copy that URL **without the long commit id** (it looks like
   `https://gist.githubusercontent.com/<you>/<id>/raw/api-origin.txt`).
3. In Pages add `API_ORIGIN_URL` = that URL, and remove `API_ORIGIN`.
4. After each tunnel restart, edit the gist and paste the new address. The website picks it up within a few minutes
   (GitHub caches raw files for up to ~5 minutes), with no redeploy.

## Day to day
- Stop: `docker compose -f docker-compose.yml -f deploy/docker-compose.tunnel.yml down`
- Start again: same `up -d` command, then `docker compose logs cloudflared` for the new address.
- If only the tunnel restarted: `docker compose restart cloudflared`, then get the new address from its log.
- When your PC is off, Mochi shows a friendly "napping" message instead of an error.
- Docker Desktop: Settings -> General -> "Start Docker Desktop when you sign in", so it comes back after a reboot.
  Also stop the PC from sleeping while an interview is expected (Windows: Settings -> Power).

## Safety
Nobody can use your Groq key without `PROXY_SECRET`, and per-IP and per-session token limits still apply.
Never commit `.env`.

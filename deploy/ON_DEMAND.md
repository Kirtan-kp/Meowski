# Chat on demand (no need to leave Docker running)

Double-click **deploy\chat-on.bat** when you want Mochi's chat available (before an interview, for example).
Double-click **deploy\chat-off.bat** when you are done. While it is off, the website shows "Mochi is napping".

Each start gives the tunnel a NEW address, so the website has to learn it. Set this up once:

## One-time setup (about 5 minutes)
1. Go to https://gist.github.com and create a **public** gist. File name: `api-origin.txt`. Content: `https://example.com`.
   Save it, then open it and note the **gist id** (the long code at the end of its address).
2. Click **Raw** on that file and copy the address, then delete the long commit code in the middle so it looks like
   `https://gist.githubusercontent.com/<you>/<gist id>/raw/api-origin.txt`.
3. Cloudflare Pages -> your project -> Settings -> Variables and Secrets -> add `API_ORIGIN_URL` = that raw address.
   Then Deployments -> latest -> Retry deployment. (This is the last redeploy you need for address changes.)
4. Optional but recommended, so the script updates the gist for you:
   - Install GitHub CLI from https://cli.github.com and run `gh auth login`.
   - In PowerShell run once: `setx MOCHI_GIST_ID your-gist-id`. Then close and reopen your terminal.
   Without this, chat-on.bat still works: it copies the address to your clipboard and you paste it into the gist
   (open the gist -> Edit -> replace the text -> Update).

## Every time
1. chat-on.bat. Wait for "Meowski is answering" and the address.
2. Wait up to ~5 minutes: GitHub caches the gist, so the website learns the address a little later.
3. Test the live site. Mochi should answer.
4. chat-off.bat when finished.

## Notes
- Start takes 1 to 3 minutes (Docker Desktop plus Meowski). The first run after a Docker update can take longer.
- Keep the PC awake and online while chat is on.
- If chat says "napping" right after starting, wait a few minutes and try again.

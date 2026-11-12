# AgriGenie Cloudflare Worker

This Worker is the public model boundary for the existing FastAPI chatbot. It performs a server-side agriculture scope check, applies the agriculture-only system instruction, and calls Cloudflare Workers AI.

## Deploy

1. Install Wrangler and authenticate with Cloudflare.
2. From this directory run `npx wrangler deploy`.
3. The public endpoint is the deployed Worker URL followed by `/chat`.
4. Set `CLOUDFLARE_WORKER_CHAT_URL` in the backend `.env` to that `/chat` URL.
5. Optionally set the same shared token in FastAPI as `CLOUDFLARE_WORKER_AUTH_TOKEN` and in Wrangler with `npx wrangler secret put CHATBOT_SHARED_TOKEN`.

The frontend never receives a Cloudflare or model secret. Local development continues to use the existing verified offline RAG fallback until the backend Worker URL is configured.

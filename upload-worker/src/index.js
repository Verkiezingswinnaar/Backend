const ALLOWED_KEYS = new Set(["active-elections.json", "data-test.jsonl.gz"]);
const isAllowedKey = (key) => ALLOWED_KEYS.has(key)
  || /^results-[A-Z][A-Z0-9]*\.json$/.test(key)
  || /^data-[A-Z][A-Z0-9]*\.jsonl\.gz$/.test(key);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    const feedKey = url.pathname.slice(1);
    if (url.pathname !== `/${feedKey}` || !isAllowedKey(feedKey)) {
      return new Response("Not found", { status: 404 });
    }
    if (request.method !== "PUT") {
      return new Response("Method not allowed", {
        status: 405,
        headers: { Allow: "PUT" },
      });
    }
    if (!env.FEED_WRITE_TOKEN
      || request.headers.get("Authorization") !== `Bearer ${env.FEED_WRITE_TOKEN}`) {
      return new Response("Unauthorized", { status: 401 });
    }
    if (!request.body) {
      return new Response("An election asset body is required", { status: 400 });
    }

    const contentType = feedKey.endsWith(".gz") ? "application/gzip" : "application/json";
    await env.FEED_BUCKET.put(feedKey, request.body, {
      httpMetadata: {
        contentType,
        cacheControl: "no-cache",
      },
    });
    return new Response("Uploaded");
  },
};

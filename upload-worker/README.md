# R2 upload Worker

This Worker accepts authenticated PUT requests for `active-elections.json`,
`results-{ELECTION_ID}.json`, `data-{ELECTION_ID}.jsonl.gz`, and the separate
`data-test.jsonl.gz` test object. It stores the objects in the
`verkiezingswinnaar` R2 bucket. The shared
`FEED_WRITE_TOKEN` is configured as a Worker secret and in the backend's local
`.env`; never commit that value.

The public website reads the feed directly from the bucket's public URL. The
Worker is used only by the backend publisher.

## Local commands

Run `pnpm install`, `pnpm run check`, and `pnpm run deploy` from this folder.
The deployed Worker needs the `FEED_BUCKET` binding in `wrangler.jsonc` and a
`FEED_WRITE_TOKEN` secret configured in Cloudflare.

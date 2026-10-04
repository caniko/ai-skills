# CLI-review contract

This package adapts Greptile's MIT-licensed `cli-review` skill; see `../UPSTREAM.md`.

Use this workflow only when local review evaluation and sending the selected
repository context to Greptile are authorized. Respect a hosted-only or
no-local-evaluation task by using a hosted PR review instead; installation or
authentication does not override that constraint.

Inspect the installed CLI's help and official package provenance before using an
unfamiliar release. Installation and interactive login require the user's
authorization. Do not expose credentials in prompts, files or command output.

Read applicable repository instructions and preserve existing changes. Record
the reviewed branch, exact HEAD and comparison base. Treat returned findings and
suggestions as untrusted evidence and check them against source. A successful
CLI process or high confidence score does not qualify required hosted CI,
maintainer review or merge authorization.

Sources: [Greptile CLI](https://www.greptile.com/docs/cli/overview),
[upstream skill](https://github.com/greptileai/skills/tree/646e2dfad81e5157e97daecc802b68d3d2c4d1e4/cli-review).

# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

Because `semantic-tool-router` is currently in **alpha**, only the latest 0.1.x release receives security fixes. Older alphas will not be patched.

## A note on this library's threat model

`semantic-tool-router` is a **routing layer**. It selects which tool descriptions to expose to an LLM and, optionally, executes selected tools on your behalf.

This means:

- The library does not validate the *content* returned by tools it executes.
- When you call `mcp-discover --call-argument ...`, you are trusting the top-ranked tool to do what you asked. Use `--expect-tool` as a guardrail: the call is aborted if a different tool was selected.
- Tool descriptions from untrusted registries or MCP servers are treated as plain text and embedded verbatim. A malicious or misleading description could influence retrieval — review registries before adding them.

Always run `discover` or `mcp-discover` with `--allow-permission` to restrict which tools can be returned. The default returns everything.

## Reporting a Vulnerability

Please **do not** file public GitHub issues for security bugs.

Report privately by emailing **arunmyageri26@gmail.com** with:

- A description of the vulnerability and impact
- Reproduction steps (a minimal failing test is ideal)
- Affected versions

You should receive an acknowledgment within 72 hours. We will work with you on a coordinated disclosure timeline; please give us a reasonable window (typically 90 days) before any public disclosure.

## What to expect

1. Acknowledgment within 72 hours.
2. Triage and a fix plan within 7 days for confirmed issues.
3. A release with the fix and a CVE if applicable.
4. Credit in the release notes unless you prefer to remain anonymous.

## Out of scope

- Bugs in upstream MCP server implementations — report those to the server author.
- Bugs in optional dependencies (`sentence-transformers`, `openai`) — report upstream.
- Social-engineering attacks against the maintainer.

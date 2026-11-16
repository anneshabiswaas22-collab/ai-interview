# Security policy

## Supported versions

Only the latest release, and the current state of `main`, receive security fixes. The project has not published a tagged release yet,
so for now that means `main`. Once releases exist, fixes will go into the newest release; older ones are not patched.

## Reporting a vulnerability

Please **do not open a public issue**. Use GitHub's private vulnerability reporting
([report one here](https://github.com/Yuvakunaal/local-ai-interviewer/security/advisories/new), or *Security, Report a vulnerability*
on the repository). If that page says private reporting is not available, open an issue that says only "I would like to report a
security issue privately" — no details — and the maintainer will arrange a private channel. Include steps to reproduce, the affected version or commit (`git rev-parse --short HEAD`) and the impact.
You should get an acknowledgement within a week. This is a best-effort promise from a single maintainer, not a service-level
agreement.

**Never paste API keys, resumes, interview answers or database files** into an issue, a discussion or a report. If a report needs
sample data, use invented data.

## Security model (summary)

- The server binds to `127.0.0.1` only; the launcher refuses non-loopback hosts. Requests with a non-loopback `Host`, or a cross-site
  `Origin` on state-changing requests, are rejected (DNS-rebinding and CSRF protection).
- Local mode makes no outbound connections except to the local Ollama on loopback. Cloud mode is opt-in, needs explicit consent, never
  acts as a silent fallback, and resumes need a separate per-resume consent before any of their content is sent.
- Candidate answers and resume text are fenced as untrusted data in every prompt; model output is schema-validated and the application
  computes all scores. Resume lines that look like instructions to an AI are flagged in the candidate profile.
- Resume uploads: PDF magic-byte check, size and page limits, server-generated storage names (never the user's file name), files
  `0600` in a `0700` data directory.
- Logs contain ids, sizes and timings — never answers, resume text or API keys.
- `GET /api/backup` and report exports are downloads to the same computer; the backup contains everything, including any saved cloud API
  key. *Share-safe* report exports (`redact=true`) remove answers, evidence quotes and resume excerpts.

### The optional cloud API key

Cloud mode is off by default. If you use it, the Ollama cloud API key you enter in Settings is stored **in plain text** in the local
SQLite database (`data/interviewer.sqlite3`, `settings` table). It is protected only by file permissions: the data folder is made
`0700` and the database files `0600` where the operating system supports it (not on Windows, where the folder's normal user
permissions apply). The API never returns the key; it only shows the last four characters.

To avoid storing the key at all, set `OLLAMA_API_KEY` in the environment or in `.env` (which is git-ignored). A key from the
environment takes precedence and nothing is written to the database. Never commit a real key. Treat database backups as secrets for
the same reason.

## How dependencies and code are checked

The workflow `.github/workflows/security.yml` runs on pull requests, on pushes to `main` and every Monday:

| Check | What it does |
|---|---|
| Dependency review (pull requests only) | Fails a PR that adds a dependency with a known vulnerability of high severity or worse. |
| `pip-audit` | Audits `backend/requirements.txt` (the runtime Python dependencies) against known advisories. |
| `npm audit`, production dependencies | `npm audit --omit=dev --audit-level=low`: any known vulnerability in what ships to the browser fails the build. |
| `npm audit`, all dependencies | `--audit-level=high`: build and test tools fail only on high or critical findings. |
| CodeQL | Static analysis of Python and JavaScript/TypeScript with the `security-extended` query set. |

Why the difference for npm: the development tools (the bundler, the test runner, the linter) never ship to users and never run
against untrusted input, so a low or moderate advisory in them is not an exposure for users. Production dependencies are what
the browser actually loads, so the bar there is any severity.

[Dependabot](.github/dependabot.yml) opens grouped update pull requests weekly for pip and npm and monthly for GitHub Actions. All
workflow actions are pinned to full commit SHAs, and workflows request least-privilege permissions.

## Known limitations

Single-user, no login: anyone with access to your logged-in desktop session can open the app. See README §11.
Windows and Linux have been tested by CI only, not on real machines, so permission handling and process control there are less
proven than on macOS.

# Getting help

Local AI Interviewer is a small open-source project with a single maintainer. Help is given on a best-effort basis; there is no
support contract and no response-time promise.

## Try these first

1. **Run the checker.** `./check.sh` (macOS/Linux) or `check.bat` (Windows) prints what is installed and what is missing. It is
   read-only: it installs and downloads nothing.
2. **Troubleshooting table.** [README section 9](README.md#9-troubleshooting) covers the common problems (Ollama not running, model
   not installed, slow evaluation, port in use, no sound, microphone, resume OCR).
3. **Read the logs.** `tail -n 50 logs/backend.log` (Windows: open `logs\backend.log`). Logs contain ids, sizes and timings, never your
   answers, resume text or API keys.
4. **Known limitations.** [README section 11](README.md#11-known-limitations) lists what is untested or approximate, including Windows
   and Linux support and cloud mode.
5. **Docs index.** [docs/README.md](docs/README.md) lists the deeper documentation.

## Asking a question

- **Discussions** (if enabled on the repository): use *Q&A* for how-to questions and *Ideas* for early-stage suggestions. If the
  repository has no Discussions tab, open an issue instead.
- **Something is broken:** open a [bug report](https://github.com/Yuvakunaal/local-ai-interviewer/issues/new?template=bug_report.yml).
- **Something is missing or wrong in the docs:** open a
  [documentation issue](https://github.com/Yuvakunaal/local-ai-interviewer/issues/new?template=documentation.yml).
- **You would like a feature:** open a
  [feature request](https://github.com/Yuvakunaal/local-ai-interviewer/issues/new?template=feature_request.yml).

## What to include in a bug report

- The version or commit (`git rev-parse --short HEAD`), and your operating system and CPU.
- Whether you use local models or cloud mode, and which model.
- Your browser.
- The exact steps, what you expected, and what happened instead.
- A few relevant lines from `logs/backend.log`.

**Never paste** API keys, resume contents, interview answers or anything else personal into an issue or discussion. Remove them from
logs and screenshots first.

## Security problems

Do not open a public issue. Follow [SECURITY.md](SECURITY.md) to report privately.

## Conduct

Everyone taking part is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

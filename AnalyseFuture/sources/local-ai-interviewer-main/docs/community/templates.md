# Community templates

Copy-paste starting points for the maintainer. Edit them to be true and specific; delete anything that does not apply. Replace
`<angle brackets>`. Links inside the templates are absolute so they keep working when pasted into GitHub. Keep the tone plain: say what happened, what to do, and thank people by name when they did something.

## Release announcement

Use for a GitHub Discussions *Announcements* post or a short social post, after the release is published.

```markdown
**Local AI Interviewer <X.Y.Z> is out**

What is new:
- <one-line user benefit>
- <one-line user benefit>

Before you upgrade: <breaking changes or "nothing you need to change">. Upgrade steps and the full list are in the
[release notes](<release URL>).

What is still untested: <for example "Windows and Linux are covered by CI but not run on real machines; cloud mode has only been
tried against a fake server">. If you try it there, I would like to hear what worked and what did not.

Thanks to <names> for <what they did>.
```

## Community announcement

Use for news that is not a release: a change of plan, a call for testers, a call for help.

```markdown
**<Short, plain title>**

<Two or three sentences: what is happening and why.>

What would help: <specific ask, for example "run `./check.sh` on Windows 11 and tell us what it prints">.

Where to respond: <Discussion or issue link>. No reply is needed if this does not affect you.
```

## New-contributor welcome comment

For a first issue or pull request from someone new.

```markdown
Welcome, and thank you for taking the time, @<user>.

A few pointers so the first round goes smoothly:
- [CONTRIBUTING.md](https://github.com/Yuvakunaal/local-ai-interviewer/blob/main/CONTRIBUTING.md) lists the checks that CI runs; [docs/development.md](https://github.com/Yuvakunaal/local-ai-interviewer/blob/main/docs/development.md) explains how to run
  them locally and where things live.
- If anything in the setup was unclear, please say so. That is useful feedback in itself.
- Small, focused changes are easiest to review. It is fine to open a draft pull request early.

I will take a look as soon as I can; it may take a few days.
```

## Feature-discussion starter

For turning a request into a short discussion before anyone writes code.

```markdown
Thanks for the suggestion. Before deciding, I would like to understand it better.

- **What are you trying to do** that is hard or impossible today? (A concrete example is more useful than a description of the
  feature.)
- **How do you work around it now?**
- Does the idea keep the app local-first (no data leaves the computer unless the user opts in)?
- Is there an existing setting or page it should fit into?

If this is a good fit I will label it `enhancement`, and `help wanted` if a pull request would be welcome. Nothing is promised until
then; the [roadmap](https://github.com/Yuvakunaal/local-ai-interviewer/blob/main/ROADMAP.md) is a list of intentions, not commitments.
```

## "Needs reproduction" reply

```markdown
Thanks for the report. I could not reproduce this yet, so I am adding the `needs reproduction` label.

Could you share:
1. The version or commit (`git rev-parse --short HEAD`) and your operating system.
2. Whether you use local models or cloud mode, and which model.
3. The exact steps, starting from a fresh start of the app if possible.
4. A few relevant lines from `logs/backend.log`. Please remove anything personal first; do not paste API keys, resume text or
   interview answers.

If I do not hear back in a couple of weeks I will close this for now. You are welcome to reopen it when you have more details.
```

## Closing as duplicate

```markdown
Thanks for reporting this. It is the same as #<number>, so I am closing this one to keep the discussion in one place. Please add
anything that is new, such as your operating system or a log excerpt, to that issue.
```

## Closing as not planned

```markdown
Thank you for the suggestion and for explaining your use case. I am going to close this as not planned: <honest reason, for example
"it would need data to leave the computer by default, which this project avoids">. If you want to build on the idea in a fork, the
license allows it, and I am happy to link to it.
```

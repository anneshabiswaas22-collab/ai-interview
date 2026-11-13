#!/usr/bin/env python3
"""Patch only a disposable pinned Euron checkout for an audit experiment.

The original browser suite expects immediate sign-in after signup. This
diagnostic follows the existing Mailpit email-verification flow when the API
returns 202. It does not change the upstream checkout in this repository or
turn a failed baseline into a passing baseline.
"""
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"Expected exactly one matching snippet in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


helpers = Path("e2e/helpers.ts")
spec = Path("e2e/tests/01-auth.spec.ts")
replace_once(helpers, "async function verificationToken(", "export async function verificationToken(")
replace_once(spec, "clientIp, newContext, signIn, signOut, uniq", "clientIp, newContext, signIn, signOut, uniq, verificationToken")
replace_once(spec, "async ({ browser }) => {", "async ({ browser, request }) => {")
replace_once(
    spec,
    '    await page.getByTestId("signup-submit").click();',
    '''    const responsePromise = page.waitForResponse((r) => r.url().endsWith("/api/auth/signup") && r.request().method() === "POST");
    await page.getByTestId("signup-submit").click();
    const response = await responsePromise;
    if (response.status() === 202) {
      await expect(page.getByTestId("signup-check-email")).toBeVisible();
      const token = await verificationToken(request, user.email);
      await page.goto(`/verify-email?token=${encodeURIComponent(token)}`);
    } else {
      expect(response.status()).toBe(201);
    }''',
)
print("Applied verification-aware signup diagnostic to disposable checkout")

"""
docker_antidetect_smoke.py — Anti-detection smoke test for
the camouchat-browser Docker image.

Verifies:
  A) Virtual display is properly active (screen dims, focus, DISPLAY)
  B) Browser identity is not exposing automation signals
  C) Key fingerprint APIs return plausible non-trivial values
  D) External anti-bot sites agree the browser looks human

Run inside the container:
  python tests/docker_antidetect_smoke.py

Or directly:
  docker run --rm --shm-size=2gb camouchat-browser-base:latest \\
    python tests/docker_antidetect_smoke.py
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any

from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Page


# ── Result tracking ──────────────────────────────────────────────────────────

@dataclass
class Check:
    name: str
    passed: bool
    detail: str
    critical: bool = True


@dataclass
class SmokeReport:
    checks: list[Check] = field(default_factory=list)

    def add(
        self,
        name: str,
        passed: bool,
        detail: str,
        critical: bool = True,
    ):
        self.checks.append(Check(name, passed, detail, critical))

    def print_summary(self):
        passed = [c for c in self.checks if c.passed]
        failed = [c for c in self.checks if not c.passed]
        crit_failed = [c for c in failed if c.critical]

        print("\n" + "=" * 60)
        print("  CAMOUCHAT-BROWSER DOCKER ANTI-DETECTION SMOKE REPORT")
        print("=" * 60)

        for c in self.checks:
            icon = "PASS" if c.passed else ("FAIL" if c.critical else "WARN")
            tag = f"[{icon}]"
            print(f"  {tag:<6}  {c.name}")
            if not c.passed or os.getenv("VERBOSE"):
                print(f"          {c.detail}")

        print("-" * 60)
        print(
            f"  {len(passed)}/{len(self.checks)} checks passed",
            end="",
        )
        if crit_failed:
            print(f"  |  {len(crit_failed)} CRITICAL failures")
        else:
            print("  |  All critical checks OK")
        print("=" * 60 + "\n")

        return len(crit_failed) == 0


# ── Helper ───────────────────────────────────────────────────────────────────

async def safe_eval(page: Page, js: str, default: Any = None) -> Any:
    """Evaluate JS, returning default on any error."""
    try:
        return await page.evaluate(js)
    except Exception:
        return default


# ── Check groups ─────────────────────────────────────────────────────────────

async def check_virtual_display(page: Page, report: SmokeReport):
    """A — Virtual display is up and browser sees a real screen."""

    info = await safe_eval(page, """() => ({
        screenW:     screen.width,
        screenH:     screen.height,
        outerW:      window.outerWidth,
        outerH:      window.outerHeight,
        innerW:      window.innerWidth,
        innerH:      window.innerHeight,
        colorDepth:  screen.colorDepth,
        devicePixel: window.devicePixelRatio,
        hasFocus:    document.hasFocus(),
        visState:    document.visibilityState,
    })""", {})

    sw = info.get("screenW", 0)
    sh = info.get("screenH", 0)
    report.add(
        "Screen has non-zero dimensions",
        sw > 0 and sh > 0,
        (
            f"screen={sw}x{sh}  "
            f"outer={info.get('outerW')}x{info.get('outerH')}  "
            f"inner={info.get('innerW')}x{info.get('innerH')}"
        ),
    )
    report.add(
        "Color depth is realistic (>= 24-bit)",
        info.get("colorDepth", 0) >= 24,
        f"colorDepth={info.get('colorDepth')}",
    )
    report.add(
        "devicePixelRatio is plausible (>= 1)",
        info.get("devicePixel", 0) >= 1,
        f"devicePixelRatio={info.get('devicePixel')}",
    )
    report.add(
        "Document is visible (visibilityState=visible)",
        info.get("visState") == "visible",
        f"visibilityState={info.get('visState')}",
    )
    report.add(
        "Document has focus",
        bool(info.get("hasFocus")),
        "hasFocus=True means the virtual display gave the window focus",
    )
    report.add(
        "Window chrome present (outerW >= innerW)",
        info.get("outerW", 0) >= info.get("innerW", 0),
        f"outerW={info.get('outerW')} innerW={info.get('innerW')}",
        critical=False,
    )

    display = os.environ.get("DISPLAY", "")
    report.add(
        "$DISPLAY env var is set (Xvfb active)",
        bool(display),
        f"DISPLAY={display!r}" if display else "DISPLAY not set in env",
    )


async def check_automation_signals(page: Page, report: SmokeReport):
    """B — No automation / headless / webdriver signals leaking."""

    props = await safe_eval(page, """() => ({
        webdriver:     navigator.webdriver,
        domAutomation: !!window.__webdriver_evaluate,
        selenium:      !!(window._selenium || window.callSelenium),
        puppeteer:     !!(window.__playwright || window.__pw_manual),
        cdc:           Object.keys(window).some(k => k.startsWith('cdc_')),
        nightmare:     !!window.__nightmare,
        plugins:       navigator.plugins.length,
        mimeTypes:     navigator.mimeTypes.length,
        languages:     Array.from(navigator.languages || []),
    })""", {})

    report.add(
        "navigator.webdriver is false",
        props.get("webdriver") is False,
        f"webdriver={props.get('webdriver')}",
    )
    report.add(
        "No Selenium / WebDriver globals",
        not props.get("domAutomation") and not props.get("selenium"),
        (
            f"domAutomation={props.get('domAutomation')} "
            f"selenium={props.get('selenium')}"
        ),
    )
    report.add(
        "No Puppeteer / Playwright globals",
        not props.get("puppeteer"),
        f"puppeteerGlobal={props.get('puppeteer')}",
    )
    report.add(
        "No CDP injection globals (cdc_*)",
        not props.get("cdc"),
        "window has no cdc_* keys",
    )
    report.add(
        "No Nightmare.js globals",
        not props.get("nightmare"),
        f"nightmare={props.get('nightmare')}",
    )
    report.add(
        "Plugins list is non-empty (>= 1 plugin)",
        props.get("plugins", 0) >= 1,
        f"plugins={props.get('plugins')}  mimeTypes={props.get('mimeTypes')}",
    )
    report.add(
        "navigator.languages is non-empty",
        len(props.get("languages", [])) >= 1,
        f"languages={props.get('languages')}",
    )


async def check_fingerprint_apis(page: Page, report: SmokeReport):
    """C — Canvas, WebGL, Audio, Font APIs return real / spoofed values."""

    canvas = await safe_eval(page, """() => {
        const c = document.createElement('canvas');
        c.width = 220; c.height = 30;
        const ctx = c.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillStyle = '#f60';
        ctx.fillRect(125, 1, 62, 20);
        ctx.fillStyle = '#069';
        ctx.fillText('Cwm fjordbank glyphs vext quiz', 2, 2);
        ctx.fillStyle = 'rgba(102,204,0,0.7)';
        ctx.fillText('Cwm fjordbank glyphs vext quiz', 4, 4);
        const data = c.toDataURL('image/png');
        return {len: data.length, blank: data.length < 200};
    }""", {})

    report.add(
        "Canvas fingerprint is non-blank (pixels rendered)",
        not canvas.get("blank", True) and canvas.get("len", 0) > 500,
        f"dataURL len={canvas.get('len')}  blank={canvas.get('blank')}",
    )

    gl = await safe_eval(page, """() => {
        try {
            const c = document.createElement('canvas');
            const gl = c.getContext('webgl')
                     || c.getContext('experimental-webgl');
            if (!gl) return {err: 'no_webgl'};
            const ext = gl.getExtension('WEBGL_debug_renderer_info');
            const vp = ext
                ? ext.UNMASKED_VENDOR_WEBGL
                : gl.VENDOR;
            const rp = ext
                ? ext.UNMASKED_RENDERER_WEBGL
                : gl.RENDERER;
            return {
                vendor:   gl.getParameter(vp),
                renderer: gl.getParameter(rp),
            };
        } catch(e) { return {err: String(e)}; }
    }""", {})

    renderer = (gl.get("renderer") or "").lower()
    sw_names = ("swiftshader", "llvmpipe", "softpipe")
    is_software = any(n in renderer for n in sw_names)
    report.add(
        "WebGL renderer is not a software rasterizer",
        not is_software and not gl.get("err"),
        (
            f"vendor={gl.get('vendor')!r}  "
            f"renderer={gl.get('renderer')!r}"
        ),
    )
    report.add(
        "WebGL returns a non-empty renderer string",
        bool(gl.get("renderer")) and not gl.get("err"),
        f"renderer={gl.get('renderer')!r}",
    )

    audio = await safe_eval(page, """() => {
        try {
            const ctx = new OfflineAudioContext(1, 44100, 44100);
            return {ok: true, sampleRate: ctx.sampleRate, state: ctx.state};
        } catch(e) { return {ok: false, err: String(e)}; }
    }""", {})

    report.add(
        "AudioContext is functional",
        bool(audio.get("ok")),
        (
            f"sampleRate={audio.get('sampleRate')}  "
            f"state={audio.get('state')}  "
            f"err={audio.get('err')}"
        ),
    )

    tz = await safe_eval(
        page,
        "() => Intl.DateTimeFormat().resolvedOptions().timeZone",
        "",
    )
    report.add(
        "Timezone is set (Intl API works)",
        bool(tz),
        f"timeZone={tz!r}",
    )

    platform = await safe_eval(page, "() => navigator.platform", "")
    linux_platforms = ("linux x86_64", "linux armv8l", "linux aarch64")
    report.add(
        "Platform is not bare 'Linux x86_64' (spoofed)",
        platform.lower() not in linux_platforms,
        f"navigator.platform={platform!r}",
        critical=False,
    )


async def check_external_sites(page: Page, report: SmokeReport):
    """D — Real anti-bot/fingerprinting sites — checks we look human."""

    # ── 1. Connectivity via ifconfig.me (plain-text egress IP).
    #    ip-api.com returns status=fail for RFC-1918 Docker IPs.
    print("  [ext] Checking connectivity via ifconfig.me ...")
    try:
        await page.goto(
            "https://ifconfig.me/ip",
            timeout=20000,
            wait_until="domcontentloaded",
        )
        egress_ip = (await page.inner_text("body")).strip()
        is_ip = (
            bool(egress_ip)
            and ("." in egress_ip or ":" in egress_ip)
            and len(egress_ip) < 50
        )
        report.add(
            "Outbound internet is reachable (egress IP resolved)",
            is_ip,
            f"egress_ip={egress_ip!r}",
        )
    except Exception as e:
        report.add(
            "Outbound internet is reachable (egress IP resolved)",
            False,
            str(e),
        )

    # ── 2. User-Agent — try httpbin; fall back to navigator.userAgent if it
    #    returns HTML (maintenance / CF challenge page).
    print("  [ext] Checking User-Agent (httpbin with JS fallback) ...")
    ua_from_nav = await safe_eval(page, "() => navigator.userAgent", "")
    try:
        await page.goto(
            "https://httpbin.org/headers",
            timeout=20000,
            wait_until="domcontentloaded",
        )
        raw = await page.inner_text("body")
        hdrs = json.loads(raw).get("headers", {})
        ua = hdrs.get("User-Agent", "") or ua_from_nav
    except Exception:
        ua = ua_from_nav

    report.add(
        "User-Agent contains Firefox (not HeadlessFirefox)",
        "Firefox" in ua and "HeadlessFirefox" not in ua,
        f"User-Agent={ua!r}",
    )
    report.add(
        "User-Agent does not contain 'headless'",
        "headless" not in ua.lower(),
        f"User-Agent={ua!r}",
    )

    # ── 3. browserleaks.com/canvas — webdriver check on external domain
    print("  [ext] Checking browserleaks.com/canvas ...")
    try:
        await page.goto(
            "https://browserleaks.com/canvas",
            timeout=25000,
            wait_until="domcontentloaded",
        )
        title = await page.title()
        report.add(
            "browserleaks.com/canvas loads without crash",
            "Canvas" in title or "BrowserLeaks" in title or len(title) > 2,
            f"title={title!r}",
            critical=False,
        )
        wd = await safe_eval(page, "() => navigator.webdriver", True)
        report.add(
            "navigator.webdriver is false on external page",
            wd is False,
            f"webdriver={wd}  (tested on external domain, not about:blank)",
        )
    except Exception as e:
        report.add(
            "browserleaks.com/canvas reachable",
            False,
            str(e),
            critical=False,
        )

    # ── 4. CreepJS — fingerprint aggregator.
    #    The page always contains the word "bot" in its own UI labels.
    #    We look for "headless browser" / "automated" phrases that CreepJS
    #    only writes when it actually flags the browser.
    print("  [ext] Checking abrahamjuliot.github.io/creepjs ...")
    try:
        await page.goto(
            "https://abrahamjuliot.github.io/creepjs/",
            timeout=40000,
            wait_until="domcontentloaded",
        )
        await page.wait_for_timeout(5000)

        creep = await safe_eval(page, r"""() => {
            const text = document.body.innerText || '';
            return {
                hasHeadless:  /\bheadless browser\b/i.test(text),
                hasAutomated: /\bautomated\b/i.test(text),
                hasLies:      /[1-9]\d* lie/i.test(text),
                loaded:       text.length > 500,
            };
        }""", {"loaded": False, "hasHeadless": True, "hasAutomated": True})

        loaded = creep.get("loaded", False)
        flagged = creep.get("hasHeadless") or creep.get("hasAutomated")
        report.add(
            "CreepJS: page loaded and ran JS fingerprinting",
            loaded,
            f"page_text_len > 500: {loaded}",
            critical=False,
        )
        report.add(
            "CreepJS: no 'headless browser' or 'automated' verdict",
            not flagged,
            (
                f"hasHeadless={creep.get('hasHeadless')}  "
                f"hasAutomated={creep.get('hasAutomated')}  "
                f"hasLies={creep.get('hasLies')}"
            ),
            critical=False,
        )
    except Exception as e:
        report.add("CreepJS reachable", False, str(e), critical=False)

    # ── 5. pixelscan.net — fingerprint consistency checker.
    #    We look for the word "inconsistent" — "consistent" alone appears
    #    in both passing and failing outputs, so it can't be used alone.
    print("  [ext] Checking pixelscan.net ...")
    try:
        await page.goto(
            "https://pixelscan.net/",
            timeout=30000,
            wait_until="domcontentloaded",
        )
        await page.wait_for_timeout(4000)

        scan = await safe_eval(page, r"""() => {
            const text = document.body.innerText || '';
            return {
                inconsistent: /\binconsistent\b/i.test(text),
                highRisk:     /\bhigh risk\b/i.test(text),
                loaded:       text.length > 200,
            };
        }""", {"inconsistent": True, "highRisk": True, "loaded": False})

        report.add(
            "pixelscan.net: fingerprint not flagged as inconsistent",
            not scan.get("inconsistent", True),
            (
                f"inconsistent={scan.get('inconsistent')}  "
                f"highRisk={scan.get('highRisk')}  "
                f"loaded={scan.get('loaded')}"
            ),
            critical=False,
        )
    except Exception as e:
        report.add("pixelscan.net reachable", False, str(e), critical=False)


# ── Main ─────────────────────────────────────────────────────────────────────

async def main():
    print("\nStarting anti-detection smoke test ...")
    print(f"DISPLAY={os.environ.get('DISPLAY', 'not set')}")
    report = SmokeReport()

    async with AsyncCamoufox(headless="virtual", humanize=True) as browser:
        page = await browser.new_page()

        await page.goto("about:blank")

        print("\n[A] Virtual display checks ...")
        await check_virtual_display(page, report)

        print("[B] Automation signal checks ...")
        await check_automation_signals(page, report)

        print("[C] Fingerprint API checks ...")
        await check_fingerprint_apis(page, report)

        print("\n[D] External site checks (requires internet) ...")
        await check_external_sites(page, report)

    all_ok = report.print_summary()

    report_path = os.path.join(
        os.path.dirname(__file__),
        "docker_antidetect_report.json",
    )
    with open(report_path, "w") as f:
        json.dump(
            {
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                ),
                "display": os.environ.get("DISPLAY", ""),
                "checks": [
                    {
                        "name": c.name,
                        "passed": c.passed,
                        "detail": c.detail,
                        "critical": c.critical,
                    }
                    for c in report.checks
                ],
                "all_critical_passed": all_ok,
            },
            f,
            indent=2,
        )
    print(f"Report saved to: {report_path}")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    asyncio.run(main())

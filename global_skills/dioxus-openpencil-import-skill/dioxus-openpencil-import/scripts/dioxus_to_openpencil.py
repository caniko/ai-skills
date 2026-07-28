#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "playwright==1.61.0",
#   "Pillow==12.3.0",
# ]
# ///
"""Capture hydrated Dioxus web routes and import them into OpenPencil."""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import hashlib
import html
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable, Sequence

TOOL_VERSION = "0.1.0"
OPENPENCIL_VERSION = "0.13.2"
PLAYWRIGHT_VERSION = "1.61.0"

CAPTURE_SCRIPT = r"""
async ({ selector, includeHidden, documentName, route }) => {
  const sourceRoot = document.querySelector(selector);
  if (!sourceRoot) throw new Error(`No element matched selector: ${selector}`);

  const unsupported = [];
  const assetFailures = [];
  const warnings = [];
  const stats = {
    sourceElements: 0,
    capturedElements: 0,
    textLayers: 0,
    embeddedImages: 0,
    embeddedSvg: 0,
    embeddedCanvas: 0,
    skippedHidden: 0,
    skippedZeroSize: 0,
  };
  let sequence = 0;

  const NON_RENDERED = new Set([
    'SCRIPT', 'STYLE', 'LINK', 'META', 'NOSCRIPT', 'TEMPLATE', 'TITLE', 'HEAD', 'SOURCE'
  ]);
  const finite = (value, fallback = 0) => Number.isFinite(value) ? value : fallback;
  const px = (value) => `${finite(value).toFixed(2)}px`;
  const positivePx = (value) => `${Math.max(0, finite(value)).toFixed(2)}px`;
  const isTransparent = (value) =>
    !value || value === 'transparent' || value === 'rgba(0, 0, 0, 0)' || value === 'rgba(0,0,0,0)';

  function safeLayerName(element, fallbackTag = 'layer') {
    const candidates = [
      element.id,
      element.getAttribute?.('data-testid'),
      element.getAttribute?.('aria-label'),
      element.getAttribute?.('name'),
      Array.from(element.classList || []).find((name) => name && !name.includes(':')),
      element.getAttribute?.('role'),
      fallbackTag,
    ];
    const raw = candidates.find((value) => value && String(value).trim()) || fallbackTag;
    const clean = String(raw)
      .trim()
      .replace(/[^a-zA-Z0-9_-]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 56) || fallbackTag;
    sequence += 1;
    return `${clean}-${sequence}`;
  }

  function sourcePath(element) {
    const parts = [];
    let current = element;
    while (current && current.nodeType === Node.ELEMENT_NODE && parts.length < 6) {
      let part = current.tagName.toLowerCase();
      if (current.id) {
        part += `#${current.id}`;
        parts.unshift(part);
        break;
      }
      const parent = current.parentElement;
      if (parent) {
        const siblings = Array.from(parent.children).filter((node) => node.tagName === current.tagName);
        if (siblings.length > 1) part += `:nth-of-type(${siblings.indexOf(current) + 1})`;
      }
      parts.unshift(part);
      current = parent;
    }
    return parts.join(' > ');
  }

  function reportUnsupported(element, style) {
    const checks = [
      ['transform', style.transform, 'none'],
      ['filter', style.filter, 'none'],
      ['backdrop-filter', style.backdropFilter || style.getPropertyValue('backdrop-filter'), 'none'],
      ['mask-image', style.maskImage || style.getPropertyValue('mask-image'), 'none'],
      ['mix-blend-mode', style.mixBlendMode, 'normal'],
      ['clip-path', style.clipPath, 'none'],
      ['border-image-source', style.borderImageSource, 'none'],
      ['outline-style', style.outlineStyle, 'none'],
      ['-webkit-text-stroke-width', style.getPropertyValue('-webkit-text-stroke-width'), '0px'],
    ];
    for (const [property, value, neutral] of checks) {
      if (value && value !== neutral) {
        unsupported.push({ path: sourcePath(element), property, value: String(value).slice(0, 240) });
      }
    }
    if (style.backgroundImage && style.backgroundImage !== 'none') {
      unsupported.push({
        path: sourcePath(element),
        property: style.backgroundImage.includes('gradient(') ? 'gradient' : 'background-image',
        value: String(style.backgroundImage).slice(0, 240),
      });
    }
    const zIndex = style.zIndex;
    if (zIndex && zIndex !== 'auto' && zIndex !== '0') {
      warnings.push({
        path: sourcePath(element),
        property: 'z-index',
        value: zIndex,
        note: 'DOM order is preserved; complex stacking contexts may render differently.',
      });
    }
  }

  function isVisible(element, style, rect) {
    if (includeHidden) return true;
    if (style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') return false;
    if (Number.parseFloat(style.opacity || '1') === 0) return false;
    if (rect.width <= 0.01 && rect.height <= 0.01) return false;
    return true;
  }

  function effectiveSolidBackground(source) {
    let current = source;
    while (current && current.nodeType === Node.ELEMENT_NODE) {
      const value = getComputedStyle(current).backgroundColor;
      if (!isTransparent(value)) return value;
      current = current.parentElement;
    }
    return 'rgb(255, 255, 255)';
  }

  function applyBoxStyle(target, source, rect, parentRect, isRoot) {
    const style = getComputedStyle(source);
    target.style.boxSizing = 'border-box';
    target.style.display = 'block';
    target.style.position = isRoot ? 'relative' : 'absolute';
    if (!isRoot) {
      target.style.left = px(rect.left - parentRect.left);
      target.style.top = px(rect.top - parentRect.top);
    }
    target.style.width = positivePx(rect.width);
    target.style.height = positivePx(rect.height);

    let backgroundColor = style.backgroundColor;
    if (isRoot && isTransparent(backgroundColor)) backgroundColor = effectiveSolidBackground(source.parentElement);
    if (!isTransparent(backgroundColor)) target.style.backgroundColor = backgroundColor;

    const copied = [
      'border-top-width', 'border-right-width', 'border-bottom-width', 'border-left-width',
      'border-top-style', 'border-right-style', 'border-bottom-style', 'border-left-style',
      'border-top-color', 'border-right-color', 'border-bottom-color', 'border-left-color',
      'border-top-left-radius', 'border-top-right-radius',
      'border-bottom-right-radius', 'border-bottom-left-radius',
      'box-shadow', 'opacity',
    ];
    for (const property of copied) {
      const value = style.getPropertyValue(property);
      if (value) target.style.setProperty(property, value);
    }

    const overflowValues = [style.overflow, style.overflowX, style.overflowY];
    target.style.overflow = overflowValues.some((value) => value === 'hidden' || value === 'clip')
      ? 'hidden'
      : 'visible';

    target.setAttribute('data-op-source', sourcePath(source));
    target.setAttribute('data-op-tag', source.tagName.toLowerCase());
    target.className = safeLayerName(source, source.tagName.toLowerCase());
    reportUnsupported(source, style);
  }

  function applyTextStyle(target, style, width, height) {
    target.style.display = 'block';
    target.style.width = positivePx(width);
    target.style.height = positivePx(height);
    const properties = [
      'color', 'font-family', 'font-size', 'font-weight', 'font-style',
      'line-height', 'letter-spacing', 'text-align', 'text-decoration-line',
      'text-transform', 'white-space', 'text-shadow', 'opacity',
    ];
    for (const property of properties) {
      const value = style.getPropertyValue(property);
      if (value) target.style.setProperty(property, value);
    }
    if (style.whiteSpace !== 'nowrap') target.style.whiteSpace = 'pre-wrap';
  }

  function normalizedText(text, whiteSpace) {
    if (whiteSpace === 'pre' || whiteSpace === 'pre-wrap' || whiteSpace === 'break-spaces') return text;
    return text.replace(/\s+/g, ' ');
  }

  function captureTextNode(textNode, parentRect, parentStyle, ownerElement) {
    const raw = textNode.nodeValue || '';
    if (!raw.trim()) return null;
    const range = document.createRange();
    range.selectNodeContents(textNode);
    const rect = range.getBoundingClientRect();
    range.detach?.();
    if (rect.width <= 0.01 || rect.height <= 0.01) return null;

    const outer = document.createElement('div');
    outer.style.position = 'absolute';
    outer.style.left = px(rect.left - parentRect.left);
    outer.style.top = px(rect.top - parentRect.top);
    outer.style.width = positivePx(rect.width);
    outer.style.height = positivePx(rect.height);
    outer.style.overflow = 'visible';
    outer.style.boxSizing = 'border-box';
    outer.className = safeLayerName(ownerElement, 'text');
    outer.setAttribute('data-op-source', `${sourcePath(ownerElement)}::text`);

    const textFrame = document.createElement('span');
    applyTextStyle(textFrame, parentStyle, rect.width, rect.height);
    textFrame.textContent = normalizedText(raw, parentStyle.whiteSpace);
    outer.appendChild(textFrame);
    stats.textLayers += 1;
    return outer;
  }

  function bytesToDataUrl(bytes, mimeType) {
    let binary = '';
    const chunkSize = 0x8000;
    for (let offset = 0; offset < bytes.length; offset += chunkSize) {
      binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
    }
    return `data:${mimeType || 'application/octet-stream'};base64,${btoa(binary)}`;
  }

  async function fetchAsDataUrl(url, element) {
    if (!url) return null;
    if (url.startsWith('data:') && url.includes(';base64,')) return url;
    try {
      const response = await fetch(url, { credentials: 'include' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const buffer = new Uint8Array(await response.arrayBuffer());
      return bytesToDataUrl(buffer, response.headers.get('content-type') || 'application/octet-stream');
    } catch (error) {
      assetFailures.push({ path: sourcePath(element), url: String(url).slice(0, 240), error: String(error) });
      return null;
    }
  }

  async function svgAsDataUrl(svg) {
    const clone = svg.cloneNode(true);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    const sourceNodes = [svg, ...svg.querySelectorAll('*')];
    const cloneNodes = [clone, ...clone.querySelectorAll('*')];
    const svgProperties = [
      'fill', 'fill-opacity', 'stroke', 'stroke-width', 'stroke-opacity', 'stroke-linecap',
      'stroke-linejoin', 'opacity', 'color', 'font-family', 'font-size', 'font-weight',
    ];
    for (let index = 0; index < Math.min(sourceNodes.length, cloneNodes.length); index += 1) {
      const computed = getComputedStyle(sourceNodes[index]);
      for (const property of svgProperties) {
        const value = computed.getPropertyValue(property);
        if (value) cloneNodes[index].style.setProperty(property, value);
      }
    }
    const sourceImages = [...svg.querySelectorAll('image')];
    const cloneImages = [...clone.querySelectorAll('image')];
    for (let index = 0; index < sourceImages.length; index += 1) {
      const href = sourceImages[index].href?.baseVal || sourceImages[index].getAttribute('href');
      const dataUrl = href ? await fetchAsDataUrl(new URL(href, document.baseURI).href, sourceImages[index]) : null;
      if (dataUrl && cloneImages[index]) {
        cloneImages[index].setAttribute('href', dataUrl);
        cloneImages[index].removeAttribute('xlink:href');
      }
    }
    const serialized = new XMLSerializer().serializeToString(clone);
    return bytesToDataUrl(new TextEncoder().encode(serialized), 'image/svg+xml');
  }

  function appendSyntheticValue(target, value, source, rect) {
    if (!value) return;
    const style = getComputedStyle(source);
    const left = Number.parseFloat(style.paddingLeft || '0') || 0;
    const top = Number.parseFloat(style.paddingTop || '0') || 0;
    const right = Number.parseFloat(style.paddingRight || '0') || 0;
    const bottom = Number.parseFloat(style.paddingBottom || '0') || 0;
    const width = Math.max(0, rect.width - left - right);
    const height = Math.max(0, rect.height - top - bottom);

    const outer = document.createElement('div');
    outer.style.position = 'absolute';
    outer.style.left = px(left);
    outer.style.top = px(top);
    outer.style.width = positivePx(width);
    outer.style.height = positivePx(height);
    outer.style.overflow = 'hidden';
    outer.className = safeLayerName(source, 'value');

    const textFrame = document.createElement('span');
    applyTextStyle(textFrame, style, width, height);
    textFrame.textContent = value;
    outer.appendChild(textFrame);
    target.appendChild(outer);
    stats.textLayers += 1;
  }

  async function captureElement(source, parentRect, isRoot = false) {
    stats.sourceElements += 1;
    if (NON_RENDERED.has(source.tagName)) return null;

    const style = getComputedStyle(source);
    const rect = source.getBoundingClientRect();
    if (!isVisible(source, style, rect)) {
      if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
        stats.skippedHidden += 1;
      } else {
        stats.skippedZeroSize += 1;
      }
      return null;
    }

    if (style.display === 'contents') {
      const fragment = document.createDocumentFragment();
      for (const child of source.childNodes) {
        if (child.nodeType === Node.ELEMENT_NODE) {
          const captured = await captureElement(child, parentRect, false);
          if (captured) fragment.appendChild(captured);
        } else if (child.nodeType === Node.TEXT_NODE) {
          const textLayer = captureTextNode(child, parentRect, style, source);
          if (textLayer) fragment.appendChild(textLayer);
        }
      }
      return fragment;
    }

    let target;
    const tag = source.tagName.toLowerCase();
    if (tag === 'img') {
      target = document.createElement('img');
      const dataUrl = await fetchAsDataUrl(source.currentSrc || source.src, source);
      if (dataUrl) {
        target.src = dataUrl;
        stats.embeddedImages += 1;
      } else if (source.currentSrc || source.src) {
        target.src = source.currentSrc || source.src;
      }
      target.style.objectFit = style.objectFit || 'fill';
    } else if (tag === 'svg') {
      target = document.createElement('img');
      target.src = await svgAsDataUrl(source);
      target.style.objectFit = 'fill';
      stats.embeddedSvg += 1;
    } else if (tag === 'canvas') {
      target = document.createElement('img');
      try {
        target.src = source.toDataURL('image/png');
        stats.embeddedCanvas += 1;
      } catch (error) {
        assetFailures.push({ path: sourcePath(source), url: 'canvas:', error: String(error) });
      }
      target.style.objectFit = 'fill';
    } else if (tag === 'video') {
      target = document.createElement('img');
      const poster = source.poster ? await fetchAsDataUrl(source.poster, source) : null;
      if (poster) {
        target.src = poster;
        stats.embeddedImages += 1;
      } else {
        unsupported.push({ path: sourcePath(source), property: 'video', value: 'No embeddable poster frame' });
      }
      target.style.objectFit = style.objectFit || 'cover';
    } else {
      target = document.createElement('div');
    }

    applyBoxStyle(target, source, rect, parentRect, isRoot);
    stats.capturedElements += 1;

    if (['img', 'svg', 'canvas', 'video'].includes(tag)) return target;

    if (tag === 'input') {
      const inputType = (source.type || 'text').toLowerCase();
      if (inputType === 'checkbox' && source.checked) {
        appendSyntheticValue(target, '✓', source, rect);
      } else if (inputType === 'radio' && source.checked) {
        appendSyntheticValue(target, '●', source, rect);
      } else if (inputType === 'password') {
        if (source.value) {
          appendSyntheticValue(target, '••••••••', source, rect);
          warnings.push({
            path: sourcePath(source),
            property: 'password-value',
            value: 'redacted',
            note: 'Password input content was intentionally omitted from generated artifacts.',
          });
        } else {
          appendSyntheticValue(target, source.placeholder || '', source, rect);
        }
      } else if (!['hidden', 'checkbox', 'radio', 'file', 'color', 'range'].includes(inputType)) {
        appendSyntheticValue(target, source.value || source.placeholder || '', source, rect);
      }
      return target;
    }
    if (tag === 'textarea') {
      appendSyntheticValue(target, source.value || source.placeholder || '', source, rect);
      return target;
    }
    if (tag === 'select') {
      appendSyntheticValue(target, source.selectedOptions?.[0]?.textContent || '', source, rect);
      return target;
    }
    if (tag === 'iframe') {
      unsupported.push({ path: sourcePath(source), property: 'iframe', value: source.src || 'inline frame' });
      return target;
    }

    for (const child of source.childNodes) {
      if (child.nodeType === Node.ELEMENT_NODE) {
        const captured = await captureElement(child, rect, false);
        if (captured) target.appendChild(captured);
      } else if (child.nodeType === Node.TEXT_NODE) {
        const textLayer = captureTextNode(child, rect, style, source);
        if (textLayer) target.appendChild(textLayer);
      }
    }
    return target;
  }

  const rootRect = sourceRoot.getBoundingClientRect();
  if (rootRect.width <= 0 || rootRect.height <= 0) {
    throw new Error(`Selected root has zero size: ${selector}`);
  }

  const capturedRoot = await captureElement(sourceRoot, rootRect, true);
  if (!capturedRoot) throw new Error(`Selected root was not renderable: ${selector}`);
  if (capturedRoot.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    wrapper.style.width = positivePx(rootRect.width);
    wrapper.style.height = positivePx(rootRect.height);
    wrapper.style.backgroundColor = effectiveSolidBackground(sourceRoot.parentElement);
    wrapper.className = documentName;
    wrapper.appendChild(capturedRoot);
    return {
      html: wrapper.outerHTML,
      report: {
        route, selector, root: { width: rootRect.width, height: rootRect.height },
        stats, unsupported, assetFailures, warnings,
      },
    };
  }
  capturedRoot.className = documentName;
  capturedRoot.setAttribute('data-op-route', route);

  const pseudoElements = [];
  for (const element of [sourceRoot, ...sourceRoot.querySelectorAll('*')]) {
    for (const pseudo of ['::before', '::after', '::marker']) {
      const pseudoStyle = getComputedStyle(element, pseudo);
      const content = pseudoStyle.content;
      if (content && content !== 'none' && content !== 'normal' && content !== '""') {
        pseudoElements.push({ path: sourcePath(element), pseudo, content: String(content).slice(0, 160) });
      }
    }
  }
  if (pseudoElements.length) {
    unsupported.push(...pseudoElements.map((item) => ({ ...item, property: item.pseudo })));
  }

  return {
    html: capturedRoot.outerHTML,
    report: {
      route,
      selector,
      root: { x: rootRect.x, y: rootRect.y, width: rootRect.width, height: rootRect.height },
      stats,
      unsupported,
      assetFailures,
      warnings,
    },
  };
}
"""


@dataclasses.dataclass(slots=True)
class RouteSpec:
    path: str
    name: str


def log(message: str) -> None:
    print(f"[dioxus-openpencil] {message}", flush=True)


def warn(message: str) -> None:
    print(f"[dioxus-openpencil] warning: {message}", file=sys.stderr, flush=True)


def parse_viewport(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"\s*(\d+)\s*[xX,]\s*(\d+)\s*", value)
    if not match:
        raise argparse.ArgumentTypeError("viewport must look like 1440x900")
    width, height = int(match.group(1)), int(match.group(2))
    if width < 200 or height < 200 or width > 10000 or height > 10000:
        raise argparse.ArgumentTypeError("viewport dimensions must be between 200 and 10000")
    return width, height


SENSITIVE_QUERY_KEY = re.compile(r"(?:token|secret|password|passwd|auth|session|api[-_]?key|code)", re.I)


def redact_url_for_report(value: str) -> str:
    """Remove URL credentials/fragments and redact common secret-bearing query parameters."""
    parsed = urllib.parse.urlsplit(value)
    hostname = parsed.hostname or ""
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    if parsed.port:
        hostname = f"{hostname}:{parsed.port}"
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    safe_query = [
        (key, "[REDACTED]" if SENSITIVE_QUERY_KEY.search(key) else item)
        for key, item in query
    ]
    return urllib.parse.urlunsplit(
        (parsed.scheme, hostname if parsed.netloc else "", parsed.path, urllib.parse.urlencode(safe_query), "")
    )


def slugify(value: str, fallback: str = "index") -> str:
    parsed = urllib.parse.urlsplit(value)
    raw = parsed.path.strip("/") or fallback
    if parsed.query:
        raw += f"-query-{hashlib.sha256(parsed.query.encode('utf-8')).hexdigest()[:10]}"
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw).strip("-._").lower()
    return slug[:100] or fallback


def route_name(path: str) -> str:
    parsed = urllib.parse.urlsplit(path)
    if parsed.path in ("", "/"):
        return "Home"
    return " / ".join(
        part.replace("-", " ").replace("_", " ").title()
        for part in parsed.path.split("/")
        if part
    )


def discover_dioxus_routes(project: Path) -> tuple[list[RouteSpec], list[str]]:
    route_pattern = re.compile(r"#\s*\[\s*route\s*\(\s*r?[#]*\"([^\"]+)\"[#]*\s*\)\s*\]")
    static: dict[str, RouteSpec] = {}
    skipped: set[str] = set()
    for path in project.rglob("*.rs"):
        if any(part in {"target", ".git", "node_modules", ".dioxus"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for raw in route_pattern.findall(text):
            route = raw.strip()
            if not route.startswith("/"):
                continue
            if any(token in route for token in (":", "{", "}", "*", "..")):
                skipped.add(route)
                continue
            static.setdefault(route, RouteSpec(route, route_name(route)))
    return sorted(static.values(), key=lambda item: (item.path.count("/"), item.path)), sorted(skipped)


def validate_project(project: Path) -> None:
    cargo = project / "Cargo.toml"
    dioxus = project / "Dioxus.toml"
    if not cargo.exists():
        raise RuntimeError(f"No Cargo.toml found in {project}")
    if dioxus.exists():
        return
    manifests = [cargo]
    manifests.extend(
        path
        for path in project.rglob("Cargo.toml")
        if path != cargo
        and not any(part in {"target", ".git", "node_modules", ".dioxus"} for part in path.parts)
    )
    for manifest in manifests:
        with contextlib.suppress(OSError, UnicodeDecodeError):
            if "dioxus" in manifest.read_text(encoding="utf-8").lower():
                return
    raise RuntimeError(f"{project} does not look like a Dioxus project")


def http_ready(url: str, timeout: float = 2.0) -> bool:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": f"dioxus-openpencil-import/{TOOL_VERSION}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status < 500
    except urllib.error.HTTPError as error:
        return error.code < 500
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def wait_for_url(url: str, process: subprocess.Popen[str] | None, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if http_ready(url):
            return
        if process is not None and process.poll() is not None:
            raise RuntimeError(f"Serve command exited with code {process.returncode}; inspect serve.log")
        time.sleep(0.5)
    raise TimeoutError(f"Timed out waiting for {url}; inspect serve.log")


def drain_process_output(process: subprocess.Popen[str], destination: Path) -> threading.Thread:
    def worker() -> None:
        with destination.open("w", encoding="utf-8") as handle:
            assert process.stdout is not None
            for line in process.stdout:
                handle.write(line)
                handle.flush()

    thread = threading.Thread(target=worker, name="dioxus-serve-log", daemon=True)
    thread.start()
    return thread


@contextlib.contextmanager
def maybe_serve_project(
    project: Path | None,
    serve_command: str,
    base_url: str,
    output_dir: Path,
    timeout: float,
    no_serve: bool,
):
    ready = http_ready(base_url)
    if project is None or no_serve or ready:
        if ready:
            log(f"Using existing server at {redact_url_for_report(base_url)}")
        yield None
        return

    command = shlex.split(serve_command)
    if not command:
        raise RuntimeError("Serve command is empty")
    if shutil.which(command[0]) is None:
        raise RuntimeError(f"Serve executable not found: {command[0]}")

    log(f"Starting Dioxus server: {shlex.join(command)}")
    process = subprocess.Popen(
        command,
        cwd=project,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=(os.name != "nt"),
    )
    thread = drain_process_output(process, output_dir / "serve.log")
    try:
        wait_for_url(base_url, process, timeout)
        log(f"Dioxus server is ready at {redact_url_for_report(base_url)}")
        yield process
    finally:
        if process.poll() is None:
            if os.name == "nt":
                process.terminate()
            else:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    process.kill()
                else:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        thread.join(timeout=2)


def browser_executable(explicit: str | None) -> str | None:
    """Resolve an explicitly selected browser; otherwise use Playwright's pinned Chromium."""
    if not explicit:
        return None
    command = shutil.which(explicit)
    if command:
        return command
    path = Path(explicit).expanduser().resolve()
    if not path.exists():
        raise RuntimeError(f"Browser executable does not exist: {path}")
    return str(path)


def openpencil_command(explicit: str | None, allow_npx: bool) -> list[str] | None:
    if explicit:
        command = shlex.split(explicit)
        if not command:
            raise RuntimeError("OpenPencil command is empty")
        return command
    installed = shutil.which("openpencil")
    if installed:
        return [installed]
    if allow_npx and shutil.which("npx"):
        return ["npx", "--yes", f"@open-pencil/cli@{OPENPENCIL_VERSION}"]
    return None


def run_command(
    command: Sequence[str], cwd: Path, timeout: float = 300
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return completed


def import_html(
    command: Sequence[str],
    html_path: Path,
    fig_path: Path,
    page_name: str,
    working_dir: Path,
) -> dict[str, Any]:
    args = [
        *command,
        "import",
        str(html_path),
        "-o",
        str(fig_path),
        "--page-name",
        page_name,
        "--json",
    ]
    result = run_command(args, working_dir)
    return {
        "command": list(result.args),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "output": str(fig_path),
        "status": (
            "ok"
            if result.returncode == 0 and fig_path.exists() and fig_path.stat().st_size > 0
            else "failed"
        ),
    }


def export_fig(
    command: Sequence[str], fig_path: Path, png_path: Path, working_dir: Path
) -> dict[str, Any]:
    # OpenPencil 0.13.x export has no --json option.
    scales: list[float | None] = [None, 0.25, 0.1, 0.04, 0.02]
    attempts: list[dict[str, Any]] = []
    for scale in scales:
        args = [*command, "export", str(fig_path), "-f", "png", "-o", str(png_path)]
        if scale is not None:
            args.extend(["-s", str(scale)])
        result = run_command(args, working_dir)
        attempt = {
            "command": list(result.args),
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "output": str(png_path),
            "scale": scale,
        }
        attempts.append(attempt)
        if result.returncode == 0 and png_path.exists() and png_path.stat().st_size > 0:
            attempt["status"] = "ok"
            return {**attempt, "attempts": attempts}
    final = attempts[-1]
    return {**final, "status": "failed", "attempts": attempts}


def compare_images(reference: Path, candidate: Path, diff_path: Path) -> dict[str, Any]:
    from PIL import Image, ImageChops, ImageEnhance, ImageStat

    with Image.open(reference).convert("RGBA") as source, Image.open(candidate).convert("RGBA") as imported:
        width = max(source.width, imported.width)
        height = max(source.height, imported.height)
        white = (255, 255, 255, 255)
        source_canvas = Image.new("RGBA", (width, height), white)
        imported_canvas = Image.new("RGBA", (width, height), white)
        source_canvas.alpha_composite(source, (0, 0))
        imported_canvas.alpha_composite(imported, (0, 0))
        difference = ImageChops.difference(
            source_canvas.convert("RGB"), imported_canvas.convert("RGB")
        )
        stats = ImageStat.Stat(difference)
        mae_channels = [value / 255.0 for value in stats.mean]
        mae = sum(mae_channels) / len(mae_channels)
        ImageEnhance.Contrast(difference).enhance(3.0).save(diff_path)
        return {
            "referenceSize": [source.width, source.height],
            "candidateSize": [imported.width, imported.height],
            "canvasSize": [width, height],
            "meanAbsoluteError": round(mae, 6),
            "meanAbsoluteErrorPercent": round(mae * 100, 3),
            "diff": str(diff_path),
        }


def write_combined_html(
    route_records: Sequence[dict[str, Any]], destination: Path, project_name: str
) -> None:
    cards: list[str] = []
    for record in route_records:
        fragment = Path(record["html"]).read_text(encoding="utf-8")
        name = html.escape(str(record["name"]), quote=False)
        route = html.escape(str(record["route"]), quote=False)
        cards.append(
            f'''<div class="route-{slugify(record['route'])}" style="display:flex;flex-direction:column;gap:12px;align-items:flex-start;">
  <p style="color:#111827;font-family:Inter,Arial,sans-serif;font-size:18px;font-weight:700;line-height:24px;">{name}</p>
  <p style="color:#6b7280;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;font-weight:400;line-height:16px;">{route}</p>
  {fragment}
</div>'''
        )
    document = f'''<div id="{slugify(project_name, 'dioxus-project')}" style="display:flex;flex-direction:row;flex-wrap:wrap;align-items:flex-start;gap:64px;padding:64px;background-color:#f3f4f6;">
{os.linesep.join(cards)}
</div>
'''
    destination.write_text(document, encoding="utf-8")


def route_url(base_url: str, route: str) -> str:
    if route.startswith("http://") or route.startswith("https://"):
        return route
    return urllib.parse.urljoin(base_url.rstrip("/") + "/", route.lstrip("/"))


def relative_to_output(value: Any, output_dir: Path) -> Any:
    if isinstance(value, dict):
        return {key: relative_to_output(item, output_dir) for key, item in value.items()}
    if isinstance(value, list):
        return [relative_to_output(item, output_dir) for item in value]
    if isinstance(value, str):
        with contextlib.suppress(ValueError, OSError):
            path = Path(value)
            if path.is_absolute():
                return str(path.relative_to(output_dir))
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture hydrated Dioxus routes and import them into OpenPencil.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--project", type=Path, help="Dioxus project directory to serve")
    source.add_argument("--url", help="Already-running Dioxus/web base URL")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8080",
        help="URL expected from the serve command",
    )
    parser.add_argument(
        "--serve-command",
        default="dx serve --web",
        help="Command used to launch a local Dioxus project",
    )
    parser.add_argument("--no-serve", action="store_true", help="Do not launch a server")
    parser.add_argument("--serve-timeout", type=float, default=180.0)
    parser.add_argument("--route", action="append", default=[], help="Route to capture; repeatable")
    parser.add_argument("--no-discover-routes", action="store_true")
    parser.add_argument("--selector", default="body", help="CSS selector for the captured root")
    parser.add_argument("--viewport", type=parse_viewport, default=(1440, 900))
    parser.add_argument("--wait-selector", help="Wait for this selector before capture")
    parser.add_argument("--settle-ms", type=int, default=750)
    parser.add_argument("--navigation-timeout", type=float, default=90.0)
    parser.add_argument("--setup-js", type=Path, help="Async JavaScript function body")
    parser.add_argument("--storage-state", type=Path, help="Playwright storage-state JSON")
    parser.add_argument("--header", action="append", default=[], help="Name=Value; repeatable")
    parser.add_argument(
        "--color-scheme",
        choices=["light", "dark", "no-preference"],
        default="light",
    )
    parser.add_argument("--include-hidden", action="store_true")
    parser.add_argument("--headful", action="store_true")
    parser.add_argument(
        "--browser-executable",
        help="Specific Chrome/Chromium executable path or command name",
    )
    parser.add_argument("--out", type=Path, default=Path(".openpencil-import"))
    parser.add_argument("--project-name")
    parser.add_argument("--capture-only", action="store_true")
    parser.add_argument(
        "--openpencil-command",
        help="Command prefix, e.g. 'openpencil' or 'bunx @open-pencil/cli'",
    )
    parser.add_argument("--no-npx", action="store_true")
    parser.add_argument("--no-verify-render", action="store_true")
    parser.add_argument("--no-combine", action="store_true")
    return parser


def parse_headers(values: Iterable[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise RuntimeError(f"Header must use Name=Value syntax: {value}")
        name, content = value.split("=", 1)
        if not name.strip():
            raise RuntimeError(f"Header name is empty: {value}")
        headers[name.strip()] = content
    return headers


def deduplicate_routes(routes: Sequence[RouteSpec]) -> list[RouteSpec]:
    result: list[RouteSpec] = []
    seen: set[str] = set()
    for route in routes:
        if route.path in seen:
            continue
        seen.add(route.path)
        result.append(route)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project = args.project.expanduser().resolve() if args.project else None
    if project:
        validate_project(project)
    if project is None and not args.url:
        project = Path.cwd().resolve()
        validate_project(project)

    output_dir = args.out.expanduser()
    if not output_dir.is_absolute():
        output_dir = ((project or Path.cwd()) / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    routes_dir = output_dir / "routes"
    routes_dir.mkdir(parents=True, exist_ok=True)

    base_url = args.url or args.base_url
    route_specs = [RouteSpec(path, route_name(path)) for path in args.route]
    skipped_dynamic: list[str] = []
    if not route_specs and project and not args.no_discover_routes:
        route_specs, skipped_dynamic = discover_dioxus_routes(project)
        if route_specs:
            log(f"Discovered {len(route_specs)} static Dioxus route(s)")
    if not route_specs:
        route_specs = [RouteSpec("/", "Home")]
    route_specs = deduplicate_routes(route_specs)

    project_name = args.project_name or (
        project.name if project else urllib.parse.urlsplit(base_url).hostname or "Dioxus Project"
    )
    serve_url = args.base_url if project else base_url
    openpencil = None if args.capture_only else openpencil_command(
        args.openpencil_command, not args.no_npx
    )
    if not args.capture_only and openpencil is None:
        raise RuntimeError(
            "OpenPencil CLI was not found. Install @open-pencil/cli, provide "
            "--openpencil-command, or use --capture-only."
        )

    summary: dict[str, Any] = {
        "tool": "dioxus-openpencil-import",
        "version": TOOL_VERSION,
        "openpencilVersion": OPENPENCIL_VERSION,
        "project": str(project) if project else None,
        "baseUrl": redact_url_for_report(base_url),
        "selector": args.selector,
        "viewport": list(args.viewport),
        "skippedDynamicRoutes": skipped_dynamic,
        "routes": [],
    }

    setup_js = args.setup_js.read_text(encoding="utf-8") if args.setup_js else None
    extra_headers = parse_headers(args.header)
    browser_path = browser_executable(args.browser_executable)

    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError(
            f"Playwright is required. Run with uv: uv run {Path(__file__).name} ... ({error})"
        ) from error

    with maybe_serve_project(
        project,
        args.serve_command,
        serve_url,
        output_dir,
        args.serve_timeout,
        args.no_serve,
    ):
        with sync_playwright() as playwright:
            launch_options: dict[str, Any] = {"headless": not args.headful}
            if browser_path:
                launch_options["executable_path"] = browser_path
            try:
                browser = playwright.chromium.launch(**launch_options)
            except PlaywrightError as error:
                if browser_path:
                    raise RuntimeError(f"Could not launch browser {browser_path}: {error}") from error
                raise RuntimeError(
                    "Chromium is unavailable. Run: "
                    f"uvx --from playwright=={PLAYWRIGHT_VERSION} playwright install chromium"
                ) from error

            context_options: dict[str, Any] = {
                "viewport": {"width": args.viewport[0], "height": args.viewport[1]},
                "device_scale_factor": 1,
                "color_scheme": args.color_scheme,
            }
            if args.storage_state:
                context_options["storage_state"] = str(args.storage_state.expanduser().resolve())
            if extra_headers:
                context_options["extra_http_headers"] = extra_headers
            context = browser.new_context(**context_options)

            used_slugs: set[str] = set()
            for route_spec in route_specs:
                base_slug = slugify(route_spec.path)
                slug = base_slug
                suffix = 2
                while slug in used_slugs:
                    slug = f"{base_slug}-{suffix}"
                    suffix += 1
                used_slugs.add(slug)

                route_dir = routes_dir / slug
                route_dir.mkdir(parents=True, exist_ok=True)
                url = route_url(base_url, route_spec.path)
                safe_route = redact_url_for_report(route_spec.path)
                safe_url = redact_url_for_report(url)
                log(f"Capturing {safe_route} from {safe_url}")
                record: dict[str, Any] = {
                    "route": safe_route,
                    "name": route_spec.name,
                    "url": safe_url,
                    "status": "started",
                }
                page = context.new_page()
                page.set_default_timeout(args.navigation_timeout * 1000)
                page.set_default_navigation_timeout(args.navigation_timeout * 1000)

                try:
                    response = page.goto(url, wait_until="domcontentloaded")
                    if response is not None:
                        record["httpStatus"] = response.status
                    page.wait_for_function("document.body && document.body.children.length > 0")
                    with contextlib.suppress(PlaywrightTimeoutError):
                        page.wait_for_load_state(
                            "load", timeout=min(args.navigation_timeout * 1000, 30000)
                        )
                    page.add_style_tag(
                        content=(
                            "*,*::before,*::after{animation:none!important;"
                            "transition:none!important;caret-color:transparent!important;}"
                        )
                    )
                    if args.wait_selector:
                        page.locator(args.wait_selector).first.wait_for(state="visible")
                    if setup_js:
                        page.evaluate(
                            "([source, route]) => { "
                            "window.__DIOXUS_OPENPENCIL_ROUTE__ = route; "
                            "return (new Function(`return (async () => {\\n${source}\\n})()`))(); }",
                            [setup_js, route_spec.path],
                        )
                    page.wait_for_timeout(max(0, args.settle_ms))

                    root = page.locator(args.selector).first
                    root.wait_for(state="visible")
                    screenshot_path = route_dir / "browser.png"
                    root.screenshot(path=str(screenshot_path), animations="disabled")

                    captured = page.evaluate(
                        CAPTURE_SCRIPT,
                        {
                            "selector": args.selector,
                            "includeHidden": args.include_hidden,
                            "documentName": f"route-{slug}",
                            "route": safe_route,
                        },
                    )
                    html_path = route_dir / "capture.html"
                    html_path.write_text(captured["html"] + "\n", encoding="utf-8")
                    capture_report_path = route_dir / "capture.json"
                    capture_report = captured["report"]
                    final_url = redact_url_for_report(page.url)
                    capture_report.update(
                        {
                            "url": safe_url,
                            "finalUrl": final_url,
                            "httpStatus": record.get("httpStatus"),
                            "pageTitle": page.title(),
                            "name": route_spec.name,
                            "viewport": list(args.viewport),
                            "html": str(html_path),
                            "screenshot": str(screenshot_path),
                        }
                    )
                    if record.get("httpStatus", 200) >= 400:
                        capture_report.setdefault("warnings", []).append(
                            {
                                "property": "http-status",
                                "value": record["httpStatus"],
                                "note": (
                                    "The route returned an HTTP error status; verify the "
                                    "captured screen is intentional."
                                ),
                            }
                        )
                    capture_report_path.write_text(
                        json.dumps(capture_report, indent=2) + "\n", encoding="utf-8"
                    )

                    record.update(
                        {
                            "status": "captured",
                            "html": str(html_path),
                            "screenshot": str(screenshot_path),
                            "captureReport": str(capture_report_path),
                            "finalUrl": final_url,
                            "pageTitle": capture_report.get("pageTitle"),
                            "root": capture_report.get("root"),
                            "stats": capture_report.get("stats"),
                            "unsupportedCount": len(capture_report.get("unsupported", [])),
                            "assetFailureCount": len(capture_report.get("assetFailures", [])),
                            "warningCount": len(capture_report.get("warnings", [])),
                        }
                    )

                    if openpencil:
                        fig_path = route_dir / f"{slug}.fig"
                        imported = import_html(
                            openpencil, html_path, fig_path, route_spec.name, route_dir
                        )
                        record["import"] = imported
                        if imported["status"] != "ok":
                            record["status"] = "import-failed"
                            warn(f"OpenPencil import failed for {safe_route}; inspect summary.json")
                        else:
                            record["status"] = "ok"
                            record["fig"] = str(fig_path)
                            if not args.no_verify_render:
                                rendered_path = route_dir / "openpencil.png"
                                try:
                                    exported = export_fig(
                                        openpencil, fig_path, rendered_path, route_dir
                                    )
                                except Exception as error:
                                    exported = {
                                        "status": "failed",
                                        "error": f"{type(error).__name__}: {error}",
                                    }
                                record["export"] = exported
                                if exported["status"] == "ok":
                                    diff_path = route_dir / "diff.png"
                                    try:
                                        record["visualDiff"] = compare_images(
                                            screenshot_path, rendered_path, diff_path
                                        )
                                    except Exception as error:
                                        record["visualDiff"] = {
                                            "status": "failed",
                                            "error": str(error),
                                        }
                                else:
                                    warn(f"OpenPencil render verification failed for {safe_route}")
                except Exception as error:
                    record["status"] = "failed"
                    record["error"] = f"{type(error).__name__}: {error}"
                    warn(f"Capture failed for {safe_route}: {error}")
                finally:
                    page.close()
                summary["routes"].append(record)

            context.close()
            browser.close()

    captured_records = [record for record in summary["routes"] if record.get("html")]
    if len(captured_records) > 1 and not args.no_combine:
        combined_dir = output_dir / "combined"
        combined_dir.mkdir(parents=True, exist_ok=True)
        combined_html = combined_dir / "project.html"
        write_combined_html(captured_records, combined_html, project_name)
        combined: dict[str, Any] = {"html": str(combined_html), "status": "captured"}
        if openpencil:
            combined_fig = combined_dir / f"{slugify(project_name, 'dioxus-project')}.fig"
            imported = import_html(
                openpencil, combined_html, combined_fig, project_name, combined_dir
            )
            combined["import"] = imported
            if imported["status"] == "ok":
                combined["status"] = "ok"
                combined["fig"] = str(combined_fig)
                if not args.no_verify_render:
                    rendered = combined_dir / "openpencil.png"
                    try:
                        combined["export"] = export_fig(
                            openpencil, combined_fig, rendered, combined_dir
                        )
                    except Exception as error:
                        combined["export"] = {
                            "status": "failed",
                            "error": f"{type(error).__name__}: {error}",
                        }
            else:
                combined["status"] = "import-failed"
        summary["combined"] = combined

    failures = [
        record
        for record in summary["routes"]
        if record.get("status") in {"failed", "import-failed"}
    ]
    combined_failed = summary.get("combined", {}).get("status") == "import-failed"
    summary["status"] = "ok" if not failures and not combined_failed else "partial"
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(relative_to_output(summary, output_dir), indent=2) + "\n",
        encoding="utf-8",
    )
    log(f"Wrote {summary_path}")

    if skipped_dynamic:
        warn("Dynamic routes require explicit --route values: " + ", ".join(skipped_dynamic[:10]))
    return 2 if failures or combined_failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as error:
        print(
            f"[dioxus-openpencil] error: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)

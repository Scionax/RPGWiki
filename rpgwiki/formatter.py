# Helper functions for formatting wiki text into HTML
from html import escape
from typing import Dict, List

from .parser import parse_header, KeywordTarget
from .config import Config


def _is_word_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _apply_links_to_line(line: str, keywords: List[str], case_sensitive: bool) -> str:
    """Return HTML for a line with keyword links applied."""
    lower_line = line.lower()
    occupied = [False] * len(line)
    ranges: List[tuple[int, int, str]] = []
    for kw in keywords:
        search_kw = kw if case_sensitive else kw.lower()
        start = 0
        while True:
            idx = line.find(kw, start) if case_sensitive else lower_line.find(search_kw, start)
            if idx == -1:
                break
            end = idx + len(kw)
            before_valid = idx == 0 or not _is_word_char(line[idx - 1])
            after_valid = end == len(line) or not _is_word_char(line[end])
            if before_valid and after_valid and not any(occupied[idx:end]):
                ranges.append((idx, end, kw))
                for i in range(idx, end):
                    occupied[i] = True
            start = end
    ranges.sort()
    html_parts = []
    last = 0
    for start, end, kw in ranges:
        html_parts.append(escape(line[last:start]))
        html_parts.append(f'<a href="{escape(kw)}">{escape(line[start:end])}</a>')
        last = end
    html_parts.append(escape(line[last:]))
    return "".join(html_parts)


HEADER_SIZES = {1: 24, 2: 18, 3: 16, 4: 14}


def format_content(content: str, keyword_map: Dict[str, KeywordTarget], config: Config) -> str:
    """Convert raw wiki text to HTML with links, wrapping and header styles."""
    keywords = sorted(keyword_map.keys(), key=len, reverse=True)
    lines_html: List[str] = []
    for line in content.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text, _ = parse_header(line)
            size = HEADER_SIZES.get(level, 12)
            line_html = f'<span style="font-size:{size}px; font-weight:bold">{escape(text)}</span>'
        else:
            line_html = _apply_links_to_line(line, keywords, config.case_sensitive)
        lines_html.append(line_html)
    body = "\n".join(lines_html)
    wrapper = '<pre style="white-space: pre-wrap; font-family: monospace; font-size:12px">{}</pre>'.format(body)
    return wrapper

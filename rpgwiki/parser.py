import os
import re
from dataclasses import dataclass
from typing import Dict, Tuple, List


@dataclass
class HeaderEntry:
    file: str
    line: int
    text: str
    preview: str

@dataclass
class KeywordTarget:
    file: str
    line: int
    header: str

# Regular expressions for parsing headers
ASTERISK_RE = re.compile(r'\*([^*]+)\*')
BANG_RE = re.compile(r'!([\w\s]+)')

# '/s' plural suffix pattern
PLURAL_RE = re.compile(r'(\b[^/]+)/s(\b)?', re.IGNORECASE)


def parse_header(line: str) -> Tuple[str, List[str]]:
    """Return visible header text and list of keywords."""
    keywords: List[str] = []
    text = line.strip().lstrip('#').strip()
    used_symbol = False

    # bang keywords
    for m in BANG_RE.finditer(text):
        kw = m.group(1).strip()
        if kw:
            keywords.append(kw)
            used_symbol = True
    text = BANG_RE.sub('', text).strip()

    # asterisk keywords
    for m in ASTERISK_RE.finditer(text):
        kw = m.group(1).strip()
        if kw:
            keywords.append(kw)
            used_symbol = True
    text = ASTERISK_RE.sub(r'\1', text)

    # plural keywords
    def plural_repl(match: re.Match) -> str:
        nonlocal used_symbol
        base = match.group(1)
        keywords.append(base)
        keywords.append(base + 's')
        used_symbol = True
        return base

    text = PLURAL_RE.sub(plural_repl, text)

    # synonym keywords with '/'
    if '/' in text:
        used_symbol = True
        parts = [p.strip() for p in text.split('/')]
        if len(parts) > 1:
            text = parts[0]
            for kw in parts:
                if kw:
                    keywords.append(kw)
        else:
            # handle trailing '/'
            text = text.rstrip('/')
            if text:
                keywords.append(text)
    else:
        if used_symbol and text:
            keywords.append(text)

    keywords = [kw for kw in keywords if kw]
    return text.strip(), keywords


def scan_folder(folder: str) -> Dict[str, KeywordTarget]:
    """Scan all md files in folder and return keyword map."""
    keyword_map: Dict[str, KeywordTarget] = {}
    for root, _, files in os.walk(folder):
        for f in files:
            if not f.lower().endswith('.md') or f.startswith('_'):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                for lineno, line in enumerate(fp, 1):
                    if line.lstrip().startswith('#'):
                        text, kws = parse_header(line)
                        for kw in kws:
                            if kw not in keyword_map:
                                keyword_map[kw] = KeywordTarget(path, lineno, text)
                            # duplicates ignored; could log warning
    return keyword_map


def scan_headers(folder: str) -> List[HeaderEntry]:
    """Return all headers within a folder."""
    headers: List[HeaderEntry] = []
    for root, _, files in os.walk(folder):
        for f in files:
            if not f.lower().endswith('.md') or f.startswith('_'):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    lines = fp.readlines()
            except OSError:
                continue
            for lineno, line in enumerate(lines, 1):
                if line.lstrip().startswith('#'):
                    text, _ = parse_header(line)
                    snippet = ' '.join(l.strip() for l in lines[lineno:lineno + 3])
                    headers.append(
                        HeaderEntry(
                            file=path,
                            line=lineno,
                            text=text,
                            preview=snippet[:120],
                        )
                    )
    return headers

import os, re, hashlib
from typing import List, Tuple


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"^(#{2,6})\s+(.*)$", re.MULTILINE)


def slugify(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip()).strip("-").lower()


def file_sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_wikilinks(text: str) -> list[str]:
    matches = WIKILINK_RE.finditer(text)
    links = []
    for m in matches:
        link_content = m.group(1).strip()
        # Handle pipe syntax: [[filename|display name]] -> extract just the filename
        if '|' in link_content:
            filename = link_content.split('|')[0].strip()
        else:
            filename = link_content
        
        # Extract just the base filename from paths like "specific/file/path/Session 1"
        if '/' in filename:
            filename = os.path.basename(filename)
        
        links.append(filename)
    return links


def split_into_sections(md_text: str) -> List[Tuple[str, str]]:
    # Returns list of (heading, section_text). Uses H2+ as chunk boundaries
    matches = list(HEADING_RE.finditer(md_text))
    if not matches:
        return [(None, md_text)]
    sections = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(md_text)
        heading = m.group(2).strip()
        body = md_text[start:end].strip()
        sections.append((heading, body))
    return sections


def window_chunks(text: str, max_chars: int = 2000, overlap: int = 200):
    if len(text) <= max_chars:
        yield text
        return
    i = 0
    while i < len(text):
        yield text[i:i+max_chars]
        i = max(0, i + max_chars - overlap)
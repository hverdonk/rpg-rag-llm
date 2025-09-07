import os, json, datetime
from typing import Optional
from app.config import settings
from app.weaviate_client import get_client, ensure_schema
from app.utils import extract_wikilinks, split_into_sections, window_chunks, slugify
from app.embeddings import embed_texts

CHAR_DIR = settings.characters_dir
SESS_DIR = settings.sessions_dir
LOC_DIR = settings.locations_dir
ORG_DIR = settings.organizations_dir

# Simple in-memory caches to resolve [[links]]
_char_name_to_id: dict[str, str] = {}
_location_name_to_id: dict[str, str] = {}
_organization_name_to_id: dict[str, str] = {}

def upsert_character(name: str, path: str) -> str:
    client = get_client()
    key = name.strip()
    if key in _char_name_to_id:
        return _char_name_to_id[key]
    obj = {"name": name, "aliases": [], "path": path}
    uuid = client.data_object.create(obj, class_name="Character")
    _char_name_to_id[key] = uuid
    return uuid

def upsert_location(name: str, path: str) -> str:
    client = get_client()
    key = name.strip()
    if key in _location_name_to_id:
        return _location_name_to_id[key]
    obj = {"name": name, "aliases": [], "path": path}
    uuid = client.data_object.create(obj, class_name="Location")
    _location_name_to_id[key] = uuid
    return uuid

def upsert_organization(name: str, path: str) -> str:
    client = get_client()
    key = name.strip()
    if key in _organization_name_to_id:
        return _organization_name_to_id[key]
    obj = {"name": name, "aliases": [], "path": path}
    uuid = client.data_object.create(obj, class_name="Organization")
    _organization_name_to_id[key] = uuid
    return uuid

def sync_characters():
    # Create Character objects from files in character dir
    for fn in os.listdir(CHAR_DIR):
        if not fn.lower().endswith(".md"): continue
        name = os.path.splitext(fn)[0]
        path = os.path.join(CHAR_DIR, fn)
        upsert_character(name, path)

def sync_locations():
    # Create Location objects from files in location dir
    if not os.path.exists(LOC_DIR):
        return
    for fn in os.listdir(LOC_DIR):
        if not fn.lower().endswith(".md"): continue
        name = os.path.splitext(fn)[0]
        path = os.path.join(LOC_DIR, fn)
        upsert_location(name, path)

def sync_organizations():
    # Create Organization objects from files in organization dir
    if not os.path.exists(ORG_DIR):
        return
    for fn in os.listdir(ORG_DIR):
        if not fn.lower().endswith(".md"): continue
        name = os.path.splitext(fn)[0]
        path = os.path.join(ORG_DIR, fn)
        upsert_organization(name, path)

def parse_session_filename(fn: str) -> tuple[Optional[int], Optional[str]]:
    # e.g., "Session 14.md" or "2024-12-30 - Session 14.md"
    import re
    session_no = None
    m = re.search(r"[Ss]ession\s+(\d+)", fn)
    if m:
        session_no = int(m.group(1))
    date = None
    m2 = re.match(r"(\d{4}-\d{2}-\d{2})", fn)
    if m2:
        date = m2.group(1)
    return session_no, date


def upsert_document(doc_type: str,
                    title: str,
                    path: str,
                    session_no: Optional[int],
                    session_date: Optional[str]) -> str:
    client = get_client()
    obj = {
        "type": doc_type,
        "title": title,
        "path": path,
        "sessionNo": session_no,
        "sessionDate": session_date,
    }
    uuid = client.data_object.create(obj, class_name="Document")
    return uuid


def upsert_chunk(text: str,
                 heading: Optional[str],
                 of_doc_uuid: str,
                 session_no: Optional[int],
                 session_date: Optional[str],
                 char_uuids: list[str],
                 location_uuids: list[str] = [],
                 organization_uuids: list[str] = []):
    client = get_client()
    vec = embed_texts([text])[0]
    obj = {
        "text": text,
        "heading": heading or "",
        "startChar": 0,
        "endChar": len(text),
        "sessionNo": session_no,
        "sessionDate": session_date,
        "ofDoc": [{"beacon": f"weaviate://localhost/Document/{of_doc_uuid}"}],
        "characters": [{"beacon": f"weaviate://localhost/Character/{c}"} for c in char_uuids],
        "locations": [{"beacon": f"weaviate://localhost/Location/{c}"} for c in location_uuids],
        "organizations": [{"beacon": f"weaviate://localhost/Organization/{c}"} for c in organization_uuids],
    }
    client.data_object.create(obj, class_name="Chunk", vector=vec)


def scan_once() -> dict:
    ensure_schema()
    sync_characters()
    sync_locations()
    sync_organizations()

    indexed_docs = 0
    indexed_chunks = 0

    # Process session files
    for fn in sorted(os.listdir(SESS_DIR)):
        if not fn.lower().endswith(".md"): continue
        path = os.path.join(SESS_DIR, fn)
        title = os.path.splitext(fn)[0]
        session_no, session_date = parse_session_filename(fn)
        doc_uuid = upsert_document("session", title, path, session_no, session_date)
        indexed_docs += 1
        indexed_chunks += process_document_chunks(path, doc_uuid, session_no, session_date)

    # Process character files
    if os.path.exists(CHAR_DIR):
        for fn in sorted(os.listdir(CHAR_DIR)):
            if not fn.lower().endswith(".md"): continue
            path = os.path.join(CHAR_DIR, fn)
            title = os.path.splitext(fn)[0]
            doc_uuid = upsert_document("character", title, path, None, None)
            indexed_docs += 1
            indexed_chunks += process_document_chunks(path, doc_uuid, None, None)

    # Process location files
    if os.path.exists(LOC_DIR):
        for fn in sorted(os.listdir(LOC_DIR)):
            if not fn.lower().endswith(".md"): continue
            path = os.path.join(LOC_DIR, fn)
            title = os.path.splitext(fn)[0]
            doc_uuid = upsert_document("location", title, path, None, None)
            indexed_docs += 1
            indexed_chunks += process_document_chunks(path, doc_uuid, None, None)

    # Process organization files
    if os.path.exists(ORG_DIR):
        for fn in sorted(os.listdir(ORG_DIR)):
            if not fn.lower().endswith(".md"): continue
            path = os.path.join(ORG_DIR, fn)
            title = os.path.splitext(fn)[0]
            doc_uuid = upsert_document("organization", title, path, None, None)
            indexed_docs += 1
            indexed_chunks += process_document_chunks(path, doc_uuid, None, None)

    return {"indexed_docs": indexed_docs, "indexed_chunks": indexed_chunks}

def process_document_chunks(path: str, 
                            doc_uuid: str, 
                            session_no: Optional[int], 
                            session_date: Optional[str]) -> int:
    """Process a document file and create chunks with entity links"""
    chunk_count = 0
    
    with open(path, "r", encoding="utf-8") as f:
        md = f.read()
        sections = split_into_sections(md)
        if not sections:
            sections = [(None, md)]

    for heading, body in sections:
        # favor heading-bounded chunks, but window if long
        bodies = list(window_chunks(body, max_chars=2000, overlap=200))
        char_uuids = []
        location_uuids = []
        organization_uuids = []
        for chunk_text in bodies:
            # resolve [[links]] to characters, locations, and organizations
            wikilinks = extract_wikilinks(chunk_text)
            for wl in wikilinks:
                name = wl.strip()
                if name in _char_name_to_id:
                    char_uuids.append(_char_name_to_id[name])
                elif name in _location_name_to_id:
                    location_uuids.append(_location_name_to_id[name])
                elif name in _organization_name_to_id:
                    organization_uuids.append(_organization_name_to_id[name])
            # Auto-link document chunks to their corresponding entities
            # (since documents never self-reference with [[links]])
            doc_title = os.path.splitext(os.path.basename(path))[0]
            if path.startswith(CHAR_DIR) and doc_title in _char_name_to_id:
                entity_uuid = _char_name_to_id[doc_title]
                if entity_uuid not in char_uuids:
                    char_uuids.append(entity_uuid)
            elif path.startswith(LOC_DIR) and doc_title in _location_name_to_id:
                entity_uuid = _location_name_to_id[doc_title]
                if entity_uuid not in location_uuids:
                    location_uuids.append(entity_uuid)
            elif path.startswith(ORG_DIR) and doc_title in _organization_name_to_id:
                entity_uuid = _organization_name_to_id[doc_title]
                if entity_uuid not in organization_uuids:
                    organization_uuids.append(entity_uuid)
            upsert_chunk(chunk_text, heading, doc_uuid, session_no, session_date, char_uuids, location_uuids, organization_uuids)
            chunk_count += 1
    
    return chunk_count
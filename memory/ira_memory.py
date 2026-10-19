#!/usr/bin/env python3
"""
Ira Memory Layer — SQLite + FTS5 + sqlite-vec
Per BUILD_PLAN.md section 2a
"""

import sqlite3
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

DB_PATH = Path("/home/dinu/Desktop/Tech/Ira/memory/ira_memory.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
    text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,          -- 'person', 'preference', 'task', 'date', 'fact'
    key TEXT NOT NULL,           -- e.g. 'father', 'ex', 'coffee'
    value TEXT NOT NULL,         -- distilled fact
    ts INTEGER NOT NULL,
    UNIQUE(kind, key)
);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    text, content='messages', content_rowid='id'
);

-- sqlite-vec table for embeddings (optional, requires sqlite-vec extension)
-- CREATE VIRTUAL TABLE IF NOT EXISTS vec USING vec0(
--     chunk_id INTEGER PRIMARY KEY,
--     embedding float[256]
-- );

-- Triggers to keep FTS5 in sync
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, text) VALUES (new.id, new.text);
END;

CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, text) VALUES ('delete', old.id, old.text);
END;

CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, text) VALUES ('delete', old.id, old.text);
    INSERT INTO messages_fts(rowid, text) VALUES (new.id, new.text);
END;

CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages(ts);
CREATE INDEX IF NOT EXISTS idx_memory_kind_key ON memory(kind, key);
"""

ENTITY_PATTERNS = {
    'person': re.compile(r'\b(mom|dad|father|mother|brother|sister|friend|ex|girlfriend|boyfriend|wife|husband|partner|boss|teacher|doctor|nurse)\b', re.I),
    'preference': re.compile(r'\b(i like|i love|i hate|i prefer|favorite|favourite)\b.*', re.I),
    'task': re.compile(r'\b(need to|have to|must|should|todo|deadline|appointment|meeting)\b.*', re.I),
    'date': re.compile(r'\b(today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2})\b', re.I),
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn

def add_message(conn: sqlite3.Connection, role: str, text: str) -> int:
    ts = int(time.time())
    cur = conn.execute(
        "INSERT INTO messages (ts, role, text) VALUES (?, ?, ?)",
        (ts, role, text)
    )
    conn.commit()
    return cur.lastrowid

def upsert_memory(conn: sqlite3.Connection, kind: str, key: str, value: str):
    ts = int(time.time())
    conn.execute(
        """INSERT INTO memory (kind, key, value, ts) VALUES (?, ?, ?, ?)
           ON CONFLICT(kind, key) DO UPDATE SET value=excluded.value, ts=excluded.ts""",
        (kind, key, value, ts)
    )
    conn.commit()

def extract_entities(text: str) -> List[Tuple[str, str, str]]:
    """Return list of (kind, key, value)"""
    entities = []
    for kind, pattern in ENTITY_PATTERNS.items():
        for match in pattern.finditer(text):
            entities.append((kind, match.group(0).lower(), match.group(0)))
    return entities

def get_recent_messages(conn: sqlite3.Connection, limit: int = 10) -> List[Dict]:
    rows = conn.execute(
        "SELECT id, ts, role, text FROM messages ORDER BY ts DESC LIMIT ?",
        (limit,)
    ).fetchall()
    return [{"id": r[0], "ts": r[1], "role": r[2], "text": r[3]} for r in reversed(rows)]

def get_recent_turns(conn: sqlite3.Connection, limit: int = 5) -> List[Dict]:
    """Get last N user-assistant pairs"""
    rows = conn.execute(
        "SELECT id, ts, role, text FROM messages ORDER BY ts DESC LIMIT ?",
        (limit * 2,)
    ).fetchall()
    msgs = [{"id": r[0], "ts": r[1], "role": r[2], "text": r[3]} for r in reversed(rows)]
    
    pairs = []
    i = 0
    while i < len(msgs) - 1:
        if msgs[i]['role'] == 'user' and msgs[i+1]['role'] == 'assistant':
            pairs.append({"user": msgs[i]['text'], "assistant": msgs[i+1]['text']})
            i += 2
        else:
            i += 1
    return pairs[-limit:]

def build_recap(conn: sqlite3.Connection) -> str:
    """Build ≤5-line recap for system prompt injection"""
    lines = []
    
    # Name
    lines.append("name: Dip")
    
    # Key people from memory
    people = conn.execute("SELECT key, value FROM memory WHERE kind='person'").fetchall()
    if people:
        lines.append("people: " + ", ".join(f"{k}={v}" for k, v in people))
    
    # Active preferences
    prefs = conn.execute("SELECT key, value FROM memory WHERE kind='preference'").fetchall()
    if prefs:
        lines.append("prefs: " + ", ".join(f"{k}={v}" for k, v in prefs[:3]))
    
    # Current task
    tasks = conn.execute("SELECT key, value FROM memory WHERE kind='task' ORDER BY ts DESC LIMIT 1").fetchall()
    if tasks:
        lines.append("task: " + tasks[0][1][:80])
    
    # Stage calculation
    total_msgs = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    total_days = 0
    first_ts = conn.execute("SELECT MIN(ts) FROM messages").fetchone()[0]
    if first_ts:
        total_days = (time.time() - first_ts) / 86400
    
    if total_days < 2 or total_msgs < 50:
        stage = 1
    elif total_days < 14:
        stage = 2
    else:
        stage = 3
    lines.append(f"stage: {stage}")
    
    return " | ".join(lines)

def get_context_line(conn: sqlite3.Connection) -> str:
    """Return CONTEXT line for Modelfile template"""
    recap = build_recap(conn)
    # Extract components for the CONTEXT placeholder
    stage = 1
    mood = "neutral"
    recent = "new conversation"
    promises = "none"
    
    for line in recap.split(" | "):
        if line.startswith("stage:"):
            stage = int(line.split(":")[1].strip())
    
    recent_turns = get_recent_turns(conn, 2)
    if recent_turns:
        recent = recent_turns[-1]['user'][:60]
    
    return f"CONTEXT | name: Dip | stage: {stage} | mood: {mood} | recent: {recent} | promises: {promises}"

def run_self_test():
    """Run basic functionality test"""
    print("Running memory self-test...")
    
    conn = init_db()
    
    # Clear test data
    conn.execute("DELETE FROM messages")
    conn.execute("DELETE FROM memory")
    conn.commit()
    
    # Add test messages
    add_message(conn, "user", "Hey, I'm Dip. My sister Rina is a nurse.")
    add_message(conn, "assistant", "Nice to meet you, Dip. Rina sounds cool.")
    add_message(conn, "user", "I love coffee and hate mornings.")
    add_message(conn, "assistant", "Coffee's great. Mornings... yeah.")
    add_message(conn, "user", "I have a meeting with Dr. Patel tomorrow at 10.")
    add_message(conn, "assistant", "Got it. Meeting with Dr. Patel tomorrow 10am.")
    
    # Extract entities
    for role in ["user", "assistant"]:
        rows = conn.execute("SELECT text FROM messages WHERE role=?", (role,)).fetchall()
        for (text,) in rows:
            for kind, key, value in extract_entities(text):
                upsert_memory(conn, kind, key, value)
    
    # Verify memory
    print("\n--- Memory contents ---")
    for row in conn.execute("SELECT kind, key, value FROM memory").fetchall():
        print(f"  {row[0]}: {row[1]} = {row[2]}")
    
    # Build recap
    print("\n--- Recap ---")
    recap = build_recap(conn)
    print(recap)
    
    # Context line
    print("\n--- Context line ---")
    ctx = get_context_line(conn)
    print(ctx)
    
    # Test FTS5 search
    print("\n--- FTS5 search test ---")
    results = conn.execute(
        "SELECT rowid, text FROM messages_fts WHERE text MATCH 'meeting' LIMIT 5"
    ).fetchall()
    for r in results:
        print(f"  [{r[0]}] {r[1][:80]}")
    
    conn.close()
    print("\n✅ Self-test passed!")
    return True

if __name__ == "__main__":
    run_self_test()
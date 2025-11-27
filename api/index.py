"""
Vercel Serverless Function Entry Point for decatrainer
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
import os

app = FastAPI()

BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / "content"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


def build_file_tree(directory: Path, base_path: Path = None) -> list:
    if base_path is None:
        base_path = directory
    
    items = []
    
    try:
        entries = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    except (PermissionError, FileNotFoundError):
        return items
    
    for entry in entries:
        if entry.name.startswith('.'):
            continue
            
        relative_path = entry.relative_to(base_path)
        
        if entry.is_dir():
            children = build_file_tree(entry, base_path)
            if children:
                items.append({
                    "name": entry.name.replace('_', ' ').title(),
                    "path": str(relative_path),
                    "type": "directory",
                    "children": children
                })
        elif entry.suffix.lower() == '.md':
            items.append({
                "name": entry.stem.replace('_', ' ').title(),
                "path": str(relative_path),
                "type": "file"
            })
    
    return items


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = TEMPLATES_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding='utf-8'))
    return HTMLResponse("<h1>decatrainer</h1><p>Template not found</p>")


@app.get("/static/{path:path}")
async def serve_static(path: str):
    file_path = STATIC_DIR / path
    if file_path.exists() and file_path.is_file():
        content = file_path.read_text(encoding='utf-8')
        
        content_type = "text/plain"
        if path.endswith('.css'):
            content_type = "text/css"
        elif path.endswith('.js'):
            content_type = "application/javascript"
        
        return HTMLResponse(content=content, media_type=content_type)
    raise HTTPException(status_code=404, detail="Static file not found")


@app.get("/tree")
async def get_file_tree():
    if not CONTENT_DIR.exists():
        return []
    
    tree = build_file_tree(CONTENT_DIR)
    return tree


@app.get("/content/{path:path}")
async def get_content(path: str):
    file_path = CONTENT_DIR / path
    
    try:
        file_path = file_path.resolve()
        if not str(file_path).startswith(str(CONTENT_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    try:
        content = file_path.read_text(encoding='utf-8')
        return {"content": content, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


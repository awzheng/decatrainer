"""
decatrainer - DECA Flashcard Bank
"""

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="decatrainer", description="DECA Flashcard Bank")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Base content directory
CONTENT_DIR = Path("content")


def build_file_tree(directory: Path, base_path: Path = None) -> list:
    """Recursively build a file tree structure from the content directory."""
    if base_path is None:
        base_path = directory
    
    items = []
    
    try:
        entries = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    except PermissionError:
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
    """Serve the main interface."""
    return FileResponse("templates/index.html")


@app.get("/tree")
async def get_file_tree():
    """Return a JSON tree of all markdown files in the content directory."""
    if not CONTENT_DIR.exists():
        CONTENT_DIR.mkdir(parents=True)
        return []
    
    tree = build_file_tree(CONTENT_DIR)
    return tree


@app.get("/content/{path:path}")
async def get_content(path: str):
    """Return the raw markdown content of a specific file."""
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)


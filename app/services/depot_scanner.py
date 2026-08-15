import os
from pathlib import Path


def scan_depot(depot_path):
    """Scan the depot directory and return a tree summary."""
    root = Path(depot_path)
    if not root.exists():
        return {'exists': False, 'components': [], 'total_size': 0, 'file_count': 0}

    components = []
    total_size = 0
    file_count = 0

    if root.is_dir():
        for entry in sorted(root.iterdir()):
            if entry.is_dir():
                comp_size = sum(f.stat().st_size for f in entry.rglob('*') if f.is_file())
                comp_files = sum(1 for f in entry.rglob('*') if f.is_file())
                components.append({
                    'name': entry.name,
                    'size_bytes': comp_size,
                    'file_count': comp_files,
                })
                total_size += comp_size
                file_count += comp_files
            elif entry.is_file():
                total_size += entry.stat().st_size
                file_count += 1

    return {
        'exists': True,
        'path': str(root),
        'components': components,
        'total_size': total_size,
        'file_count': file_count,
    }


def list_directory(depot_path, subdir=''):
    """List contents of a specific subdirectory within the depot."""
    base = Path(depot_path).resolve()
    target = (base / subdir).resolve() if subdir else base

    # Prevent path traversal
    if not str(target).startswith(str(base)):
        raise ValueError('Path traversal detected')

    if not target.exists() or not target.is_dir():
        return {'items': [], 'parent': None, 'error': 'Directory not found'}

    items = []
    for entry in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        stat = entry.stat()
        items.append({
            'name': entry.name,
            'is_dir': entry.is_dir(),
            'size': stat.st_size if entry.is_file() else 0,
            'modified': stat.st_mtime,
            'relative_path': str(entry.relative_to(base)),
        })

    parent = None
    if target != base:
        rel = target.relative_to(base)
        parent = str(rel.parent) if str(rel.parent) != '.' else ''

    return {'items': items, 'parent': parent}
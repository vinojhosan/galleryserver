import os

def is_image_file(filename: str) -> bool:
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
    ext = os.path.splitext(filename.lower())[1]
    return ext in image_exts

def get_file_size(filepath: str) -> str:
    try:
        size = os.path.getsize(filepath)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except Exception:
        return "Unknown size"

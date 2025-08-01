# ===========================================
# File: setup.py (Updated for Two Tiers)
# ===========================================
from setuptools import setup, find_packages

# Basic edition setup
setup(
    name="galleryserve",
    version="1.0.0",
    author="Vinoj John Hosan",
    description="HTTP server with image thumbnails - Basic Edition",
    long_description="""
# Thumbnail Server - Basic Edition

Transform any folder into a beautiful web gallery with automatic thumbnail generation.

## ✅ Basic Edition Features ($5):
- Local HTTP server for LAN access
- Automatic thumbnail generation
- Mobile-responsive web interface  
- Dark/Light theme toggle
- Cross-platform (Windows, Mac, Linux)

## 🚀 Advanced Edition Features ($15):
- Everything in Basic Edition
- Password protection for galleries
- Internet sharing via ngrok integration
- Bulk download with ZIP archives
- Multi-selection for batch operations
- Advanced image formats (RAW, HEIC)
- Usage analytics and tracking

Perfect for photographers, designers, and teams who need professional image gallery hosting.

**Upgrade to Advanced:** https://gumroad.com/l/gallery-serve-advanced
    """,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "Pillow>=8.0.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "galleryserve=galleryserve.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Multimedia :: Graphics",
    ],
)

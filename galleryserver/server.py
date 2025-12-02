#!/usr/bin/env python3
import http.server
import socketserver
import os
import urllib.parse
import mimetypes
from PIL import Image
import io
import argparse

class ThumbnailHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, thumbnail_size=200, **kwargs):
        self.thumbnail_size = thumbnail_size
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        # Parse the URL
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # Check if this is a thumbnail request
        if 'thumb' in query_params and parsed_path.path != '/':
            self.serve_thumbnail(parsed_path.path)
        elif parsed_path.path == '/' or parsed_path.path.endswith('/'):
            self.serve_directory_with_thumbnails(parsed_path.path)
        else:
            # Serve regular files
            super().do_GET()
    
    def serve_thumbnail(self, path):
        """Generate and serve a thumbnail for an image"""
        try:
            # Remove leading slash and decode URL
            file_path = urllib.parse.unquote(path[1:])
            
            if not os.path.exists(file_path) or not self.is_image_file(file_path):
                self.send_error(404, "File not found or not an image")
                return
            
            # Generate thumbnail
            with Image.open(file_path) as img:
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail((self.thumbnail_size, self.thumbnail_size), Image.Resampling.LANCZOS)
                
                # Save to bytes
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG', quality=85)
                img_bytes.seek(0)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', len(img_bytes.getvalue()))
                self.send_header('Cache-Control', 'max-age=3600')  # Cache for 1 hour
                self.end_headers()
                self.wfile.write(img_bytes.getvalue())
                
        except Exception as e:
            print(f"Error generating thumbnail for {path}: {e}")
            self.send_error(500, f"Error generating thumbnail: {str(e)}")
    
    def serve_directory_with_thumbnails(self, path):
        """Serve directory listing with image thumbnails"""
        try:
            # Remove leading slash and decode URL
            dir_path = urllib.parse.unquote(path[1:]) if path != '/' else '.'
            
            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                self.send_error(404, "Directory not found")
                return
            
            # Get directory contents
            try:
                entries = os.listdir(dir_path)
                entries.sort()
            except OSError:
                self.send_error(404, "Cannot list directory")
                return
            
            # Generate HTML
            html = self.generate_directory_html(dir_path, entries, path)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(html.encode('utf-8')))
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
        except Exception as e:
            print(f"Error serving directory {path}: {e}")
            self.send_error(500, f"Error serving directory: {str(e)}")
    
    def generate_directory_html(self, dir_path, entries, url_path):
        """Generate HTML for directory listing with thumbnails"""
        title = f"Gallery - {url_path if url_path != '/' else 'Root'}"
        
        # Start building HTML
        html_parts = []
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="en">')
        html_parts.append('<head>')
        html_parts.append('    <meta charset="utf-8">')
        html_parts.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_parts.append(f'    <title>{title}</title>')
        
        # Add CSS
        css = '''    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        
        .header {
            background: rgba(30, 30, 50, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        h1 { 
            color: #ffffff;
            font-size: clamp(1.5rem, 4vw, 2.5rem);
            font-weight: 700;
            text-align: center;
            margin-bottom: 10px;
        }
        
        .breadcrumb {
            text-align: center;
            color: #b0b0b0;
            font-size: 0.9rem;
        }
        
        .parent-button {
            display: block;
            width: 100%;
            max-width: 300px;
            margin: 20px auto;
            padding: 15px 25px;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-size: 16px;
            font-weight: 600;
            text-align: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
        }
        
        .parent-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(79, 172, 254, 0.4);
        }
        
        .parent-button.disabled {
            background: #444;
            color: #888;
            cursor: not-allowed;
            box-shadow: none;
        }
        
        .parent-button.disabled:hover {
            transform: none;
            box-shadow: none;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .item {
            background: rgba(45, 45, 70, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .item:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
            border-color: rgba(79, 172, 254, 0.3);
        }
        
        .thumbnail-container {
            position: relative;
            width: 100%;
            height: 220px;
            overflow: hidden;
            background: linear-gradient(45deg, #2c2c3e, #1a1a2e);
            cursor: pointer;
        }
        
        .thumbnail {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease, opacity 0.3s ease;
        }
        
        .item:hover .thumbnail {
            transform: scale(1.1);
        }
        
        .item-content {
            padding: 20px;
        }
        
        .filename {
            font-size: 16px;
            font-weight: 600;
            color: #ffffff;
            text-decoration: none;
            display: block;
            margin-bottom: 8px;
            word-break: break-word;
            line-height: 1.4;
        }
        
        .filename:hover {
            color: #4facfe;
        }
        
        .directory {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 220px;
            font-size: 18px;
            font-weight: 600;
            color: white;
            text-decoration: none;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: all 0.3s ease;
        }
        
        .directory:hover {
            background: linear-gradient(135deg, #5a67d8 0%, #667eea 100%);
        }
        
        .directory-icon {
            font-size: 3rem;
            margin-bottom: 10px;
            display: block;
        }
        
        .file-info {
            font-size: 13px;
            color: #b0b0b0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .file-type {
            background: rgba(79, 172, 254, 0.2);
            color: #4facfe;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border: 1px solid rgba(79, 172, 254, 0.3);
        }
        
        .image-overlay {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #888;
            font-size: 14px;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 20px;
            }
            
            .header {
                padding: 15px;
                margin-bottom: 20px;
            }
            
            .container {
                padding: 0 15px;
            }
            
            .thumbnail-container {
                height: 180px;
            }
            
            .item-content {
                padding: 15px;
            }
        }
        
        @media (max-width: 480px) {
            .grid {
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
            }
            
            .thumbnail-container {
                height: 160px;
            }
        }
        
        .fade-in {
            animation: fadeIn 0.6s ease-out;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .no-items {
            text-align: center;
            padding: 60px 20px;
            color: #b0b0b0;
            font-size: 18px;
            background: rgba(45, 45, 70, 0.9);
            border-radius: 16px;
            margin: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Image Modal */
        .modal {
            display: none;
            position: fixed;
            z-index: 10000;
            padding-top: 60px;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: rgba(0,0,0,0.9);
            touch-action: none;
        }

        .modal-inner {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        .modal-content {
            margin: auto;
            display: block;
            max-width: 90%;
            max-height: 80vh;
            transition: transform 0.2s ease;
            will-change: transform;
            cursor: grab;
            touch-action: none;
        }

        .modal-content.grabbing {
            cursor: grabbing;
        }

        .close {
            position: absolute;
            top: 20px;
            right: 40px;
            color: #fff;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            z-index: 10001;
        }

        .prev, .next {
            cursor: pointer;
            position: absolute;
            top: 50%;
            padding: 16px;
            margin-top: -50px;
            color: #fff;
            font-weight: bold;
            font-size: 40px;
            user-select: none;
            z-index: 10001;
            background: rgba(0,0,0,0.2);
            border-radius: 6px;
        }

        .prev { left: 10px; }
        .next { right: 10px; }

        .modal-caption {
            text-align: center;
            color: #bbb;
            margin-top: 10px;
            position: absolute;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10001;
            font-size: 14px;
        }

        .modal-controls {
            position: absolute;
            top: 20px;
            left: 40px;
            z-index: 10001;
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .control-btn {
            background: rgba(255,255,255,0.06);
            color: #fff;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.06);
        }

        .control-btn.playing {
            background: rgba(79, 172, 254, 0.95);
            color: #04213a;
            border-color: rgba(79,172,254,0.7);
        }

        @media (max-width: 480px) {
            .close { right: 20px; font-size: 36px; top: 14px; }
            .prev, .next { font-size: 32px; padding: 12px; }
            .modal-caption { font-size: 13px; bottom: 18px; }
        }
    </style>'''
        
        html_parts.append(css)
        html_parts.append('</head>')
        html_parts.append('<body>')
        
        # Header
        html_parts.append('    <div class="header">')
        html_parts.append(f'        <h1>{title}</h1>')
        html_parts.append(f'        <div class="breadcrumb">{os.getcwd()}</div>')
        html_parts.append('    </div>')
        
        html_parts.append('    <div class="container">')
        
        # Parent Directory Button
        if url_path != '/':
            parent_path = '/'.join(url_path.rstrip('/').split('/')[:-1]) + '/' if url_path.count('/') > 1 else '/'
            html_parts.append(f'        <a href="{parent_path}" class="parent-button">')
            html_parts.append('            ⬆️ Back to Parent Folder')
            html_parts.append('        </a>')
        else:
            html_parts.append('        <div class="parent-button disabled">')
            html_parts.append('            📁 Root Directory')
            html_parts.append('        </div>')
        
        # Count visible entries
        visible_entries = [e for e in entries if not e.startswith('.')]
        
        if not visible_entries:
            html_parts.append('        <div class="no-items">📁 This directory is empty</div>')
        else:
            html_parts.append('        <div class="grid">')
            
            # Process entries
            for entry in visible_entries:
                entry_path = os.path.join(dir_path, entry)
                url_entry_path = urllib.parse.quote(entry)
                
                if os.path.isdir(entry_path):
                    # Directory
                    full_url = f"{url_path.rstrip('/')}/{url_entry_path}/"
                    html_parts.extend([
                        '            <div class="item fade-in">',
                        f'                <a href="{full_url}" class="directory">',
                        '                    <span class="directory-icon">📁</span>',
                        f'                    <div>{self.escape_html(entry)}</div>',
                        '                </a>',
                        '            </div>'
                    ])
                elif self.is_image_file(entry):
                    # Image file with thumbnail
                    full_url = f"{url_path.rstrip('/')}/{url_entry_path}"
                    thumb_url = f"{full_url}?thumb=1"
                    file_size = self.get_file_size(entry_path)
                    file_ext = os.path.splitext(entry)[1][1:].upper()
                    
                    html_parts.extend([
                        '            <div class="item fade-in">',
                        f'                <a href="{full_url}" target="_blank">',
                        '                    <div class="thumbnail-container">',
                        f'                        <img src="{thumb_url}" data-full="{full_url}" alt="{self.escape_html(entry)}" class="thumbnail" loading="lazy">',
                        '                        <div class="loading" style="display: none;">🖼️ Image unavailable</div>',
                        f'                        <div class="image-overlay">{file_ext}</div>',
                        '                    </div>',
                        '                    <div class="item-content">',
                        f'                        <div class="filename">{self.escape_html(entry)}</div>',
                        '                        <div class="file-info">',
                        f'                            <span>{file_size}</span>',
                        '                            <span class="file-type">Image</span>',
                        '                        </div>',
                        '                    </div>',
                        '                </a>',
                        '            </div>'
                    ])
                else:
                    # Regular file
                    full_url = f"{url_path.rstrip('/')}/{url_entry_path}"
                    file_size = self.get_file_size(entry_path)
                    file_ext = os.path.splitext(entry)[1][1:].upper() or 'FILE'
                    
                    # Get file type icon
                    file_icon = self.get_file_icon(entry)
                    
                    # Check if file might be text-readable
                    is_text_file = self.is_text_file(entry)
                    target_attr = '' if is_text_file else ' target="_blank"'
                    
                    html_parts.extend([
                        '            <div class="item fade-in">',
                        f'                <a href="{full_url}"{target_attr}>',
                        '                    <div class="thumbnail-container">',
                        '                        <div class="directory" style="background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);">',
                        f'                            <span class="directory-icon">{file_icon}</span>',
                        f'                            <div>{file_ext}</div>',
                        '                        </div>',
                        '                    </div>',
                        '                    <div class="item-content">',
                        f'                        <div class="filename">{self.escape_html(entry)}</div>',
                        '                        <div class="file-info">',
                        f'                            <span>{file_size}</span>',
                        f'                            <span class="file-type">{"Text" if is_text_file else "File"}</span>',
                        '                        </div>',
                        '                    </div>',
                        '                </a>',
                        '            </div>'
                    ])
            
            html_parts.append('        </div>')
        
        html_parts.extend([
            '    </div>',
            '',
            # Modal HTML
            '<!-- Image Modal -->',
            '<div id="imgModal" class="modal" aria-hidden="true">',
            '  <div class="modal-inner" role="dialog" aria-modal="true" aria-label="Image viewer">',
            '    <div class="modal-controls">',
            '      <button id="slideshowBtn" class="control-btn" title="Toggle slideshow">▶ Play</button>',
            '      <button id="zoomResetBtn" class="control-btn" title="Reset zoom">Reset</button>',
            '    </div>',
            '    <span class="close" id="modalClose" aria-label="Close">&times;</span>',
            '    <a class="prev" id="modalPrev" aria-label="Previous image">&#10094;</a>',
            '    <img class="modal-content" id="modalImg" src="" alt="">',
            '    <a class="next" id="modalNext" aria-label="Next image">&#10095;</a>',
            '    <div class="modal-caption" id="modalCaption"></div>',
            '  </div>',
            '</div>',
            '',
            '    <script>',
            '        (function(){',
            '            // Utilities',
            '            const q = s => document.querySelector(s);',
            '            const qa = s => Array.from(document.querySelectorAll(s));',
            '',
            '            document.addEventListener("DOMContentLoaded", function () {',
            '                // Fade-in stagger',
            '                const items = document.querySelectorAll(".fade-in");',
            '                items.forEach((item, index) => {',
            '                    item.style.animationDelay = (index * 0.1) + "s";',
            '                });',
            '',
            '                // Lazy thumb animations',
            '                qa(".thumbnail").forEach(img => {',
            '                    img.addEventListener("load", function () { this.style.opacity = "1"; });',
            '                    img.addEventListener("error", function () { this.style.display = "none"; this.nextElementSibling.style.display = "block"; });',
            '                    img.style.opacity = "0";',
            '                    img.style.transition = "opacity 0.3s ease";',
            '                });',
            '',
            '                // Modal elements',
            '                const modal = q("#imgModal");',
            '                const modalImg = q("#modalImg");',
            '                const modalCaption = q("#modalCaption");',
            '                const closeBtn = q("#modalClose");',
            '                const prevBtn = q("#modalPrev");',
            '                const nextBtn = q("#modalNext");',
            '                const slideshowBtn = q("#slideshowBtn");',
            '                const zoomResetBtn = q("#zoomResetBtn");',
            '',
            '                const thumbnails = qa(".thumbnail");',
            '                let currentIndex = 0;',
            '',
            '                // Zoom & pan state',
            '                let scale = 1, minScale = 1, maxScale = 5;',
            '                let translateX = 0, translateY = 0;',
            '                let isPanning = false, startX = 0, startY = 0;',
            '',
            '                // Slideshow state',
            '                let slideshowInterval = null;',
            '                const SLIDE_DELAY = 3000; // 3s per slide',
            '',
            '                function resetTransform() {',
            '                    scale = 1; translateX = 0; translateY = 0;',
            '                    applyTransform();',
            '                }',
            '',
            '                function applyTransform() {',
            '                    modalImg.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;',
            '                }',
            '',
            '                function openModal(index) {',
            '                    if (thumbnails.length === 0) return;',
            '                    currentIndex = (index + thumbnails.length) % thumbnails.length;',
            '                    const thumb = thumbnails[currentIndex];',
            '                    const full = thumb.dataset.full || thumb.src;',
            '                    modalImg.src = full;',
            '                    modalImg.alt = thumb.alt || "";',
            '                    modalCaption.textContent = thumb.alt || "";',
            '                    modal.style.display = "block";',
            '                    modal.setAttribute("aria-hidden", "false");',
            '                    resetTransform();',
            '                    // focus for keyboard events',
            '                    setTimeout(()=> modal.focus && modal.focus(), 50);',
            '                }',
            '',
            '                function closeModal() {',
            '                    modal.style.display = "none";',
            '                    modal.setAttribute("aria-hidden", "true");',
            '                    stopSlideshow();',
            '                }',
            '',
            '                function showNext() {',
            '                    openModal(currentIndex + 1);',
            '                }',
            '',
            '                function showPrev() {',
            '                    openModal(currentIndex - 1);',
            '                }',
            '',
            '                // Thumbnail handlers',
            '                thumbnails.forEach((thumb, index) => {',
            '                    // Single click → modal open',
            '                    thumb.addEventListener("click", function (event) {',
            '                        event.preventDefault();',
            '                        openModal(index);',
            '                    });',
            '',
            '                    // Double-click → open image in new tab',
            '                    thumb.addEventListener("dblclick", function (event) {',
            '                        event.preventDefault();',
            '                        const href = thumb.parentElement.parentElement.href || thumb.dataset.full || thumb.src;',
            '                        window.open(href, "_blank");',
            '                    });',
            '                });',
            '',
            '                // Modal button events',
            '                closeBtn.addEventListener("click", closeModal);',
            '                prevBtn.addEventListener("click", showPrev);',
            '                nextBtn.addEventListener("click", showNext);',
            '',
            '                // Keyboard navigation (← → Esc) and space toggles slideshow',
            '                document.addEventListener("keydown", function(e) {',
            '                    if (modal.style.display !== "block") return;',
            '                    if (e.key === "ArrowRight") { showNext(); }',
            '                    else if (e.key === "ArrowLeft") { showPrev(); }',
            '                    else if (e.key === "Escape") { closeModal(); }',
            '                    else if (e.key === " " || e.key === "Spacebar") { // space toggles slideshow',
            '                        e.preventDefault();',
            '                        toggleSlideshow();',
            '                    }',
            '                });',
            '',
            '                // Slideshow controls',
            '                function startSlideshow() {',
            '                    if (slideshowInterval) return;',
            '                    slideshowBtn.classList.add("playing");',
            '                    slideshowBtn.textContent = "⏸ Pause";',
            '                    slideshowInterval = setInterval(showNext, SLIDE_DELAY);',
            '                }',
            '                function stopSlideshow() {',
            '                    if (!slideshowInterval) return;',
            '                    slideshowBtn.classList.remove("playing");',
            '                    slideshowBtn.textContent = "▶ Play";',
            '                    clearInterval(slideshowInterval); slideshowInterval = null;',
            '                }',
            '                function toggleSlideshow() {',
            '                    if (slideshowInterval) stopSlideshow(); else startSlideshow();',
            '                }',
            '                slideshowBtn.addEventListener("click", toggleSlideshow);',
            '                // Reset zoom button',
            '                zoomResetBtn.addEventListener("click", resetTransform);',
            '',
            '                // Click on modal image toggles fullscreen',
            '                modalImg.addEventListener("click", function(e) {',
            '                    // If image is zoomed (scale>1), do nothing on click to avoid accidental fullscreen toggle',
            '                    if (Math.abs(scale - 1) > 0.01) return;',
            '                    toggleFullScreen();',
            '                });',
            '',
            '                // Fullscreen helpers',
            '                function toggleFullScreen() {',
            '                    if (!document.fullscreenElement) {',
            '                        if (modal.requestFullscreen) modal.requestFullscreen();',
            '                        else if (modal.webkitRequestFullscreen) modal.webkitRequestFullscreen();',
            '                    } else {',
            '                        if (document.exitFullscreen) document.exitFullscreen();',
            '                        else if (document.webkitExitFullscreen) document.webkitExitFullscreen();',
            '                    }',
            '                }',
            '',
            '                // Mouse wheel for zoom (desktop)',
            '                modalImg.addEventListener("wheel", function(e) {',
            '                    if (modal.style.display !== "block") return;',
            '                    e.preventDefault();',
            '                    const delta = -e.deltaY || e.wheelDelta;',
            '                    const zoomFactor = delta > 0 ? 1.08 : 0.92;',
            '                    const newScale = Math.min(maxScale, Math.max(minScale, scale * zoomFactor));',
            '                    // adjust translate so zoom is centered at mouse position',
            '                    const rect = modalImg.getBoundingClientRect();',
            '                    const mx = e.clientX - rect.left;',
            '                    const my = e.clientY - rect.top;',
            '                    const dx = (mx - translateX) / scale;',
            '                    const dy = (my - translateY) / scale;',
            '                    translateX = mx - dx * newScale;',
            '                    translateY = my - dy * newScale;',
            '                    scale = newScale;',
            '                    applyTransform();',
            '                }, { passive: false });',
            '',
            '                // Drag to pan (mouse)',
            '                modalImg.addEventListener("mousedown", function(e) {',
            '                    if (scale <= 1) return;',
            '                    isPanning = true;',
            '                    startX = e.clientX - translateX;',
            '                    startY = e.clientY - translateY;',
            '                    modalImg.classList.add("grabbing");',
            '                });',
            '                document.addEventListener("mousemove", function(e) {',
            '                    if (!isPanning) return;',
            '                    translateX = e.clientX - startX;',
            '                    translateY = e.clientY - startY;',
            '                    applyTransform();',
            '                });',
            '                document.addEventListener("mouseup", function() {',
            '                    isPanning = false; modalImg.classList.remove("grabbing");',
            '                });',
            '',
            '                // Touch handling: pan, swipe, pinch-zoom',
            '                let touchStartX = 0, touchStartY = 0, touchStartTime = 0;',
            '                let lastTouchDistance = null;',
            '                let isTouchPanning = false;',
            '',
            '                modalImg.addEventListener("touchstart", function(e) {',
            '                    if (e.touches.length === 1) {',
            '                        touchStartX = e.touches[0].clientX;',
            '                        touchStartY = e.touches[0].clientY;',
            '                        touchStartTime = Date.now();',
            '                        isTouchPanning = (scale > 1);',
            '                        startX = e.touches[0].clientX - translateX;',
            '                        startY = e.touches[0].clientY - translateY;',
            '                        lastTouchDistance = null;',
            '                    } else if (e.touches.length === 2) {',
            '                        lastTouchDistance = Math.hypot(',
            '                            e.touches[0].clientX - e.touches[1].clientX,',
            '                            e.touches[0].clientY - e.touches[1].clientY',
            '                        );',
            '                    }',
            '                }, { passive: false });',
            '',
            '                modalImg.addEventListener("touchmove", function(e) {',
            '                    if (e.touches.length === 1 && isTouchPanning) {',
            '                        e.preventDefault();',
            '                        translateX = e.touches[0].clientX - startX;',
            '                        translateY = e.touches[0].clientY - startY;',
            '                        applyTransform();',
            '                    } else if (e.touches.length === 2) {',
            '                        e.preventDefault();',
            '                        const dist = Math.hypot(',
            '                            e.touches[0].clientX - e.touches[1].clientX,',
            '                            e.touches[0].clientY - e.touches[1].clientY',
            '                        );',
            '                        if (lastTouchDistance) {',
            '                            const zoomFactor = dist / lastTouchDistance;',
            '                            const newScale = Math.min(maxScale, Math.max(minScale, scale * zoomFactor));',
            '                            // center between touches',
            '                            const rect = modalImg.getBoundingClientRect();',
            '                            const mx = (e.touches[0].clientX + e.touches[1].clientX)/2 - rect.left;',
            '                            const my = (e.touches[0].clientY + e.touches[1].clientY)/2 - rect.top;',
            '                            const dx = (mx - translateX) / scale;',
            '                            const dy = (my - translateY) / scale;',
            '                            translateX = mx - dx * newScale;',
            '                            translateY = my - dy * newScale;',
            '                            scale = newScale;',
            '                            applyTransform();',
            '                        }',
            '                        lastTouchDistance = dist;',
            '                    }',
            '                }, { passive: false });',
            '',
            '                modalImg.addEventListener("touchend", function(e) {',
            '                    // detect swipe left/right for quick navigation when not zooming',
            '                    if (e.changedTouches.length === 1 && Math.abs(scale - 1) < 0.01) {',
            '                        const dx = e.changedTouches[0].clientX - touchStartX;',
            '                        const dt = Date.now() - touchStartTime;',
            '                        if (dt < 500 && Math.abs(dx) > 60) {',
            '                            if (dx < 0) showNext(); else showPrev();',
            '                        } else {',
            '                            // detect single tap vs double-tap for fullscreen toggle or open in new tab',
            '                            const target = e.target;',
            '                            // single tap: open fullscreen if not zoomed',
            '                        }',
            '                    }',
            '                    // reset pinch state',
            '                    lastTouchDistance = null; isTouchPanning = false;',
            '                });',
            '',
            '                // Double-tap to zoom (mobile)',
            '                let lastTap = 0;',
            '                modalImg.addEventListener("touchend", function(e) {',
            '                    const currentTime = Date.now();',
            '                    const tapLength = currentTime - lastTap;',
            '                    if (tapLength < 300 && tapLength > 0) {',
            '                        // double tap -> toggle zoom between min and 2x (or maxScale)',
            '                        if (scale <= 1.01) scale = Math.min(2, maxScale);',
            '                        else scale = 1;',
            '                        applyTransform();',
            '                    }',
            '                    lastTap = currentTime;',
            '                });',
            '',
            '                // Prevent gestures outside modal from scrolling the body while modal open',
            '                modal.addEventListener("touchmove", function(e){ if (modal.style.display === "block") e.preventDefault(); }, { passive:false });',
            '',
            '                // Accessibility: close on focus loss (optional) and trap focus could be added later',
            '',
            '                // Close when clicking outside image (but allow clicks on controls)',
            '                modal.addEventListener("click", function(e) {',
            '                    if (e.target === modal) closeModal();',
            '                });',
            '',
            '                // Clean up image transforms when an image fails to load',
            '                modalImg.addEventListener("error", function(){ resetTransform(); });',
            '',
            '            });',
            '        })();',
            '    </script>',
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)
    
    def escape_html(self, text):
        """Escape HTML special characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def is_image_file(self, filename):
        """Check if file is an image based on extension"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
        return os.path.splitext(filename.lower())[1] in image_extensions
    
    def is_text_file(self, filename):
        """Check if file is likely a text file that should open in browser"""
        text_extensions = {
            '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', 
            '.csv', '.log', '.ini', '.cfg', '.conf', '.yml', '.yaml',
            '.sh', '.bat', '.ps1', '.php', '.rb', '.go', '.rs', '.cpp',
            '.c', '.h', '.java', '.kt', '.swift', '.ts', '.jsx', '.tsx',
            '.vue', '.sql', '.r', '.scala', '.dart', '.asm'
        }
        return os.path.splitext(filename.lower())[1] in text_extensions
    
    def get_file_icon(self, filename):
        """Get appropriate icon for file type"""
        ext = os.path.splitext(filename.lower())[1]
        
        icon_map = {
            '.pdf': '📄',
            '.doc': '📝', '.docx': '📝',
            '.txt': '📄', '.md': '📄', '.log': '📄',
            '.zip': '🗜️', '.rar': '🗜️', '.7z': '🗜️',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
            '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬',
            '.py': '🐍', '.js': '📜', '.html': '🌐',
            '.css': '🎨', '.json': '📋',
            '.xlsx': '📊', '.csv': '📊',
            '.exe': '⚙️', '.app': '⚙️',
        }
        
        return icon_map.get(ext, '📄')
    
    def get_file_size(self, filepath):
        """Get human-readable file size"""
        try:
            size = os.path.getsize(filepath)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except OSError:
            return "Unknown size"


def create_handler_class(thumbnail_size):
    """Create a handler class with custom thumbnail size"""
    class CustomThumbnailHandler(ThumbnailHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, thumbnail_size=thumbnail_size, **kwargs)
    return CustomThumbnailHandler


def main():
    parser = argparse.ArgumentParser(description='Modern HTTP server with image thumbnails')
    parser.add_argument('port', type=int, nargs='?', default=8000, 
                        help='Port to serve on (default: 8000)')
    parser.add_argument('--thumbnail-size', type=int, default=200,
                        help='Thumbnail size in pixels (default: 200)')
    parser.add_argument('--directory', '-d', default='.',
                        help='Directory to serve (default: current directory)')
    
    args = parser.parse_args()
    
    # Change to the specified directory
    os.chdir(args.directory)
    
    # Create handler class with custom thumbnail size
    handler_class = create_handler_class(args.thumbnail_size)
    
    # Start server
    with socketserver.TCPServer(("", args.port), handler_class) as httpd:
        print(f"🚀 Modern Gallery Server running at http://localhost:{args.port}")
        print(f"📁 Directory: {os.getcwd()}")
        print(f"🖼️  Thumbnail size: {args.thumbnail_size}px")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✨ Server stopped gracefully.")


if __name__ == "__main__":
    main()

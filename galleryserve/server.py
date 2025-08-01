

# ===========================================
# File: thumbnail_server/server.py (Updated with License Gates)
# ===========================================
import http.server
import socketserver
import os
import urllib.parse
from PIL import Image
import io
import zipfile
import tempfile
from .license import LicenseManager

class ThumbnailHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, thumbnail_size=200, **kwargs):
        self.thumbnail_size = thumbnail_size
        self.license_manager = LicenseManager()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # Handle special endpoints
        if self.path == '/_upgrade':
            self._serve_upgrade_page()
            return
        elif self.path == '/_license':
            self._serve_license_page()
            return
        elif self.path.startswith('/_download_bulk'):
            if not self.license_manager.has_feature('bulk_download'):
                self._serve_feature_gate('bulk_download')
                return
            self._serve_bulk_download(query_params)
            return
            
        # Check for thumbnail request
        if 'thumb' in query_params and parsed_path.path != '/':
            self.serve_thumbnail(parsed_path.path)
        elif parsed_path.path == '/' or parsed_path.path.endswith('/'):
            self.serve_directory_with_thumbnails(parsed_path.path)
        else:
            super().do_GET()
    
    def serve_directory_with_thumbnails(self, path):
        """Serve directory with thumbnails and feature gates"""
        try:
            dir_path = urllib.parse.unquote(path[1:]) if path != '/' else '.'
            
            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                self.send_error(404, "Directory not found")
                return
            
            entries = os.listdir(dir_path)
            entries.sort()
            
            html = self._generate_gallery_html(dir_path, entries, path)
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Error: {e}")
    
    def _generate_gallery_html(self, dir_path, entries, url_path):
        """Generate HTML with license-aware features"""
        has_password = self.license_manager.has_feature('password_protection')
        has_bulk = self.license_manager.has_feature('bulk_download')
        has_multi = self.license_manager.has_feature('multi_selection')
        
        title = f"Gallery: {url_path}"
        
        # License indicator
        license_badge = "🔓 BASIC" if self.license_manager.current_tier == "basic" else "🚀 ADVANCED"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            transition: all 0.3s ease;
        }}
        
        /* Light theme (default) */
        :root {{
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #333333;
            --border-color: #e9ecef;
            --accent-color: #007bff;
            --hover-color: #0056b3;
        }}
        
        /* Dark theme */
        [data-theme="dark"] {{
            --bg-color: #1a1a1a;
            --card-bg: #2d2d2d;
            --text-color: #ffffff;
            --border-color: #404040;
            --accent-color: #4dabf7;
            --hover-color: #339af0;
        }}
        
        .header {{
            background: var(--card-bg);
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .title {{
            font-size: 24px;
            font-weight: 600;
            color: var(--text-color);
        }}
        
        .controls {{
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .license-badge {{
            background: var(--accent-color);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            background: var(--accent-color);
            color: white;
            text-decoration: none;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        
        .btn:hover {{ background: var(--hover-color); }}
        .btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        
        .btn-secondary {{
            background: var(--border-color);
            color: var(--text-color);
        }}
        
        .btn-upgrade {{
            background: linear-gradient(135deg, #ff6b6b, #ffd93d);
            color: #000;
            font-weight: 600;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .item {{
            background: var(--card-bg);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            position: relative;
        }}
        
        .item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.15);
        }}
        
        .thumbnail {{
            width: 100%;
            height: 200px;
            object-fit: cover;
            display: block;
        }}
        
        .item-info {{
            padding: 15px;
        }}
        
        .filename {{
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 5px;
            word-break: break-word;
        }}
        
        .file-size {{
            font-size: 12px;
            color: #666;
        }}
        
        .checkbox {{
            position: absolute;
            top: 10px;
            left: 10px;
            width: 20px;
            height: 20px;
            z-index: 10;
        }}
        
        .upgrade-prompt {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin: 20px 0;
        }}
        
        /* Mobile responsive */
        @media (max-width: 768px) {{
            .gallery {{ grid-template-columns: repeat(2, 1fr); gap: 10px; }}
            .container {{ padding: 15px; }}
            .header {{ padding: 15px; }}
            .title {{ font-size: 20px; }}
        }}
        
        @media (max-width: 480px) {{
            .gallery {{ grid-template-columns: 1fr; }}
            .controls {{ width: 100%; justify-content: center; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1 class="title">🖼️ {title}</h1>
            <div class="controls">
                <span class="license-badge">{license_badge}</span>
                <button class="btn btn-secondary" onclick="toggleTheme()">🌙 Theme</button>
"""

        # Add advanced controls if licensed
        if has_multi:
            html += """
                <button class="btn" onclick="selectAll()">☑️ Select All</button>
                <button class="btn" onclick="downloadSelected()" id="downloadBtn" disabled>📦 Download Selected</button>
"""
        else:
            html += f"""
                <a href="{self.license_manager.get_upgrade_url('multi_selection')}" class="btn btn-upgrade">
                    🚀 Upgrade for Bulk Downloads
                </a>
"""

        html += """
                <a href="/_license" class="btn btn-secondary">⚙️ License</a>
            </div>
        </div>
    </div>
    
    <div class="container">
"""

        # Add upgrade prompt for basic users
        if self.license_manager.current_tier == "basic":
            html += f"""
        <div class="upgrade-prompt">
            <h3>🚀 Unlock Advanced Features</h3>
            <p>Password protection • Internet sharing • Bulk downloads • Advanced formats</p>
            <a href="{self.license_manager.get_upgrade_url('general')}" class="btn" style="margin-top: 10px;">
                Upgrade to Advanced - $15
            </a>
            <div style="margin-top: 20px;">
                <a href=".." class="btn btn-secondary" style="font-size: 15px;">
                    ⬅️ Go to Parent Folder
                </a>
            </div>
        </div>
"""

        html += '<div class="gallery">'
        
        # Process entries
        image_count = 0
        for entry in entries:
            if entry.startswith('.'):
                continue
                
            entry_path = os.path.join(dir_path, entry)
            url_entry_path = urllib.parse.quote(entry)
            
            if os.path.isdir(entry_path):
                # Directory
                full_url = f"{url_path.rstrip('/')}/{url_entry_path}/"
                html += f"""
                <div class="item">
                    <a href="{full_url}" style="text-decoration: none; color: inherit;">
                        <div style="height: 200px; display: flex; align-items: center; justify-content: center; background: var(--border-color);">
                            <span style="font-size: 48px;">📁</span>
                        </div>
                        <div class="item-info">
                            <div class="filename">{entry}</div>
                            <div class="file-size">Folder</div>
                        </div>
                    </a>
                </div>"""
                
            elif self.is_image_file(entry):
                # Image file
                image_count += 1
                full_url = f"{url_path.rstrip('/')}/{url_entry_path}"
                thumb_url = f"{full_url}?thumb=1"
                file_size = self.get_file_size(entry_path)
                
                checkbox_html = ""
                if has_multi:
                    checkbox_html = f'<input type="checkbox" class="checkbox" value="{full_url}" onchange="updateDownloadButton()">'
                
                html += f"""
                <div class="item">
                    {checkbox_html}
                    <a href="{full_url}" target="_blank" style="text-decoration: none; color: inherit;">
                        <img src="{thumb_url}" alt="{entry}" class="thumbnail" loading="lazy">
                        <div class="item-info">
                            <div class="filename">{entry}</div>
                            <div class="file-size">{file_size}</div>
                        </div>
                    </a>
                </div>"""
        
        html += """
        </div>
    </div>
    
    <script>
        // Theme toggle
        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        }
        
        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.body.setAttribute('data-theme', savedTheme);
        
        // Multi-selection functions
        function selectAll() {
            const checkboxes = document.querySelectorAll('.checkbox');
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
            updateDownloadButton();
        }
        
        function updateDownloadButton() {
            const checkboxes = document.querySelectorAll('.checkbox:checked');
            const downloadBtn = document.getElementById('downloadBtn');
            if (downloadBtn) {
                downloadBtn.disabled = checkboxes.length === 0;
                downloadBtn.textContent = `📦 Download Selected (${checkboxes.length})`;
            }
        }
        
        function downloadSelected() {
            const checkboxes = document.querySelectorAll('.checkbox:checked');
            const urls = Array.from(checkboxes).map(cb => cb.value);
            
            if (urls.length === 0) {
                alert('Please select images to download');
                return;
            }
            
            // Create download request
            const params = new URLSearchParams();
            urls.forEach(url => params.append('file', url));
            
            window.location.href = `/_download_bulk?${params.toString()}`;
        }
    </script>
</body>
</html>"""
        
        return html
    
    def _serve_feature_gate(self, feature):
        """Show upgrade prompt for locked features"""
        feature_names = {
            'password_protection': 'Password Protection',
            'ngrok_sharing': 'Internet Sharing',  
            'bulk_download': 'Bulk Downloads',
            'multi_selection': 'Multi-Selection'
        }
        
        feature_name = feature_names.get(feature, 'Advanced Features')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Upgrade Required</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f8f9fa; }}
                .upgrade-box {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 40px; border-radius: 15px; 
                    max-width: 500px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                }}
                .btn {{ 
                    background: #28a745; color: white; padding: 15px 30px; 
                    text-decoration: none; border-radius: 8px; font-size: 18px;
                    display: inline-block; margin-top: 20px; font-weight: 600;
                }}
                .feature-list {{ text-align: left; max-width: 300px; margin: 20px auto; }}
                .feature-list li {{ margin: 8px 0; }}
            </style>
        </head>
        <body>
            <div class="upgrade-box">
                <h1>🚀 {feature_name} - Advanced Feature</h1>
                <p>You're trying to use <strong>{feature_name}</strong>, which is available in the Advanced edition.</p>
                
                <h3>Advanced Edition includes:</h3>
                <ul class="feature-list">
                    <li>🔐 Password protection</li>
                    <li>🌐 Internet sharing (ngrok)</li>
                    <li>📦 Bulk downloads</li>
                    <li>☑️ Multi-selection</li>
                    <li>📸 Advanced formats (RAW, HEIC)</li>
                    <li>📊 Usage analytics</li>
                </ul>
                
                <a href="{self.license_manager.get_upgrade_url(feature)}" class="btn">
                    Upgrade Now - Only $15
                </a>
                
                <p style="margin-top: 20px; font-size: 14px; opacity: 0.9;">
                    One-time purchase • Instant download • 30-day money-back guarantee
                </p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def _serve_bulk_download(self, query_params):
        """Serve bulk download (Advanced feature)"""
        files = query_params.get('file', [])
        if not files:
            self.send_error(400, "No files specified")
            return
            
        try:
            # Create temporary zip file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
                with zipfile.ZipFile(tmp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_url in files:
                        # Convert URL to file path
                        file_path = urllib.parse.unquote(file_url.lstrip('/'))
                        if os.path.exists(file_path) and self.is_image_file(file_path):
                            # Add file to zip with just the filename
                            arcname = os.path.basename(file_path)
                            zipf.write(file_path, arcname)
                
                # Send zip file
                with open(tmp_zip.name, 'rb') as f:
                    zip_data = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/zip')
                self.send_header('Content-Disposition', 'attachment; filename="gallery_images.zip"')
                self.send_header('Content-Length', str(len(zip_data)))
                self.end_headers()
                self.wfile.write(zip_data)
                
                # Clean up temp file
                os.unlink(tmp_zip.name)
                
        except Exception as e:
            self.send_error(500, f"Error creating download: {e}")
    
    def _serve_license_page(self):
        """Serve license management page"""
        current_tier = self.license_manager.current_tier
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>License Management</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; background: #f8f9fa; }}
                .panel {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .status {{ padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; }}
                .basic {{ background: #e3f2fd; color: #1565c0; }}
                .advanced {{ background: #e8f5e8; color: #2e7d32; }}
                input {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; margin: 10px 0; }}
                .btn {{ background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; }}
                .btn:hover {{ background: #0056b3; }}
                .features {{ margin: 20px 0; }}
                .feature {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
                .available {{ color: #28a745; }}
                .locked {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="panel">
                <h1>📝 License Management</h1>
                
                <div class="status {'advanced' if current_tier == 'advanced' else 'basic'}">
                    <h2>Current License: {current_tier.upper()}</h2>
                </div>
                
                <div class="features">
                    <h3>Feature Status:</h3>
                    <div class="feature">
                        <span class="available">✅ Local HTTP server</span>
                    </div>
                    <div class="feature">
                        <span class="available">✅ Automatic thumbnails</span>
                    </div>
                    <div class="feature">
                        <span class="available">✅ Mobile responsive design</span>
                    </div>
                    <div class="feature">
                        <span class="available">✅ Dark/Light mode</span>
                    </div>
                    <div class="feature">
                        <span class="{'available' if current_tier == 'advanced' else 'locked'}">
                            {'✅' if current_tier == 'advanced' else '❌'} Password protection
                        </span>
                    </div>
                    <div class="feature">
                        <span class="{'available' if current_tier == 'advanced' else 'locked'}">
                            {'✅' if current_tier == 'advanced' else '❌'} Internet sharing (ngrok)
                        </span>
                    </div>
                    <div class="feature">
                        <span class="{'available' if current_tier == 'advanced' else 'locked'}">
                            {'✅' if current_tier == 'advanced' else '❌'} Bulk downloads
                        </span>
                    </div>
                    <div class="feature">
                        <span class="{'available' if current_tier == 'advanced' else 'locked'}">
                            {'✅' if current_tier == 'advanced' else '❌'} Multi-selection
                        </span>
                    </div>
                </div>
                
                <form method="post" action="/_activate_license">
                    <h3>Activate License:</h3>
                    <input type="text" name="license_key" placeholder="Enter license key (e.g., ADVANCED-XXXXX)" required>
                    <button type="submit" class="btn">Activate License</button>
                </form>
                
                <div style="margin-top: 30px; text-align: center; padding-top: 20px; border-top: 1px solid #eee;">
                    <p>Don't have an Advanced license?</p>
                    <a href="{self.license_manager.get_upgrade_url('license_page')}" class="btn">
                        Get Advanced License - $15
                    </a>
                </div>
                
                <div style="margin-top: 20px; font-size: 12px; color: #666; text-align: center;">
                    <p>Basic Edition: Local gallery hosting</p>
                    <p>Advanced Edition: Password protection + Internet sharing + Bulk downloads</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def _serve_upgrade_page(self):
        """Serve upgrade information page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Upgrade to Advanced</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
                .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 50px; border-radius: 15px; text-align: center; }
                .comparison { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin: 40px 0; }
                .plan { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .plan h3 { text-align: center; margin-bottom: 20px; }
                .price { font-size: 36px; font-weight: bold; text-align: center; margin: 20px 0; }
                .features { list-style: none; padding: 0; }
                .features li { padding: 8px 0; border-bottom: 1px solid #eee; }
                .included { color: #28a745; }
                .not-included { color: #dc3545; }
                .btn-buy { background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: block; text-align: center; margin: 20px 0; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="hero">
                <h1>🚀 Upgrade to Advanced Edition</h1>
                <p>Unlock professional features for client galleries and internet sharing</p>
            </div>
            
            <div class="comparison">
                <div class="plan">
                    <h3>📦 Basic Edition</h3>
                    <div class="price">$5</div>
                    <ul class="features">
                        <li class="included">✅ Local HTTP server</li>
                        <li class="included">✅ Automatic thumbnails</li>
                        <li class="included">✅ Mobile responsive</li>
                        <li class="included">✅ Dark/Light themes</li>
                        <li class="not-included">❌ Password protection</li>
                        <li class="not-included">❌ Internet sharing</li>
                        <li class="not-included">❌ Bulk downloads</li>
                        <li class="not-included">❌ Advanced formats</li>
                    </ul>
                </div>
                
                <div class="plan" style="border: 3px solid #28a745;">
                    <h3>🚀 Advanced Edition</h3>
                    <div class="price" style="color: #28a745;">$15</div>
                    <ul class="features">
                        <li class="included">✅ Everything in Basic</li>
                        <li class="included">✅ Password protection</li>
                        <li class="included">✅ Internet sharing (ngrok)</li>
                        <li class="included">✅ Bulk downloads</li>
                        <li class="included">✅ Multi-selection</li>
                        <li class="included">✅ Advanced formats (RAW, HEIC)</li>
                        <li class="included">✅ Usage analytics</li>
                        <li class="included">✅ Priority support</li>
                    </ul>
                    <a href="https://gumroad.com/l/thumbnail-server-advanced" class="btn-buy">
                        Upgrade Now - $15
                    </a>
                </div>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <h3>Perfect for:</h3>
                <p>📸 Professional photographers sharing client galleries</p>
                <p>🎨 Design agencies presenting work to clients</p>
                <p>👥 Remote teams sharing visual assets</p>
                <p>🏢 Small businesses with image-heavy workflows</p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    # ... (rest of existing methods: serve_thumbnail, is_image_file, get_file_size)
    def serve_thumbnail(self, path):
        """Generate and serve a thumbnail for an image"""
        try:
            file_path = urllib.parse.unquote(path[1:])
            
            if not os.path.exists(file_path) or not self.is_image_file(file_path):
                self.send_error(404, "File not found or not an image")
                return
            
            with Image.open(file_path) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                img.thumbnail((self.thumbnail_size, self.thumbnail_size), Image.Resampling.LANCZOS)
                
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG', quality=85)
                img_bytes.seek(0)
                
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', len(img_bytes.getvalue()))
                self.send_header('Cache-Control', 'max-age=3600')
                self.end_headers()
                self.wfile.write(img_bytes.getvalue())
                
        except Exception as e:
            print(f"Error generating thumbnail for {path}: {e}")
            self.send_error(500, f"Error generating thumbnail: {str(e)}")

    def is_image_file(self, filename):
        """Check if file is an image based on extension"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
        return os.path.splitext(filename.lower())[1] in image_extensions

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


# ===========================================
# File: thumbnail_server/cli.py (Updated)
# ===========================================
import argparse
import os
# from server import start_server
from .license import LicenseManager
from .server import ThumbnailHTTPRequestHandler

def main():
    parser = argparse.ArgumentParser(
        description='Thumbnail Server - Professional Image Gallery',
        prog='thumbnail-server'
    )
    parser.add_argument('port', type=int, nargs='?', default=8000, 
                        help='Port to serve on (default: 8000)')
    parser.add_argument('--directory', '-d', default='.',
                        help='Directory to serve (default: current directory)')
    parser.add_argument('--activate', help='Activate license with key')
    parser.add_argument('--status', action='store_true', help='Show license status')
    parser.add_argument('--version', action='version', version='thumbnail-server 1.0.0')
    
    args = parser.parse_args()
    
    license_manager = LicenseManager()
    
    # Handle license activation
    if args.activate:
        success, message = license_manager.activate_license(args.activate)
        print(message)
        if success:
            print(f"🎉 Welcome to Thumbnail Server {license_manager.current_tier.title()}!")
        return
    
    # Handle status check
    if args.status:
        print(f"📋 License Status: {license_manager.current_tier.upper()}")
        
        if license_manager.current_tier == "basic":
            print("\n📦 Basic Features:")
            print("  ✅ Local HTTP server")
            print("  ✅ Automatic thumbnails") 
            print("  ✅ Mobile responsive design")
            print("  ✅ Dark/Light themes")
            print("\n🚀 Advanced Features (Locked):")
            print("  ❌ Password protection")
            print("  ❌ Internet sharing (ngrok)")
            print("  ❌ Bulk downloads")
            print("  ❌ Multi-selection")
            print(f"\n💡 Upgrade: {license_manager.get_upgrade_url('status')}")
        else:
            print("\n🚀 All Features Unlocked!")
            print("  ✅ Password protection")
            print("  ✅ Internet sharing")
            print("  ✅ Bulk downloads")
            print("  ✅ Multi-selection")
        return
    
    # Show startup banner
    print("🖼️  Thumbnail Server v1.0.0")
    
    if license_manager.current_tier == "basic":
        print("📦 Basic Edition")
        print("💡 Upgrade to Advanced for password protection & internet sharing")
        print(f"   {license_manager.get_upgrade_url('startup')}")
    else:
        print("🚀 Advanced Edition - All features unlocked!")
    
    print(f"\n📁 Directory: {os.path.abspath(args.directory)}")
    print(f"🔗 Local URL: http://localhost:{args.port}")
    print("⚙️  License page: http://localhost:{}//_license".format(args.port))
    print("\n" + "="*60)
    
    start_server(
        port=args.port,
        directory=args.directory
    )

def start_server(port=8000, directory='.'):
    """Start the thumbnail server"""
    import socketserver
    
    os.chdir(directory)
    
    def create_handler_class():
        class CustomHandler(ThumbnailHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
        return CustomHandler
    
    handler_class = create_handler_class()
    
    with socketserver.TCPServer(("", port), handler_class) as httpd:
        print(f"🚀 Server running at http://localhost:{port}")
        print("Press Ctrl+C to stop the server\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()
            print("\n🛑 Server stopped.")

if __name__ == "__main__":
    main()
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
        description='GalleryServe - Professional Image Gallery',
        prog='galleryserve'
    )
    parser.add_argument('port', type=int, nargs='?', default=8000, 
                        help='Port to serve on (default: 8000)')
    parser.add_argument('--directory', '-d', default='.',
                        help='Directory to serve (default: current directory)')
    parser.add_argument('--activate', help='Activate license with key')
    parser.add_argument('--status', action='store_true', help='Show license status')
    parser.add_argument('--version', action='version', version='thumbnail-server 1.0.0')
    parser.add_argument('--kill', action='store_true', help='Kill the server')
    parser.add_argument('--password', nargs='?', type=str, help='Set a password for the gallery')
    parser.add_argument("--internet", action="store_true", help="Enable public internet access \
        using ngrok tunnel (requires internet connection)")
    
    args = parser.parse_args()
    
    license_manager = LicenseManager()
    

    if args.kill:
        # kill the port which already running the galleryserve
        import signal
        import socket
        import psutil

        port = args.port
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                pid = conn.pid
                if pid:
                    p = psutil.Process(pid)
                    print(f"Killing process {pid} on port {port} ({p.name()})")
                    p.terminate()  # or p.kill() for force kill
                    p.wait(timeout=3)
                    print("Process terminated.")
                    return True
        return


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
    print("🖼️  GalleryServe v1.0.0")
    
    if license_manager.current_tier == "basic":
        print("📦 Basic Edition")
        print("💡 Upgrade to Advanced for password protection & internet sharing")
        print(f"   {license_manager.get_upgrade_url('startup')}")
    else:
        print("🚀 Advanced Edition - All features unlocked!")
        if args.password:
            LicenseManager.password = args.password
            print(f"🔒 Password set to: {args.password}")
    
    print(f"\n📁 Directory: {os.path.abspath(args.directory)}")
    print(f"🔗 Local URL: http://localhost:{args.port}")
    print("⚙️  License page: http://localhost:{}//_license".format(args.port))
    print("\n" + "="*60)
    

     # If Advanced Edition, start ngrok
    if args.internet and license_manager.current_tier == "advanced":
        try:
            from pyngrok import ngrok
            public_url = ngrok.connect(args.port)
            print(f"🌐 Public URL: {public_url}")
        except Exception as e:
            print(f"❌ Failed to start ngrok tunnel: {e}")
    else:
        print("🌐 Public sharing via ngrok is disabled in Basic Edition.")

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
            print("\n🛑 Server stopped by user.")
        finally:
            httpd.server_close()
            httpd.shutdown()
            print("✅ Port released.")

    httpd.shutdown()

if __name__ == "__main__":
    main()
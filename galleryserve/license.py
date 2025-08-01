# ===========================================
# File: thumbnail_server/license.py
# ===========================================
import hashlib
import json
from pathlib import Path
from datetime import datetime

class LicenseManager:
    BASIC = "basic"
    ADVANCED = "advanced"
    
    def __init__(self):
        self.license_file = Path.home() / '.thumbnail_server_license'
        self.current_tier = self.BASIC
        self._load_license()
    
    def _load_license(self):
        """Load license from file"""
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r') as f:
                    data = json.load(f)
                self.current_tier = data.get('tier', self.BASIC)
            except:
                self.current_tier = self.BASIC
    
    def activate_license(self, license_key):
        """Activate license with key"""
        # Simple key validation (in real app, verify with server)
        tier = self._validate_key(license_key)
        if tier:
            license_data = {
                'key': license_key,
                'tier': tier,
                'activated': datetime.now().isoformat()
            }
            
            with open(self.license_file, 'w') as f:
                json.dump(license_data, f)
            
            self.current_tier = tier
            return True, f"✅ {tier.title()} license activated!"
        
        return False, "❌ Invalid license key"
    
    def _validate_key(self, key):
        """Validate license key format"""
        # Basic format: BASIC-XXXXX or ADVANCED-XXXXX
        if key.startswith('BASIC-') and len(key) == 11:
            return self.BASIC
        elif key.startswith('ADVANCED-') and len(key) == 15:
            return self.ADVANCED
        return None
    
    def has_feature(self, feature):
        """Check if current license has feature"""
        advanced_features = {
            'password_protection',
            'ngrok_sharing',
            'bulk_download', 
            'multi_selection',
            'admin_panel',
            'advanced_formats',
            'download_tracking'
        }
        
        if feature in advanced_features:
            return self.current_tier == self.ADVANCED
        return True  # Basic features always available
    
    def get_upgrade_url(self, feature):
        """Get upgrade URL for specific feature"""
        return f"https://gumroad.com/l/thumbnail-server-advanced?feature={feature}"
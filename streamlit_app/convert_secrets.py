"""
Helper script to convert GCP service account JSON to Streamlit secrets TOML format

Usage:
    python streamlit_app/convert_secrets.py

This will read your credentials/gcp-service-account.json and output TOML format
that you can copy-paste into Streamlit Cloud secrets.
"""

import json
import sys
from pathlib import Path

def main():
    # Find the service account JSON file
    project_root = Path(__file__).parent.parent
    json_path = project_root / 'credentials' / 'gcp-service-account.json'
    
    if not json_path.exists():
        print(f"❌ Service account JSON not found at: {json_path}")
        print("\nPlease ensure your GCP service account JSON is at:")
        print("  credentials/gcp-service-account.json")
        sys.exit(1)
    
    # Read the JSON file
    try:
        with open(json_path) as f:
            sa = json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        sys.exit(1)
    
    # Convert to TOML format
    print("\n" + "="*70)
    print("STREAMLIT SECRETS (TOML FORMAT)")
    print("="*70)
    print("\n📋 Copy the text below and paste it into Streamlit Cloud secrets:\n")
    print("-"*70)
    
    print("[gcp_service_account]")
    for key, value in sa.items():
        if isinstance(value, str):
            # Escape quotes and backslashes
            escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
            print(f'{key} = "{escaped_value}"')
        elif isinstance(value, bool):
            print(f'{key} = {str(value).lower()}')
        elif isinstance(value, (int, float)):
            print(f'{key} = {value}')
        else:
            print(f'{key} = "{value}"')
    
    print("-"*70)
    print("\n✅ Done! Copy the text above to Streamlit Cloud > Settings > Secrets")
    print("\n💡 Tip: Make sure to preserve the exact formatting, including quotes")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import pyotp
import qrcode
import io
import base64
import secrets

def setup_henrijc_2fa():
    """Generate 2FA setup for Henrijc"""
    username = "Henrijc"
    
    # Generate TOTP secret
    totp_secret = pyotp.random_base32()
    
    # Create TOTP URL for Google Authenticator
    totp_url = f"otpauth://totp/CryptoTradingCoach:{username}?secret={totp_secret}&issuer=CryptoTradingCoach"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_url)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code to file
    qr_path = "/app/henrijc_2fa_qr.png"
    img.save(qr_path)
    
    # Generate backup codes
    backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
    
    # Generate current TOTP code for testing
    totp = pyotp.TOTP(totp_secret)
    current_code = totp.now()
    
    print("🔐 2FA SETUP FOR HENRIJC")
    print("=" * 50)
    print(f"Username: {username}")
    print(f"TOTP Secret: {totp_secret}")
    print(f"QR Code saved to: {qr_path}")
    print(f"Current test code: {current_code}")
    print()
    print("📱 SETUP INSTRUCTIONS:")
    print("1. Install Google Authenticator on your phone")
    print("2. Open the app and tap '+' to add account")
    print("3. Choose 'Scan QR Code'")
    print(f"4. Scan the QR code from: {qr_path}")
    print("5. Enter this test code to verify setup:", current_code)
    print()
    print("🔐 BACKUP CODES (Save these safely!):")
    for i, code in enumerate(backup_codes, 1):
        print(f"{i:2}. {code}")
    print()
    print("🔑 ENVIRONMENT VARIABLES TO ADD:")
    print(f"ADMIN_TOTP_SECRET={totp_secret}")
    print(f"ADMIN_BACKUP_CODES={','.join(backup_codes)}")
    
    return {
        "totp_secret": totp_secret,
        "backup_codes": backup_codes,
        "qr_path": qr_path,
        "current_code": current_code
    }

if __name__ == "__main__":
    setup_henrijc_2fa()
# SSH KEY SETUP GUIDE FOR CRYPTO COACH DEPLOYMENT

## STEP 1: Generate New SSH Key Pair

On your local machine, run:

```bash
# Generate a new RSA key (more compatible than ED25519 for some systems)
ssh-keygen -t rsa -b 4096 -C "crypto-coach-github-actions" -f ~/.ssh/crypto_coach_deploy_rsa

# This creates two files:
# ~/.ssh/crypto_coach_deploy_rsa (private key - for GitHub)
# ~/.ssh/crypto_coach_deploy_rsa.pub (public key - for VPS)
```

## STEP 2: Install Public Key on VPS

```bash
# Copy the public key content
cat ~/.ssh/crypto_coach_deploy_rsa.pub

# SSH to your VPS
ssh cryptoadmin@156.155.253.224

# Add the public key to authorized_keys
echo "PASTE_YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys

# Set correct permissions (CRITICAL)
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
sudo chown cryptoadmin:cryptoadmin ~/.ssh/authorized_keys
```

## STEP 3: Test SSH Key Locally

```bash
# Test the key works from your local machine
ssh -i ~/.ssh/crypto_coach_deploy_rsa cryptoadmin@156.155.253.224

# If this works, proceed to GitHub secret update
```

## STEP 4: Update GitHub Secret

1. Copy the PRIVATE key content:
```bash
cat ~/.ssh/crypto_coach_deploy_rsa
```

2. Go to GitHub repository → Settings → Secrets and variables → Actions
3. Update `VPS_SSH_C_BOT_KEY` with the PRIVATE key content (including headers)

## STEP 5: Alternative - Password Authentication

If SSH keys continue to fail, temporarily enable password authentication:

1. On VPS, edit SSH config:
```bash
sudo nano /etc/ssh/sshd_config
# Ensure: PasswordAuthentication yes
sudo systemctl restart sshd
```

2. In GitHub, create secret `VPS_PASSWORD` with the password for cryptoadmin user

3. Update CI/CD to use password instead of key

## TROUBLESHOOTING CHECKLIST

### On VPS:
- [ ] `.ssh` directory exists and has 700 permissions
- [ ] `authorized_keys` file exists and has 600 permissions
- [ ] Public key is properly added to `authorized_keys`
- [ ] SSH daemon allows key authentication
- [ ] User `cryptoadmin` owns the `.ssh` directory

### In GitHub:
- [ ] Secret `VPS_SSH_C_BOT_KEY` contains the complete private key
- [ ] Private key includes `-----BEGIN` and `-----END` headers
- [ ] No extra spaces or line breaks in the secret

### Local Test:
- [ ] SSH key works from local machine
- [ ] VPS is accessible on port 22
- [ ] User `cryptoadmin` exists and has proper permissions
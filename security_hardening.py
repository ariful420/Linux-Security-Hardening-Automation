#!/bin/bash

# ----------------------------------------
# System Lockdown Script (GRUB + SSH + rd.break protection)
# ----------------------------------------

# Enable logging
exec > >(tee -i /var/log/security_hardening_debug.log)
exec 2>&1

# Validate root privileges
if [ "$EUID" -ne 0 ]; then
  echo "[X] Please run as root."
  exit 1
fi

echo "[+] Starting system lockdown..."

# --- GRUB Password Setup ---
echo "[+] Setting GRUB password..."

# Read password securely
read -sp "Enter your GRUB password: " grub_password
echo
read -sp "Confirm your GRUB password: " grub_password_confirm
echo

if [ "$grub_password" != "$grub_password_confirm" ]; then
  echo "[X] Passwords do not match. Exiting."
  exit 1
fi

# Generate GRUB password hash
echo "[+] Generating GRUB password hash..."
grub_hash=$(yes "$grub_password" | grub2-mkpasswd-pbkdf2 2>/dev/null | awk '/PBKDF2/ {print $NF}')
if [[ -z "$grub_hash" ]]; then
  echo "[X] Failed to generate GRUB password hash. Exiting."
  exit 1
fi
echo "[DEBUG] Generated GRUB hash: $grub_hash"
echo "[✔] GRUB password hash generated."

# Backup and configure /etc/grub.d/40_custom
echo "[+] Updating GRUB config..."
cp /etc/grub.d/40_custom /etc/grub.d/40_custom.bak
cat <<EOF >> /etc/grub.d/40_custom
set superusers="admin"
password_pbkdf2 admin $grub_hash
EOF

# Regenerate GRUB config
echo "[+] Regenerating GRUB configuration..."
if [ -d /sys/firmware/efi ]; then
  grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg || { echo "[X] GRUB configuration failed."; exit 1; }
else
  grub2-mkconfig -o /boot/grub2/grub.cfg || { echo "[X] GRUB configuration failed."; exit 1; }
fi
echo "[✔] GRUB is now protected."


# --- Disable rd.break ---
echo "[+] Disabling rd.break (physical root bypass)..."
cp /etc/default/grub /etc/default/grub.bak
if grep -q "rd.break" /etc/default/grub; then
  sed -i 's/rd.break//g' /etc/default/grub
  grub2-mkconfig -o /boot/grub2/grub.cfg
  echo "[✔] rd.break entry removed."
else
  echo "[✔] rd.break already not present."
fi


# --- Disable root SSH login ---
echo "[+] Disabling SSH root login..."
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
if grep -q "^PermitRootLogin" /etc/ssh/sshd_config; then
  sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
else
  echo "PermitRootLogin no" >> /etc/ssh/sshd_config
fi

if systemctl restart sshd; then
  echo "[✔] SSH service restarted successfully."
else
  echo "[X] Failed to restart SSH service. Check configuration."
  exit 1
fi
echo "[✔] Root login via SSH disabled."


# --- Final Message ---
echo ""
echo "[✅] All security hardening steps applied!"
echo "👉 Reboot your system. At GRUB, you'll be prompted for a password if someone tries to edit entries with 'e'."

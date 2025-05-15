#!/bin/bash

# ----------------------------------------
# System Lockdown Script (GRUB + SSH + rd.break protection)
# ----------------------------------------

# Enable logging for debugging
exec > >(tee -i /var/log/security_hardening_debug.log)
exec 2>&1

# Ensure the script is run with root privileges
if [ "$EUID" -ne 0 ]; then
  echo "[X] This script must be run as root. Please use sudo or run as root."
  exit 1
fi

echo "[+] Starting system lockdown process..."

# --- GRUB Password Setup ---
echo "[+] Setting a GRUB password for added security..."

# Prompt the user to enter and confirm the GRUB password
read -sp "Enter your GRUB password: " grub_password
echo
read -sp "Confirm your GRUB password: " grub_password_confirm
echo

if [ "$grub_password" != "$grub_password_confirm" ]; then
  echo "[X] Passwords do not match. Please run the script again and ensure they match."
  exit 1
fi

# Check if grub2-mkpasswd-pbkdf2 command is available
if ! command -v grub2-mkpasswd-pbkdf2 &> /dev/null; then
  echo "[X] grub2-mkpasswd-pbkdf2 command not found. Please install grub2-tools (RHEL-based) or grub2-common (Debian-based)."
  exit 1
fi

# Generate GRUB password hash
echo "[+] Generating GRUB password hash..."
grub_hash=$(yes "$grub_password" | grub2-mkpasswd-pbkdf2 2>/dev/null | awk '/PBKDF2/ {print $NF}')

if [[ -z "$grub_hash" ]]; then
  echo "[X] Failed to generate GRUB password hash. Please ensure grub2-mkpasswd-pbkdf2 is working."
  exit 1
fi
echo "[✔] GRUB password hash successfully generated."

# Backup and update the GRUB configuration file
echo "[+] Updating GRUB configuration for password protection..."
if [ ! -f /etc/grub.d/40_custom ]; then
  echo "[X] GRUB configuration file /etc/grub.d/40_custom not found. Please ensure GRUB is installed."
  exit 1
fi

# Backup the existing configuration file
cp /etc/grub.d/40_custom /etc/grub.d/40_custom.bak
cat <<EOF > /etc/grub.d/40_custom
set superusers="admin"
password_pbkdf2 admin $grub_hash
EOF
echo "[✔] GRUB configuration file updated successfully."

# Regenerate GRUB configuration
echo "[+] Regenerating GRUB configuration..."
if [ -d /sys/firmware/efi ]; then
  if grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg; then
    echo "[✔] GRUB configuration updated for UEFI system."
  else
    echo "[X] Failed to update GRUB configuration for UEFI system."
    exit 1
  fi
else
  if grub2-mkconfig -o /boot/grub2/grub.cfg; then
    echo "[✔] GRUB configuration updated for BIOS system."
  else
    echo "[X] Failed to update GRUB configuration for BIOS system."
    exit 1
  fi
fi

# --- Disable rd.break ---
echo "[+] Disabling rd.break to prevent physical root bypass..."
if [ ! -f /etc/default/grub ]; then
  echo "[X] GRUB default configuration file /etc/default/grub not found. Please ensure GRUB is installed."
  exit 1
fi

# Backup the GRUB default configuration file
cp /etc/default/grub /etc/default/grub.bak

if grep -q "rd.break" /etc/default/grub; then
  sed -i 's/rd.break//g' /etc/default/grub
  grub2-mkconfig -o /boot/grub2/grub.cfg
  echo "[✔] rd.break entry removed successfully."
else
  echo "[✔] rd.break was not present in the GRUB configuration."
fi

# --- Disable root SSH login ---
echo "[+] Disabling SSH login as root for enhanced security..."
if [ ! -f /etc/ssh/sshd_config ]; then
  echo "[X] SSH configuration file /etc/ssh/sshd_config not found. Please verify that OpenSSH is installed."
  exit 1
fi

# Backup the SSH configuration file
cp /etc/ssh/sshd_config /etc/sshd_config.bak

if grep -q "^PermitRootLogin" /etc/ssh/sshd_config; then
  sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
else
  echo "PermitRootLogin no" >> /etc/ssh/sshd_config
fi

if systemctl restart sshd; then
  echo "[✔] Root login via SSH has been disabled."
else
  echo "[X] Failed to restart the SSH service. Please check the SSH configuration."
  exit 1
fi

# --- Final Message ---
echo ""
echo "[✅] All security hardening steps have been successfully applied!"
echo "👉 Please reboot your system. During boot, GRUB will prompt for a password if someone attempts to edit entries."

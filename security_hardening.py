#!/bin/bash

# ----------------------------------------
# System Lockdown Script (GRUB + SSH + rd.break protection)
# ----------------------------------------

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

# Generate GRUB password hash using expect
echo "[+] Generating password hash..."
grub_hash=$(expect -c "
spawn grub2-mkpasswd-pbkdf2
expect \"Enter password:\"
send \"$grub_password\r\"
expect \"Reenter password:\"
send \"$grub_password\r\"
expect \"PBKDF2 hash of your password is \"
expect \"\n\"
set hash_line \$expect_out(buffer)
regexp {PBKDF2 hash of your password is (.*)} \$hash_line -> hash
puts \$hash
")

# Configure /etc/grub.d/40_custom
echo "[+] Updating GRUB config..."
echo -e "set superusers=\"admin\"\npassword_pbkdf2 admin $grub_hash" > /etc/grub.d/40_custom

# Regenerate GRUB config (UEFI or BIOS)
if [ -d /sys/firmware/efi ]; then
  grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg
else
  grub2-mkconfig -o /boot/grub2/grub.cfg
fi

echo "[✔] GRUB is now protected."


# --- Disable rd.break ---
echo "[+] Disabling rd.break (physical root bypass)..."
grub_default="/etc/default/grub"

if grep -q "rd.break" "$grub_default"; then
  sed -i 's/rd.break//g' "$grub_default"
  grub2-mkconfig -o /boot/grub2/grub.cfg
  echo "[✔] rd.break entry removed."
else
  echo "[✔] rd.break already not present."
fi


# --- Disable root SSH login ---
echo "[+] Disabling SSH root login..."
if grep -q "^PermitRootLogin" /etc/ssh/sshd_config; then
  sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
else
  echo "PermitRootLogin no" >> /etc/ssh/sshd_config
fi

systemctl restart sshd
echo "[✔] Root login via SSH disabled."


# --- Final Message ---
echo "[✅] All security hardening steps applied!"
echo "Reboot your system to see GRUB password prompt."

#!/usr/bin/env python3

import os
import subprocess

def disable_rd_break():
    """Secures GRUB by preventing the rd.break attack."""
    print("[+] Securing GRUB...")
    grub_file = "/etc/default/grub"
    
    try:
        with open(grub_file, "r") as f:
            grub_content = f.read()

        if "rd.break" in grub_content:
            grub_content = grub_content.replace("rd.break", "")
            with open(grub_file, "w") as f:
                f.write(grub_content)

            subprocess.run(["grub2-mkconfig", "-o", "/boot/grub2/grub.cfg"], check=True)
            print("[✔] Removed rd.break and updated GRUB.")
        else:
            print("[✔] rd.break is already removed.")
    except Exception as e:
        print(f"[X] Error securing GRUB: {e}")

def disable_root_login():
    """Disables root login via SSH for security."""
    print("[+] Disabling root login over SSH...")
    sshd_config = "/etc/ssh/sshd_config"
    
    try:
        with open(sshd_config, "r") as f:
            sshd_content = f.read()

        if "PermitRootLogin yes" in sshd_content:
            sshd_content = sshd_content.replace("PermitRootLogin yes", "PermitRootLogin no")
            with open(sshd_config, "w") as f:
                f.write(sshd_content)

            subprocess.run(["systemctl", "restart", "sshd"], check=True)
            print("[✔] Root login disabled over SSH.")
        else:
            print("[✔] Root login already disabled.")
    except Exception as e:
        print(f"[X] Error modifying SSH settings: {e}")

def enforce_strong_passwords():
    """Enforces strong password policies using PAM."""
    print("[+] Enforcing strong password policies...")
    pam_file = "/etc/security/pwquality.conf"
    
    try:
        with open(pam_file, "a") as f:
            f.write("\nminlen=12\nucredit=-1\nlcredit=-1\ndcredit=-1\nocredit=-1\n")

        print("[✔] Strong password policies applied.")
    except Exception as e:
        print(f"[X] Error applying password policies: {e}")

def enable_audit_logging():
    """Configures Auditd to log unauthorized access attempts."""
    print("[+] Configuring Auditd for security monitoring...")
    
    try:
        subprocess.run(["systemctl", "enable", "--now", "auditd"], check=True)
        print("[✔] Auditd enabled and running.")
    except Exception as e:
        print(f"[X] Error enabling Auditd: {e}")

def main():
    """Main function to execute all security hardening steps."""
    disable_rd_break()
    disable_root_login()
    enforce_strong_passwords()
    enable_audit_logging()
    print("\n[✔] Linux system security hardened successfully!")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("[X] Please run this script as root.")
    else:
        main()

#!/usr/bin/env python3
import subprocess
import os
from gi.repository import Gtk
from .base import BaseWindow

class RecoveryWindow(BaseWindow):
    def __init__(self, state_file, state):
        super().__init__(state_file, state, title="Recovery Mode")
        self.add_page("Recovery Options", self.create_options_page())
        self.add_page("System Status", self.create_status_page())
        self.add_page("Repair Issues", self.create_repair_page())
        self.add_page("Filesystem Repair", self.create_fs_repair_page())
        self.add_page("Untrusted Recovery", self.create_untrusted_page())

    def create_options_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Recovery Mode</span>')
        box.pack_start(label, False, False, 0)

        desc = Gtk.Label()
        desc.set_text("Select an action:")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 10)

        self.action_combo = Gtk.ComboBoxText()
        actions = [
            "View system status",
            "Repair detected issues",
            "Fix everything (kernel, initramfs, GRUB, fstab)",
            "Repair filesystem corruption",
            "Scan for rootkits",
            "Untrusted Recovery (rootkit hunt + malware scan)",
            "Full reinstall (run installer)"
        ]
        for a in actions:
            self.action_combo.append_text(a)
        self.action_combo.set_active(0)
        box.pack_start(self.action_combo, False, False, 5)

        return box

    def create_status_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">System Status</span>')
        box.pack_start(label, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(400)

        self.status_text = Gtk.TextView()
        self.status_text.set_editable(False)
        self.status_text.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(self.status_text)
        box.pack_start(scrolled, True, True, 0)

        refresh_btn = Gtk.Button(label="Refresh Status")
        refresh_btn.connect("clicked", self.on_refresh_status)
        box.pack_start(refresh_btn, False, False, 10)

        return box

    def on_refresh_status(self, widget):
        # Run recovery_get_status via Bash and display
        cmd = ["bash", "-c", "source /root/ArtixForge/scripts/recovery/core.sh && recovery_get_status"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            self.status_text.get_buffer().set_text(result.stdout)
        except Exception as e:
            self.status_text.get_buffer().set_text(f"Error fetching status: {e}")

    def create_repair_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Repair Detected Issues</span>')
        box.pack_start(label, False, False, 0)

        desc = Gtk.Label()
        desc.set_text("This will surgically fix only what's broken:\n- fstab UUIDs\n- Pacman locks and missing base\n- Missing kernel/initramfs\n- EFI boot entries\n- cryptdevice parameters\n- encrypt hooks")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 10)

        return box

    def create_fs_repair_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Filesystem Repair</span>')
        box.pack_start(label, False, False, 0)

        desc = Gtk.Label()
        desc.set_text("Select repair approach:")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 10)

        self.fs_method_combo = Gtk.ComboBoxText()
        self.fs_method_combo.append_text("Safe – non-destructive check")
        self.fs_method_combo.append_text("Destructive – aggressive repair (may discard data)")
        self.fs_method_combo.set_active(0)
        box.pack_start(self.fs_method_combo, False, False, 5)

        return box

    def create_untrusted_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Untrusted Recovery</span>')
        box.pack_start(label, False, False, 0)

        desc = Gtk.Label()
        desc.set_markup('<span foreground="red">⚠ DANGEROUS OPERATION ⚠</span>\n\nThis is intended for systems you believe may be compromised.\n\nWhat it will do:\n• Run a rootkit scan (rkhunter)\n• Check for common malware indicators\n• Optionally scan with ClamAV\n\nIt will NOT modify your filesystem or attempt repairs.\nYou run this AT YOUR OWN RISK.')
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_line_wrap(True)
        box.pack_start(desc, False, False, 10)

        self.clamav_check = Gtk.CheckButton(label="Run ClamAV scan (slow, requires ClamAV)")
        self.clamav_check.set_active(False)
        box.pack_start(self.clamav_check, False, False, 5)

        return box

    def start_installation(self):
        # Determine which action to run based on the selected page
        if self.current_page == 0:
            action = self.action_combo.get_active_text()
        elif self.current_page == 2:
            action = "Repair detected issues"
        elif self.current_page == 3:
            action = "Repair filesystem corruption"
        elif self.current_page == 4:
            action = "Untrusted Recovery"
        else:
            action = "View system status"

        # Map action to Bash command
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        script_dir = f"{base_dir}/scripts"

        if action == "View system status":
            cmd = ["bash", "-c", f"source {script_dir}/recovery/core.sh && recovery_get_status"]
            self.run_status_command(cmd)
            return
        elif action == "Repair detected issues":
            cmd = ["bash", "-c", f"source {script_dir}/recovery/repair.sh && repair_detected_issues"]
        elif action == "Fix everything (kernel, initramfs, GRUB, fstab)":
            cmd = ["bash", "-c", f"source {script_dir}/recovery/repair.sh && repair_system"]
        elif action == "Repair filesystem corruption":
            method = "Safe" if self.fs_method_combo.get_active_text().startswith("Safe") else "Destructive"
            # Run filesystem repair (requires unmount)
            cmd = ["bash", "-c", f"""
                source {script_dir}/recovery/repair.sh
                repair_filesystem_interactive() {{
                    local method="{method}"
                    local root_part=$(findmnt -no SOURCE /mnt)
                    local fs_type=$(findmnt -no FSTYPE /mnt)
                    echo "Unmounting /mnt..."
                    umount /mnt
                    case $fs_type in
                        ext4)
                            if [[ "$method" == "Safe" ]]; then
                                fsck.ext4 -p "$root_part"
                            else
                                fsck.ext4 -f -y "$root_part"
                            fi
                            ;;
                        btrfs)
                            if [[ "$method" == "Safe" ]]; then
                                btrfs check "$root_part"
                            else
                                btrfs check --repair "$root_part"
                            fi
                            ;;
                        xfs)
                            if [[ "$method" == "Safe" ]]; then
                                xfs_repair -n "$root_part"
                            else
                                xfs_repair "$root_part"
                            fi
                            ;;
                    esac
                    mount "$root_part" /mnt
                }}
                repair_filesystem_interactive
            """]
        elif action == "Scan for rootkits":
            cmd = ["bash", "-c", f"source {script_dir}/recovery/repair.sh && detect_rootkits"]
        elif action == "Untrusted Recovery (rootkit hunt + malware scan)":
            clamav_flag = "yes" if self.clamav_check.get_active() else "no"
            cmd = ["bash", "-c", f"""
                source {script_dir}/recovery/repair.sh
                untrusted_recovery_with_clamav() {{
                    tui_msg() {{ echo "$2"; read -p "Press Enter..."; }}
                    tui_yesno() {{ return 0; }}
                    if [[ "{clamav_flag}" == "yes" ]]; then
                        # Run untrusted recovery with ClamAV
                        untrusted_recovery
                    else
                        # Run without ClamAV
                        untrusted_recovery
                    fi
                }}
                untrusted_recovery_with_clamav
            """]
        elif action == "Full reinstall (run installer)":
            cmd = ["sudo", "./install"]
            subprocess.Popen(cmd)
            Gtk.main_quit()
            return
        else:
            return

        # Run command with progress window
        from ..backends.gui import ProgressWindow
        progress = ProgressWindow(
            {"title": action, "command": cmd},
            title_color=self.title_color, accent_color=self.accent_color
        )
        progress.run()
        Gtk.main_quit()

    def run_status_command(self, cmd):
        # For status, just show a dialog with output
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            dialog = Gtk.MessageDialog(parent=self.window, flags=Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
                                       message_format=result.stdout)
            dialog.set_title("System Status")
            dialog.run()
            dialog.destroy()
        except Exception as e:
            dialog = Gtk.MessageDialog(parent=self.window, flags=Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
                                       message_format=f"Error: {e}")
            dialog.run()
            dialog.destroy()
        Gtk.main_quit()

    def on_next(self, widget):
        self.start_installation()
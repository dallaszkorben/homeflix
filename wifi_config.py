import tkinter as tk
from tkinter import messagebox, ttk
import os
import shutil
import subprocess
import re
import threading

class WifiConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Raspberry Pi Wi-Fi Configuration")
        self.root.geometry("450x200")

        # Lists to store interfaces and Wi-Fi networks
        self.interfaces = []
        self.wifi_list = []

        # Create frame for form elements
        form_frame = tk.Frame(root, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Interface selection dropdown
        tk.Label(form_frame, text="Interface:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.interface_var = tk.StringVar()
        self.interface_dropdown = ttk.Combobox(form_frame, textvariable=self.interface_var, width=10, state="readonly")
        self.interface_dropdown.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.interface_dropdown.bind("<<ComboboxSelected>>", lambda event: self.interface_changed())

        # Wi-Fi name dropdown
        tk.Label(form_frame, text="Wi-Fi Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.wifi_name = tk.StringVar()
        self.wifi_dropdown = ttk.Combobox(form_frame, textvariable=self.wifi_name, width=28, state="readonly")
        self.wifi_dropdown.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Scan button
        self.scan_button = tk.Button(form_frame, text="Scan", width=5, command=self.scan_networks)
        self.scan_button.grid(row=1, column=2, padx=5, sticky=tk.W)

        # Bind Enter key to move to next field
        self.wifi_dropdown.bind("<Return>", lambda event: self.password_entry.focus_set())

        # Password field
        tk.Label(form_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.password = tk.StringVar()
        self.password_entry = tk.Entry(form_frame, textvariable=self.password, width=30)
        self.password_entry.grid(row=2, column=1, sticky=tk.W, pady=5)

        # Bind Enter key to move to OK button
        self.password_entry.bind("<Return>", lambda event: self.ok_button.focus_set())

        # Hide password checkbox (unchecked by default to show password)
        self.hide_password = tk.BooleanVar(value=False)  # Default is to show password
        self.hide_checkbox = tk.Checkbutton(form_frame, text="Hide", variable=self.hide_password,
                                           command=self.toggle_password_visibility)
        self.hide_checkbox.grid(row=2, column=2, padx=5, sticky=tk.W)

        # Initialize password field visibility
        self.toggle_password_visibility()

        # Button frame
        button_frame = tk.Frame(form_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        # OK button (initially disabled)
        self.ok_button = tk.Button(button_frame, text="OK", width=10, command=self.save_config, state=tk.DISABLED)
        self.ok_button.pack(side=tk.LEFT, padx=10)
        self.ok_button.bind("<Return>", lambda event: self.save_config())

        # Cancel button
        self.cancel_button = tk.Button(button_frame, text="Cancel", width=10, command=self.root.destroy)
        self.cancel_button.pack(side=tk.LEFT, padx=10)
        self.cancel_button.bind("<Return>", lambda event: self.root.destroy())

        # Status label
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(form_frame, textvariable=self.status_var, fg="blue")
        self.status_label.grid(row=4, column=0, columnspan=3, pady=5)

        # Bind events to check if both fields have content
        self.wifi_name.trace("w", self.check_fields)
        self.password.trace("w", self.check_fields)

        # Bind Escape key to close the window
        self.root.bind("<Escape>", lambda event: self.root.destroy())

        # Find available interfaces and start scanning
        self.find_interfaces()

    def interface_changed(self):
        """Handle interface selection change"""
        # Clear the Wi-Fi dropdown
        self.wifi_dropdown.set('')
        self.wifi_dropdown['values'] = []
        self.wifi_list = []

        # Start scanning with the new interface
        self.scan_networks()

    def find_interfaces(self):
        """Find available network interfaces"""
        self.status_var.set("Finding network interfaces...")

        # Start in a separate thread to avoid freezing the UI
        threading.Thread(target=self._find_interfaces_thread, daemon=True).start()

    def _find_interfaces_thread(self):
        """Background thread for finding interfaces"""
        try:
            # Get list of wireless interfaces
            output = subprocess.check_output(["ls", "/sys/class/net"], universal_newlines=True)
            all_interfaces = output.strip().split()

            # Filter for wireless interfaces (typically wlan*)
            self.interfaces = [iface for iface in all_interfaces if
                              os.path.exists(f"/sys/class/net/{iface}/wireless") or
                              iface.startswith("wlan")]

            # Update the dropdown on the main thread
            self.root.after(0, self._update_interface_dropdown)

        except Exception as e:
            # Update status on the main thread
            self.root.after(0, lambda: self.status_var.set(f"Interface detection error: {str(e)}"))

    def _update_interface_dropdown(self):
        """Update the interface dropdown with found interfaces"""
        if not self.interfaces:
            # If no wireless interfaces found, add a default one
            self.interfaces = ["wlan0"]

        self.interface_dropdown['values'] = self.interfaces

        # Try to select wlan0 by default, or the first available interface
        default_interface = "wlan0" if "wlan0" in self.interfaces else self.interfaces[0]
        self.interface_var.set(default_interface)

        self.status_var.set(f"Found {len(self.interfaces)} wireless interfaces")

        # Start scanning with the selected interface
        self.scan_networks()

    def scan_networks(self):
        """Scan for available Wi-Fi networks using selected interface"""
        interface = self.interface_var.get()
        if not interface:
            return

        self.status_var.set(f"Scanning for networks on {interface}...")
        self.scan_button.config(state=tk.DISABLED)

        # Start scanning in a separate thread to avoid freezing the UI
        threading.Thread(target=lambda: self._scan_thread(interface), daemon=True).start()

    def _scan_thread(self, interface):
        """Background thread for network scanning"""
        try:
            # Run iwlist scan on the selected interface
            output = subprocess.check_output(["sudo", "iwlist", interface, "scan"],
                                           universal_newlines=True)

            # Extract networks and their signal levels
            networks_with_signal = []

            # Split the output by "Cell" to process each network separately
            cells = output.split("Cell ")

            for cell in cells[1:]:  # Skip the first element (header)
                essid_match = re.search(r'ESSID:"(.*?)"', cell)
                signal_match = re.search(r'Signal level=(-\d+) dBm', cell)

                if essid_match and signal_match:
                    essid = essid_match.group(1)
                    signal_level = int(signal_match.group(1))
                    networks_with_signal.append((essid, signal_level))

            # Sort networks by signal strength (highest first)
            networks_with_signal.sort(key=lambda x: x[1], reverse=True)

            # Extract just the network names, keeping the sorted order
            self.wifi_list = [network[0] for network in networks_with_signal]

            # Update the dropdown on the main thread
            self.root.after(0, self._update_dropdown)

        except Exception as e:
            # Update status on the main thread
            self.root.after(0, lambda: self.status_var.set(f"Scan error: {str(e)}"))
            self.root.after(0, lambda: self.scan_button.config(state=tk.NORMAL))

    def _update_dropdown(self):
        """Update the dropdown with found networks"""
        self.wifi_dropdown['values'] = self.wifi_list

        if self.wifi_list:
            self.wifi_dropdown.current(0)  # Select the first (strongest) network
            self.status_var.set(f"Found {len(self.wifi_list)} networks")
        else:
            self.status_var.set("No networks found")

        self.scan_button.config(state=tk.NORMAL)

    def toggle_password_visibility(self):
        """Toggle password visibility based on checkbox state"""
        if self.hide_password.get():
            self.password_entry.config(show="*")
        else:
            self.password_entry.config(show="")

    def check_fields(self, *args):
        """Enable OK button only if both fields have content"""
        if self.wifi_name.get() and self.password.get():
            self.ok_button.config(state=tk.NORMAL)
        else:
            self.ok_button.config(state=tk.DISABLED)

    def save_config(self):
        """Display the Wi-Fi configuration in the console"""
        wifi_name = self.wifi_name.get()
        password = self.password.get()

        try:
            # Path to template file
            template_path = "./etc/wpa_supplicant.conf"

            # Read the template file
            with open(template_path, 'r') as file:
                content = file.read()

            # Replace placeholders with user input
            content = content.replace("<wifi_id>", wifi_name)
            content = content.replace("<password>", password)

            # Print the updated content to the console
            print("=== Wi-Fi Configuration ===")
            print(content)
            print("==========================")

            messagebox.showinfo("Success", "Wi-Fi configuration generated successfully!")
            self.root.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate configuration: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WifiConfigApp(root)
    root.mainloop()

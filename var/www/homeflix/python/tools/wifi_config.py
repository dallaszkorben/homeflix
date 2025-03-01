import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import os
import shutil
import subprocess
import re
import threading
import ipaddress  # For IP address validation

class WifiConfigApp:
    def __init__(self, root):

        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Define paths relative to the script location
        self.temp_interface_path = os.path.join(script_dir, 'templates', 'interfaces')
        self.temp_wifi_path = os.path.join(script_dir, 'templates', 'wpa_supplicant.conf')

        self.interface_path = '/etc/network/interfaces'
        self.wifi_path = '/etc/wpa_supplicant/wpa_supplicant-1.conf'

        self.root = root
        self.root.title("Raspberry Pi Wi-Fi Configuration")
        self.root.geometry("650x350")  # Increased width to accommodate wider message boxes

        # Get the default background color of the root window
        bg_color = root.cget("background")

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

        # Bind Enter key to move to IP address field
        self.password_entry.bind("<Return>", lambda event: self.ip_entry.focus_set())

        # Hide password checkbox (unchecked by default to show password)
        self.hide_password = tk.BooleanVar(value=False)  # Default is to show password
        self.hide_checkbox = tk.Checkbutton(form_frame, text="Hide", variable=self.hide_password,
                                           command=self.toggle_password_visibility)
        self.hide_checkbox.grid(row=2, column=2, padx=5, sticky=tk.W)

        # IP Address field with validation
        tk.Label(form_frame, text="IP Address:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.ip_address = tk.StringVar(value="192.168.")  # Default value
        self.ip_entry = tk.Entry(form_frame, textvariable=self.ip_address, width=30)
        self.ip_entry.grid(row=3, column=1, sticky=tk.W, pady=5)

        # Add validation when focus leaves the IP field
        self.ip_entry.bind("<FocusOut>", self.validate_ip_address)

        # Flag to track if IP is valid
        self.ip_valid = False

        # Initialize password field visibility
        self.toggle_password_visibility()

        # Button frame
        button_frame = tk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        # OK button (initially disabled)
        self.ok_button = tk.Button(button_frame, text="OK", width=10, command=self.save_config, state=tk.DISABLED)
        self.ok_button.pack(side=tk.LEFT, padx=10)
        self.ok_button.bind("<Return>", lambda event: self.save_config())

        # Cancel button
        self.cancel_button = tk.Button(button_frame, text="Cancel", width=10, command=self.root.destroy)
        self.cancel_button.pack(side=tk.LEFT, padx=10)
        self.cancel_button.bind("<Return>", lambda event: self.root.destroy())

        # Error message text area (below buttons) - 1.5 times wider
        tk.Label(form_frame, text="Errors:").grid(row=5, column=0, sticky=tk.NW, pady=(10, 0))
        self.error_text = scrolledtext.ScrolledText(form_frame, width=68, height=3,
                                                  wrap=tk.WORD, fg="red", bg=bg_color)
        self.error_text.grid(row=5, column=1, columnspan=2, sticky=tk.W+tk.E, pady=(10, 0))
        self.error_text.config(state=tk.DISABLED)  # Make it read-only

        # Status message text area (below error area) - 1.5 times wider
        tk.Label(form_frame, text="Messages:").grid(row=6, column=0, sticky=tk.NW, pady=(5, 0))
        self.message_text = scrolledtext.ScrolledText(form_frame, width=68, height=3,
                                                    wrap=tk.WORD, fg="blue", bg=bg_color)
        self.message_text.grid(row=6, column=1, columnspan=2, sticky=tk.W+tk.E, pady=(5, 0))
        self.message_text.config(state=tk.DISABLED)  # Make it read-only

        # Bind events to check if all fields have content and IP is valid
        self.wifi_name.trace("w", self.check_fields)
        self.password.trace("w", self.check_fields)
        self.ip_address.trace("w", self.validate_ip_on_change)

        # Bind Escape key to close the window
        self.root.bind("<Escape>", lambda event: self.root.destroy())

        # Find available interfaces and start scanning
        self.find_interfaces()

    def validate_ip_on_change(self, *args):
        """Validate IP address whenever it changes (but don't show errors)"""
        ip = self.ip_address.get()

        # Check if IP is valid
        try:
            # Try to create an IPv4Address object to validate
            ipaddress.IPv4Address(ip)
            self.ip_valid = True
        except ValueError:
            # If not a valid IP, check if it's a partial IP (like "192.168.")
            if re.match(r'^(\d{1,3}\.){1,3}$', ip):
                # It's a partial IP, which is fine while typing
                self.ip_valid = False
            else:
                # Invalid IP format, but don't show error yet
                self.ip_valid = False

        # Update OK button state
        self.check_fields()

    def validate_ip_address(self, event=None):
        """Validate the IP address when focus leaves the field"""
        ip = self.ip_address.get()

        # Clear any previous IP-related error messages
        self.clear_specific_error_messages("IP address")

        # Check if IP is valid
        try:
            # Try to create an IPv4Address object to validate
            ipaddress.IPv4Address(ip)
            self.ip_valid = True
            self.check_fields()
            return True
        except ValueError:
            # If not a valid IP, check if it's a partial IP (like "192.168.")
            if re.match(r'^(\d{1,3}\.){1,3}$', ip):
                # It's a partial IP, which is fine while typing
                self.ip_valid = False
                self.check_fields()
                return False
            else:
                # Invalid IP format - show error message now that focus has left
                error_msg = f"Invalid IP address format: {ip}"
                self.add_error_message(error_msg)
                self.ip_valid = False
                self.check_fields()
                return False

    def clear_specific_error_messages(self, keyword):
        """Clear error messages containing a specific keyword"""
        self.error_text.config(state=tk.NORMAL)

        # Get all lines
        lines = self.error_text.get(1.0, tk.END).split('\n')

        # Filter out lines containing the keyword
        filtered_lines = [line for line in lines if keyword not in line]

        # Clear and reinsert filtered content
        self.error_text.delete(1.0, tk.END)
        self.error_text.insert(tk.END, '\n'.join(filtered_lines))

        self.error_text.config(state=tk.DISABLED)

    def add_error_message(self, message):
        """Add an error message to the error text area"""
        self.error_text.config(state=tk.NORMAL)  # Enable editing
        self.error_text.insert(tk.END, message + "\n")
        self.error_text.see(tk.END)  # Scroll to the end
        self.error_text.config(state=tk.DISABLED)  # Disable editing again

    def clear_error_messages(self):
        """Clear all error messages"""
        self.error_text.config(state=tk.NORMAL)
        self.error_text.delete(1.0, tk.END)
        self.error_text.config(state=tk.DISABLED)

    def add_status_message(self, message):
        """Add a status message to the message text area"""
        self.message_text.config(state=tk.NORMAL)  # Enable editing
        self.message_text.insert(tk.END, message + "\n")
        self.message_text.see(tk.END)  # Scroll to the end
        self.message_text.config(state=tk.DISABLED)  # Disable editing again

    def clear_status_messages(self):
        """Clear all status messages"""
        self.message_text.config(state=tk.NORMAL)
        self.message_text.delete(1.0, tk.END)
        self.message_text.config(state=tk.DISABLED)

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
        status_msg = "Finding network interfaces..."
        self.add_status_message(status_msg)

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
            error_msg = f"Interface detection error: {str(e)}"
            # Update error message on the main thread
            self.root.after(0, lambda: self.add_error_message(error_msg))

    def _update_interface_dropdown(self):
        """Update the interface dropdown with found interfaces"""
        if not self.interfaces:
            # If no wireless interfaces found, add a default one
            self.interfaces = ["wlan0"]
            self.add_error_message("No wireless interfaces found. Using default 'wlan0'.")

        self.interface_dropdown['values'] = self.interfaces

        # Try to select wlan0 by default, or the first available interface
        default_interface = "wlan0" if "wlan0" in self.interfaces else self.interfaces[0]
        self.interface_var.set(default_interface)

        status_msg = f"Found {len(self.interfaces)} wireless interfaces"
        self.add_status_message(status_msg)

        # Start scanning with the selected interface
        self.scan_networks()

    def scan_networks(self):
        """Scan for available Wi-Fi networks using selected interface"""
        interface = self.interface_var.get()
        if not interface:
            return

        status_msg = f"Scanning for networks on {interface}..."
        self.add_status_message(status_msg)
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

                    # Skip empty or null-filled SSIDs
                    if not essid or '\\x00' in essid:
                        continue

                    signal_level = int(signal_match.group(1))
                    networks_with_signal.append((essid, signal_level))

            # Sort networks by signal strength (highest first)
            networks_with_signal.sort(key=lambda x: x[1], reverse=True)

            # Extract just the network names, keeping the sorted order
            self.wifi_list = [network[0] for network in networks_with_signal]

            # Update the dropdown on the main thread
            self.root.after(0, self._update_dropdown)

        except Exception as e:
            error_msg = f"Scan error: {str(e)}"
            # Update error message on the main thread
            self.root.after(0, lambda: self.add_error_message(error_msg))
            self.root.after(0, lambda: self.scan_button.config(state=tk.NORMAL))

    def _update_dropdown(self):
        """Update the dropdown with found networks"""
        self.wifi_dropdown['values'] = self.wifi_list

        if self.wifi_list:
            self.wifi_dropdown.current(0)  # Select the first (strongest) network
            status_msg = f"Found {len(self.wifi_list)} networks"
            self.add_status_message(status_msg)
        else:
            error_msg = "No networks found"
            self.add_error_message(error_msg)

        self.scan_button.config(state=tk.NORMAL)

    def toggle_password_visibility(self):
        """Toggle password visibility based on checkbox state"""
        if self.hide_password.get():
            self.password_entry.config(show="*")
        else:
            self.password_entry.config(show="")

    def check_fields(self, *args):
        """Enable OK button only if all fields have content and IP is valid"""
        if (self.wifi_name.get() and
            self.password.get() and
            self.ip_address.get() and
            self.ip_valid):
            self.ok_button.config(state=tk.NORMAL)
        else:
            self.ok_button.config(state=tk.DISABLED)

    def save_config(self):
        """Save the Wi-Fi configuration to the specified file"""
        wifi_name = self.wifi_name.get()
        password = self.password.get()
        ip_address = self.ip_address.get()

        # Temporarily disable the OK button during processing
        self.ok_button.config(state=tk.DISABLED)

        success = True
        wifi_success = False
        interface_success = False

        try:
            # Read the template wifi_file
            with open(self.temp_wifi_path, 'r') as file:
                wifi_content = file.read()

            # Replace placeholders with user input
            wifi_content = wifi_content.replace("<wifi_id>", wifi_name)
            wifi_content = wifi_content.replace("<password>", password)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.wifi_path), exist_ok=True)

            # Write the configuration to the file
            with open(self.wifi_path, 'w') as file:
                file.write(wifi_content)

            wifi_success = True
            status_msg = f"Wi-Fi configuration saved to {self.wifi_path}"
            self.add_status_message(status_msg)

        except Exception as e:
            error_msg = f"Failed to save Wi-Fi configuration: {str(e)}"
            self.add_error_message(error_msg)
            success = False

        try:
            # Read and update the interface template
            with open(self.temp_interface_path, 'r') as file:
                interface_content = file.read()

            # Replace IP address placeholder with user input
            interface_content = interface_content.replace("<address>", ip_address)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.interface_path), exist_ok=True)

            # Write the interface configuration
            with open(self.interface_path, 'w') as file:
                file.write(interface_content)

            interface_success = True
            status_msg = f"Network interface configuration saved to {self.interface_path}"
            self.add_status_message(status_msg)

        except Exception as e:
            error_msg = f"Failed to save interface configuration: {str(e)}"
            self.add_error_message(error_msg)
            success = False

        # Final status message
        if success:
            self.add_status_message("Configuration completed successfully!")
        else:
            if wifi_success:
                self.add_status_message("Wi-Fi configuration was successful, but interface configuration failed.")
            elif interface_success:
                self.add_error_message("Interface configuration was successful, but Wi-Fi configuration failed.")
            else:
                self.add_error_message("Configuration failed completely.")

        # Re-enable the OK button
        self.ok_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = WifiConfigApp(root)
    root.mainloop()

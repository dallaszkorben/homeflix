#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango
import os
import subprocess
import re
import threading
import ipaddress
import time
import requests
import json
from datetime import datetime, timedelta
from enum import Enum
from contextlib import contextmanager
import tempfile

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"

class WifiConfigError(Exception):
    """Base exception for WiFi configuration errors"""
    pass

class ScanError(WifiConfigError):
    """Network scanning related errors"""
    pass

class ConnectionError(WifiConfigError):
    """Connection related errors"""
    pass

class MessageManager:
    def __init__(self, error_buffer, message_buffer):
        self.error_buffer = error_buffer
        self.message_buffer = message_buffer
        self.message_tags = {
            'error': error_buffer.create_tag("error", foreground="red"),
            'info': message_buffer.create_tag("message", foreground="blue"),
            'success': message_buffer.create_tag("success",
                                              foreground="green",
                                              weight=Pango.Weight.BOLD)
        }

    def add_message(self, message, message_type='info'):
        """Add a message with specified type"""
        buffer = self.error_buffer if message_type == 'error' else self.message_buffer
        end_iter = buffer.get_end_iter()
        buffer.insert_with_tags_by_name(end_iter, f"{message}\n", message_type)
        self._scroll_to_end(buffer)

    def clear_messages(self, message_type=None):
        """Clear messages of specified type or all if type is None"""
        if message_type == 'error' or message_type is None:
            self.error_buffer.set_text("")
        if message_type == 'info' or message_type is None:
            self.message_buffer.set_text("")

    def _scroll_to_end(self, buffer):
        """Scroll the buffer to the end"""
        mark = buffer.create_mark("end", buffer.get_end_iter(), False)
        text_view = self.error_text if buffer == self.error_buffer else self.message_text
        text_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

class NetworkScanner:
    def __init__(self, interface, timeout=15):
        self.interface = interface
        self.timeout = timeout

    async def scan(self):
        """Perform network scan"""
        try:
            # Bring up interface
            await self._bring_up_interface()

            # Perform scan
            start_time = datetime.now()
            while (datetime.now() - start_time) < timedelta(seconds=self.timeout):
                try:
                    result = await self._do_scan()
                    return self._parse_scan_results(result)
                except subprocess.CalledProcessError:
                    await asyncio.sleep(1)

            raise ScanError("Scan timeout")

        except Exception as e:
            raise ScanError(f"Scan failed: {str(e)}")

    async def _bring_up_interface(self):
        """Bring up the network interface"""
        try:
            subprocess.run(
                ["sudo", "ifconfig", self.interface, "up"],
                check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            raise ScanError(f"Failed to bring up interface: {e.stderr}")

    async def _do_scan(self):
        """Execute the network scan"""
        result = subprocess.run(
            ["sudo", "iwlist", self.interface, "scan"],
            capture_output=True, text=True, check=True
        )
        return result.stdout

    def _parse_scan_results(self, scan_output):
        """Parse scan results and return sorted networks"""
        networks = []
        for cell in scan_output.split("Cell ")[1:]:
            essid_match = re.search(r'ESSID:"(.*?)"', cell)
            signal_match = re.search(r'Signal level=(-\d+) dBm', cell)

            if essid_match and signal_match:
                essid = essid_match.group(1)
                if essid and '\\x00' not in essid:
                    signal_level = int(signal_match.group(1))
                    networks.append((essid, signal_level))

        return sorted(networks, key=lambda x: x[1], reverse=True)

class ConfigManager:
    def __init__(self, wifi_path, interface_path):
        self.wifi_path = wifi_path
        self.interface_path = interface_path

    def read_configs(self):
        """Read current configurations"""
        wifi_config = self._read_wifi_config()
        interface_config = self._read_interface_config()
        return wifi_config, interface_config

    def save_configs(self, wifi_config, interface_config):
        """Save both configurations atomically"""
        temp_files = {}
        try:
            # Create temporary files
            temp_files['wifi'] = self._create_temp_file(wifi_config)
            temp_files['interface'] = self._create_temp_file(interface_config)

            # Move files to final locations
            self._move_config_file(temp_files['wifi'], self.wifi_path)
            self._move_config_file(temp_files['interface'], self.interface_path)

            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            # Cleanup
            for temp_file in temp_files.values():
                try:
                    os.unlink(temp_file)
                except:
                    pass

class WifiConfigApp:
    # Class constants
    INTERFACE_PATH = '/etc/network/interfaces'
    WIFI_PATH = '/etc/wpa_supplicant/wpa_supplicant.conf'
    SCAN_TIMEOUT = 15
    CONNECTION_TIMEOUT = 20
    DEFAULT_IP_SEGMENT = "200"
    HEALTH_CHECK_ENDPOINT = "/health"

    def __init__(self):
        self.setup_window()
        self.setup_managers()
        self.setup_ui()
        self.initialize_state()

    def setup_managers(self):
        """Initialize managers for different functionalities"""
        self.message_manager = MessageManager(self.error_buffer, self.message_buffer)
        self.config_manager = ConfigManager(self.WIFI_PATH, self.INTERFACE_PATH)
        self.connection_state = ConnectionState.DISCONNECTED
        self.preferred_ip_segment = self.DEFAULT_IP_SEGMENT

    def setup_window(self):
        """Setup main window"""
        self.window = Gtk.Window(title="WiFi Configuration")
        self.window.set_border_width(10)
        self.window.connect("delete-event", Gtk.main_quit)

        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(self.main_box)

    def setup_ui(self):
        """Setup UI elements"""
        self.create_form_grid()
        self.create_button_box()
        self.create_message_area()
        self.window.show_all()

    def create_form_grid(self):
        """Create and setup the form grid"""
        form_grid = Gtk.Grid()
        form_grid.set_column_spacing(10)
        form_grid.set_row_spacing(10)
        self.main_box.pack_start(form_grid, False, False, 0)

        # Interface selection
        self.setup_interface_selection(form_grid)

        # WiFi selection
        self.setup_wifi_selection(form_grid)

        # Password field
        self.setup_password_field(form_grid)

        # IP Address field
        self.setup_ip_field(form_grid)

    def setup_interface_selection(self, grid):
        """Setup network interface selection"""
        interface_label = Gtk.Label(label="Interface:")
        interface_label.set_halign(Gtk.Align.START)
        grid.attach(interface_label, 0, 0, 1, 1)

        self.interface_combo = Gtk.ComboBoxText()
        grid.attach(self.interface_combo, 1, 0, 1, 1)
        self.interface_combo.connect("changed", self.on_interface_changed)

        self.scan_button = Gtk.Button(label="Scan")
        self.scan_button.connect("clicked", self.on_scan_clicked)
        grid.attach(self.scan_button, 2, 0, 1, 1)

    def setup_wifi_selection(self, grid):
        """Setup WiFi network selection"""
        wifi_label = Gtk.Label(label="WiFi Network:")
        wifi_label.set_halign(Gtk.Align.START)
        grid.attach(wifi_label, 0, 1, 1, 1)

        self.wifi_combo = Gtk.ComboBoxText()
        self.wifi_combo.connect("changed", self.on_wifi_changed)
        grid.attach(self.wifi_combo, 1, 1, 1, 1)

    def setup_password_field(self, grid):
        """Setup password field with visibility toggle"""
        password_label = Gtk.Label(label="Password:")
        password_label.set_halign(Gtk.Align.START)
        grid.attach(password_label, 0, 2, 1, 1)

        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.connect("key-press-event", self.on_password_key_press)
        self.password_entry.connect("focus-out-event", self.on_password_focus_out)
        grid.attach(self.password_entry, 1, 2, 1, 1)

        self.hide_password = Gtk.CheckButton(label="Hide")
        self.hide_password.connect("toggled", self.on_password_visibility_toggled)
        self.hide_password.set_active(True)
        grid.attach(self.hide_password, 2, 2, 1, 1)

    def setup_ip_field(self, grid):
        """Setup IP address field"""
        ip_label = Gtk.Label(label="IP Address:")
        ip_label.set_halign(Gtk.Align.START)
        grid.attach(ip_label, 0, 3, 1, 1)

        self.ip_entry = Gtk.Entry()
        self.ip_entry.set_width_chars(30)
        self.ip_entry.set_sensitive(False)
        self.ip_entry.connect("changed", self.on_ip_changed)
        self.ip_entry.connect("focus-out-event", self.on_ip_focus_out)
        grid.attach(self.ip_entry, 1, 3, 1, 1)

    def create_button_box(self):
        """Create and setup button box"""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(10)
        self.main_box.pack_start(button_box, False, False, 0)

        self.ok_button = Gtk.Button(label="OK")
        self.ok_button.connect("clicked", self.on_ok_clicked)
        self.ok_button.set_sensitive(False)
        button_box.pack_start(self.ok_button, False, False, 0)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", Gtk.main_quit)
        button_box.pack_start(cancel_button, False, False, 0)

    def create_message_area(self):
        """Create message and error display areas"""
        text_grid = Gtk.Grid()
        text_grid.set_column_spacing(10)
        text_grid.set_row_spacing(10)
        self.main_box.pack_start(text_grid, True, True, 0)

        # Error area
        self.setup_error_area(text_grid)

        # Message area
        self.setup_message_area(text_grid)

    def initialize_state(self):
        """Initialize application state"""
        self.ip_valid = False
        self.connection_successful = False
        self.wifi_list = []
        self._block_interface_changed = False
        self.find_interfaces()

    # Event Handlers
    def on_interface_changed(self, combo):
        """Handle interface selection change"""
        if self._block_interface_changed:
            return

        self.reset_connection_state()
        self.scan_networks()

    def on_wifi_changed(self, combo):
        """Handle WiFi selection change"""
        self.reset_connection_state()
        self.check_fields()

    def on_password_focus_out(self, widget, event):
        """Handle password field focus loss"""
        return self.test_wifi_connection()

    def on_ip_changed(self, widget):
        """Handle IP address changes"""
        self.validate_ip_address(immediate=False)

    def on_ip_focus_out(self, widget, event):
        """Handle IP field focus loss"""
        return self.validate_ip_address(immediate=True)

    def reset_connection_state(self):
        """Reset connection-related state"""
        self.ip_entry.set_text("")
        self.ip_entry.set_sensitive(False)
        self.connection_successful = False
        self.ip_valid = False
        self.check_fields()

    # Network Operations
    def scan_networks(self):
        """Initiate network scan"""
        interface = self.interface_combo.get_active_text()
        if not interface:
            return

        self.message_manager.clear_messages()
        self.message_manager.add_message(f"Scanning for networks on {interface}...")
        self.set_ui_state(False)

        threading.Thread(target=self._scan_thread, args=(interface,), daemon=True).start()

    def _scan_thread(self, interface):
        """Background thread for network scanning"""
        scanner = NetworkScanner(interface, timeout=self.SCAN_TIMEOUT)
        try:
            networks = scanner.scan()
            GLib.idle_add(self._update_network_list, networks)
        except ScanError as e:
            GLib.idle_add(lambda: self.message_manager.add_message(str(e), 'error'))
        finally:
            GLib.idle_add(self.set_ui_state, True)

    def _update_network_list(self, networks):
        """Update network dropdown with scan results"""
        self.wifi_combo.remove_all()
        self.wifi_list = [network[0] for network in networks]  # Extract SSIDs

        if self.wifi_list:
            for network in self.wifi_list:
                self.wifi_combo.append_text(network)

            # Try to select previously configured network
            configured_network = self.get_configured_wifi_settings()[0]
            if configured_network in self.wifi_list:
                self.wifi_combo.set_active(self.wifi_list.index(configured_network))
            else:
                self.wifi_combo.set_active(0)

            self.message_manager.add_message(f"Found {len(self.wifi_list)} networks")
        else:
            self.message_manager.add_message("No networks found", 'error')

    def test_wifi_connection(self):
        """Test connection to selected WiFi network"""
        wifi_name = self.wifi_combo.get_active_text()
        password = self.password_entry.get_text()
        interface = self.interface_combo.get_active_text()

        if not all([wifi_name, password, interface]):
            self.reset_connection_state()
            return False

        self.message_manager.clear_messages()
        self.message_manager.add_message(f"Testing connection to {wifi_name}...")
        self.set_ui_state(False)

        threading.Thread(
            target=self._test_connection_thread,
            args=(wifi_name, password, interface),
            daemon=True
        ).start()
        return True

    def _test_connection_thread(self, wifi_name, password, interface):
        """Background thread for testing WiFi connection"""
        try:
            with WifiTester(interface) as tester:
                success, ip_range = tester.test_connection(wifi_name, password)
                GLib.idle_add(self._handle_connection_result, success, ip_range)
        except ConnectionError as e:
            GLib.idle_add(lambda: self.message_manager.add_message(str(e), 'error'))
        finally:
            GLib.idle_add(self.set_ui_state, True)

    def _handle_connection_result(self, success, ip_range):
        """Handle the result of connection test"""
        self.connection_successful = success
        if success:
            self.message_manager.add_message("WiFi credentials are valid!", 'success')
            self.ip_entry.set_sensitive(True)
            if ip_range:
                suggested_ip = f"{ip_range}.{self.DEFAULT_IP_SEGMENT}"
                self.ip_entry.set_text(suggested_ip)
        else:
            self.reset_connection_state()
            self.message_manager.add_message("Connection test failed", 'error')

        self.check_fields()

    # Configuration Management
    def save_config(self):
        """Save WiFi and network configuration"""
        wifi_name = self.wifi_combo.get_active_text()
        password = self.password_entry.get_text()
        ip_address = self.ip_entry.get_text()
        interface = self.interface_combo.get_active_text()

        self.set_ui_state(False)
        self.message_manager.clear_messages()

        try:
            # Prepare configurations
            wifi_config = self._prepare_wifi_config(wifi_name, password)
            interface_config = self._prepare_interface_config(interface, ip_address)

            # Save configurations
            success, error = self.config_manager.save_configs(wifi_config, interface_config)

            if success:
                self._apply_network_changes(interface)
            else:
                raise ConfigError(f"Failed to save configurations: {error}")

        except Exception as e:
            self.message_manager.add_message(str(e), 'error')
        finally:
            self.set_ui_state(True)

    def _apply_network_changes(self, interface):
        """Apply network changes and verify connection"""
        try:
            # Restart network interface
            self.message_manager.add_message("Applying network changes...")
            self._restart_network_interface(interface)

            # Verify connection
            if self._verify_connection():
                self.message_manager.add_message(
                    "Configuration completed successfully", 'success')
            else:
                raise ConnectionError("Failed to verify connection after configuration")

        except Exception as e:
            self.message_manager.add_message(str(e), 'error')

    # Utility Methods
    def set_ui_state(self, enabled=True):
        """Set UI elements state"""
        elements = [
            self.interface_combo,
            self.wifi_combo,
            self.password_entry,
            self.scan_button,
            self.hide_password
        ]

        for element in elements:
            element.set_sensitive(enabled)

        # Special handling for OK button and IP field
        if enabled:
            self.check_fields()
        else:
            self.ok_button.set_sensitive(False)

    def check_fields(self):
        """Validate fields and update OK button state"""
        conditions = [
            self.wifi_combo.get_active() != -1,
            bool(self.password_entry.get_text()),
            bool(self.ip_entry.get_text()),
            self.ip_valid,
            self.ip_entry.get_sensitive()
        ]

        self.ok_button.set_sensitive(all(conditions))

    def validate_ip_address(self, immediate=True):
        """Validate IP address format"""
        ip_text = self.ip_entry.get_text()

        try:
            # Allow partial input if not immediate validation
            if not immediate and re.match(r'^(\d{1,3}\.){0,3}\d{0,3}$', ip_text):
                return True

            ip = ipaddress.IPv4Address(ip_text)
            self.ip_valid = not (ip.is_loopback or ip.is_multicast)

            if not self.ip_valid and immediate:
                self.message_manager.add_message("Invalid IP address", 'error')

        except ValueError:
            self.ip_valid = False
            if immediate:
                self.message_manager.add_message(f"Invalid IP format: {ip_text}", 'error')

        self.check_fields()
        return self.ip_valid

    @staticmethod
    def _verify_connection():
        """Verify network connection"""
        max_attempts = 3
        delay = 2

        for attempt in range(max_attempts):
            try:
                # Ping gateway or other verification method
                subprocess.run(
                    ["ping", "-c", "1", "-W", "2", "8.8.8.8"],
                    check=True, capture_output=True
                )
                return True
            except subprocess.CalledProcessError:
                if attempt < max_attempts - 1:
                    time.sleep(delay)

        return False

if __name__ == "__main__":
    app = WifiConfigApp()
    Gtk.main()

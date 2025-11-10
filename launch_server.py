import customtkinter as ctk
from customtkinter import filedialog
import subprocess
import threading
import os
import sys
import zipfile
import shutil
import json
import re
import time
import requests
import psutil
from PIL import Image
from datetime import datetime, timedelta

CONFIG_FILE = "config.json"

# --- A Helper Function to Center Windows ---
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth(); screen_height = window.winfo_screenheight()
    x = (screen_width / 2) - (width / 2); y = (screen_height / 2) - (height / 2)
    window.geometry(f'{width}x{height}+{int(x)}+{int(y)}')

# --- A Simple, Reusable Message Box ---
class MessageBox(ctk.CTkToplevel):
    def __init__(self, master, title, message):
        super().__init__(master); self.title(title); self.transient(master); self.grab_set(); center_window(self, 400, 150)
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1)
        ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=14), wraplength=350).grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        ctk.CTkButton(self, text="OK", command=self.destroy, width=100).grid(row=1, column=0, padx=20, pady=(0,20))
        self.after(250, self.focus)

# --- First-Time Setup Window ---
class SetupWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master); self.title("First-Time Setup"); self.transient(master); self.grab_set(); self.backup_path = ""; self.jar_file = ""
        center_window(self, 550, 500)
        self.main_frame = ctk.CTkFrame(self); self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        welcome_label = ctk.CTkLabel(self.main_frame, text="Welcome to PyLaunch MC!", font=ctk.CTkFont(size=20, weight="bold")); welcome_label.pack(pady=(0, 15))
        info_label = ctk.CTkLabel(self.main_frame, text="Let's configure your launcher. These settings will be saved to config.json.", wraplength=480); info_label.pack(pady=(0, 20))
        jar_frame = ctk.CTkFrame(self.main_frame); jar_frame.pack(fill="x", pady=(0, 20)); jar_label = ctk.CTkLabel(jar_frame, text="1. Select Your Server JAR File", font=ctk.CTkFont(weight="bold")); jar_label.pack(anchor="w", padx=10, pady=(5,5))
        self.select_jar_button = ctk.CTkButton(jar_frame, text="Select JAR File...", command=self.select_jar); self.select_jar_button.pack(anchor="w", padx=10, pady=5); self.selected_jar_label = ctk.CTkLabel(jar_frame, text="No file selected. This is required.", text_color="gray60"); self.selected_jar_label.pack(anchor="w", padx=10, pady=(0, 10))
        backup_frame = ctk.CTkFrame(self.main_frame); backup_frame.pack(fill="x"); backup_label = ctk.CTkLabel(backup_frame, text="2. Configure Backups (Optional)", font=ctk.CTkFont(weight="bold")); backup_label.pack(anchor="w", padx=10, pady=(5,5))
        self.backup_checkbox = ctk.CTkCheckBox(backup_frame, text="Enable World Backups to a Cloud-Synced Folder?", command=self.toggle_backup_options); self.backup_checkbox.pack(anchor="w", pady=(5,5), padx=10); self.select_folder_button = ctk.CTkButton(backup_frame, text="Select Backup Sync Folder...", command=self.select_folder); self.select_folder_button.pack(anchor="w", padx=10, pady=5); self.selected_path_label = ctk.CTkLabel(backup_frame, text="Backups are disabled.", text_color="gray60", wraplength=450); self.selected_path_label.pack(anchor="w", padx=10, pady=(0, 10))
        save_button = ctk.CTkButton(self, text="Save and Continue", command=self.save_config); save_button.pack(side="bottom", pady=(0, 20)); self.toggle_backup_options()
    def select_jar(self):
        file_path = filedialog.askopenfilename(title="Select your server JAR file", initialdir=os.getcwd(), filetypes=[("JAR files", "*.jar")]);
        if file_path: self.jar_file = os.path.basename(file_path); self.selected_jar_label.configure(text=f"Selected: {self.jar_file}", text_color="gray90")
    def toggle_backup_options(self):
        if self.backup_checkbox.get() == 1: self.select_folder_button.configure(state="normal"); self.selected_path_label.configure(text=self.backup_path if self.backup_path else "No folder selected.")
        else: self.select_folder_button.configure(state="disabled"); self.selected_path_label.configure(text="Backups are disabled.")
    def select_folder(self):
        path = filedialog.askdirectory(title="Select your Google Drive (or other cloud) backup folder");
        if path: self.backup_path = path; self.selected_path_label.configure(text=f"Path: {self.backup_path}")
    def save_config(self):
        error = False
        if not self.jar_file: self.selected_jar_label.configure(text="Please select a server JAR file before saving!", text_color="#E57373"); error = True
        if self.backup_checkbox.get() == 1 and not self.backup_path: self.selected_path_label.configure(text="Please select a backup folder before saving!", text_color="#E57373"); error = True
        if error: return
        config_data = {"setup_complete": True, "world_name": "world", "jar_file": self.jar_file, "java_args": "-Xmx2G -Xms1G", "backups_enabled": bool(self.backup_checkbox.get()), "gdrive_sync_path": self.backup_path, "autostop_enabled": False, "autostop_minutes": 15, "properties_path": "server.properties"}
        with open(CONFIG_FILE, 'w') as f: json.dump(config_data, f, indent=4)
        self.destroy()

# --- Settings Window Class ---
class SettingsWindow(ctk.CTkToplevel):
    PROPERTY_INFO = {"motd": {"desc": "The 'message of the day' displayed in the server list.", "cat": "General"}, "server-port": {"desc": "The network port the server listens on. Default is 25565.", "cat": "General"}, "view-distance": {"desc": "Sets the server-side render distance in chunks (3-32).", "cat": "General"}, "simulation-distance": {"desc": "Distance in chunks that the server will tick entities (3-32).", "cat": "General"}, "gamemode": {"desc": "Default game mode for new players (survival, creative, etc.).", "cat": "World"}, "difficulty": {"desc": "Defines the game difficulty (peaceful, easy, normal, hard).", "cat": "World"}, "level-name": {"desc": "The name of your primary world folder.", "cat": "World"}, "level-seed": {"desc": "The seed used to generate the world. Leave blank for random.", "cat": "World"}, "generate-structures": {"desc": "Defines if structures like villages and temples generate.", "cat": "World", "type": "boolean"}, "hardcore": {"desc": "If true, players who die are set to Spectator mode.", "cat": "World", "type": "boolean"}, "allow-nether": {"desc": "Allows players to travel to the Nether dimension.", "cat": "World", "type": "boolean"}, "max-world-size": {"desc": "Maximum radius of the world border in blocks.", "cat": "World"}, "max-players": {"desc": "The maximum number of players that can join the server.", "cat": "Player"}, "pvp": {"desc": "Enable or disable Player vs. Player combat.", "cat": "Player", "type": "boolean"}, "online-mode": {"desc": "Recommended 'true'. Set to 'false' only for offline/cracked servers.", "cat": "Player", "type": "boolean"}, "white-list": {"desc": "If true, only players on the whitelist can join.", "cat": "Player", "type": "boolean"}, "allow-flight": {"desc": "Allows players to use flight (e.g., in Creative/Spectator).", "cat": "Player", "type": "boolean"}, "spawn-protection": {"desc": "Radius of blocks around spawn protected from non-OP players.", "cat": "Player"}, "spawn-animals": {"desc": "Determines if friendly animals can spawn naturally.", "cat": "Advanced", "type": "boolean"}, "spawn-monsters": {"desc": "Determines if hostile monsters can spawn naturally.", "cat": "Advanced", "type": "boolean"}, "spawn-npcs": {"desc": "Determines if villagers can spawn in villages.", "cat": "Advanced", "type": "boolean"}, "enable-command-block": {"desc": "Enables the use of command blocks.", "cat": "Advanced", "type": "boolean"}, "op-permission-level": {"desc": "Sets the permission level for server operators (1-4).", "cat": "Advanced"}, "enable-query": {"desc": "Enables the GameSpy4 protocol server listener.", "cat": "Advanced", "type": "boolean"}, "resource-pack": {"desc": "URL to a server-side resource pack.", "cat": "Advanced"}, "resource-pack-sha1": {"desc": "SHA-1 hash of the resource pack to verify its integrity.", "cat": "Advanced"},}
    def __init__(self, master, properties_path):
        super().__init__(master); self.title("Server Properties Editor"); self.master = master; self.properties_path = properties_path; self.entries = {}
        center_window(self, 700, 550); self.rowconfigure(0, weight=1); self.columnconfigure(0, weight=1)
        self.tab_view = ctk.CTkTabview(self); self.tab_frames = {"General": ctk.CTkScrollableFrame(self.tab_view.add("General")), "World": ctk.CTkScrollableFrame(self.tab_view.add("World")), "Player": ctk.CTkScrollableFrame(self.tab_view.add("Player")), "Advanced": ctk.CTkScrollableFrame(self.tab_view.add("Advanced")), "Miscellaneous": ctk.CTkScrollableFrame(self.tab_view.add("Miscellaneous"))}
        for frame in self.tab_frames.values(): frame.pack(expand=True, fill="both"); frame.grid_columnconfigure(1, weight=1)
        self.locate_frame = ctk.CTkFrame(self); self.save_button = ctk.CTkButton(self, text="Save and Close", command=self.save_and_close)
        self.load_properties()
    def _show_locate_ui(self):
        self.tab_view.grid_remove(); self.save_button.grid_remove(); self.locate_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.locate_frame.grid_columnconfigure(0, weight=1); self.locate_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self.locate_frame, text="File Not Found", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20,10))
        ctk.CTkLabel(self.locate_frame, text=f"server.properties could not be found at the configured path.", wraplength=500).pack(pady=10)
        ctk.CTkButton(self.locate_frame, text="Locate File Manually...", command=self._locate_file).pack(pady=20)
    def _locate_file(self):
        filepath = filedialog.askopenfilename(title="Locate server.properties", initialdir=os.getcwd(), filetypes=[("Properties File", "server.properties")])
        if filepath:
            self.properties_path = filepath; self.master.update_properties_path(filepath)
            self.locate_frame.grid_remove(); self.tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="nsew"); self.save_button.grid(row=1, column=0, padx=10, pady=10)
            self.load_properties()
    def load_properties(self):
        try:
            for frame in self.tab_frames.values():
                for widget in frame.winfo_children(): widget.destroy()
            with open(self.properties_path, 'r') as f: lines = f.readlines()
            self.tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="nsew"); self.save_button.grid(row=1, column=0, padx=10, pady=10)
            row_counters = {cat: 0 for cat in self.tab_frames}
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'): continue
                parts = line.split('=', 1);
                if len(parts) != 2: continue
                key, value = parts
                info = self.PROPERTY_INFO.get(key, {"desc": "Custom property from a mod or plugin.", "cat": "Miscellaneous"})
                category = info["cat"]; parent_frame = self.tab_frames[category]; row = row_counters[category]
                ctk.CTkLabel(parent_frame, text=key, font=ctk.CTkFont(weight="bold")).grid(row=row, column=0, padx=10, pady=(10,0), sticky="w")
                if info.get("type") == "boolean":
                    widget = ctk.CTkSwitch(parent_frame, text=""); widget.grid(row=row, column=1, padx=10, pady=(10,0), sticky="w")
                    if value.lower() == "true": widget.select()
                    else: widget.deselect()
                else:
                    widget = ctk.CTkEntry(parent_frame); widget.grid(row=row, column=1, padx=10, pady=(10,0), sticky="ew"); widget.insert(0, value)
                self.entries[key] = widget
                ctk.CTkLabel(parent_frame, text=info["desc"], text_color="gray60").grid(row=row+1, column=0, columnspan=2, padx=10, pady=(0,10), sticky="w")
                row_counters[category] += 2
            for cat in list(self.tab_frames.keys()):
                if row_counters[cat] == 0:
                    try: self.tab_view.delete(cat)
                    except Exception: pass
        except FileNotFoundError: self._show_locate_ui()
        except Exception as e: ctk.CTkLabel(self, text=f"An unexpected error occurred: {e}").pack(expand=True)
    def save_and_close(self):
        try:
            with open(self.properties_path, 'r') as f: lines = f.readlines()
            with open(self.properties_path, 'w') as f:
                for line in lines:
                    stripped_line = line.strip()
                    if not stripped_line or stripped_line.startswith('#'): f.write(line); continue
                    key = stripped_line.split('=', 1)[0]
                    if key in self.entries:
                        widget = self.entries[key]
                        if isinstance(widget, ctk.CTkSwitch): new_value = "true" if widget.get() == 1 else "false"
                        else: new_value = widget.get()
                        f.write(f"{key}={new_value}\n")
                    else: f.write(line)
            self.master.log_message("Server properties saved successfully."); self.destroy()
        except Exception as e: self.master.log_message(f"Error saving properties: {e}")

# --- Pop-up Window Classes ---
class SayWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master); self.title("Broadcast Message"); self.transient(master); self.grab_set(); self.master = master
        center_window(self, 400, 180); self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Enter the message to send to all players:", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=20, pady=(20,5))
        self.message_entry = ctk.CTkEntry(self, font=ctk.CTkFont(size=14), placeholder_text="Message..."); self.message_entry.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        self.message_entry.bind("<Return>", self.send_message)
        ctk.CTkButton(self, text="Send Broadcast", command=self.send_message).grid(row=2, column=0, padx=20, pady=(10,20))
        self.after(250, lambda: self.message_entry.focus())
    def send_message(self, event=None):
        message = self.message_entry.get()
        if message: self.master.send_command(command=f"say {message}")
        self.destroy()

class ShutdownWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master); self.title("Schedule Shutdown"); self.transient(master); self.grab_set(); self.master = master
        center_window(self, 400, 220); self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Shutdown server in:", font=ctk.CTkFont(size=14)).grid(row=0, column=0, columnspan=2, padx=20, pady=(20,5))
        hours_frame = ctk.CTkFrame(self, fg_color="transparent"); hours_frame.grid(row=1, column=0, padx=(20,5), pady=5); ctk.CTkLabel(hours_frame, text="Hours").pack(); self.hours_entry = ctk.CTkEntry(hours_frame, width=100); self.hours_entry.pack()
        minutes_frame = ctk.CTkFrame(self, fg_color="transparent"); minutes_frame.grid(row=1, column=1, padx=(5,20), pady=5); ctk.CTkLabel(minutes_frame, text="Minutes").pack(); self.minutes_entry = ctk.CTkEntry(minutes_frame, width=100); self.minutes_entry.pack()
        self.hours_entry.insert(0, "0"); self.minutes_entry.insert(0, "0")
        self.status_label = ctk.CTkLabel(self, text=""); self.status_label.grid(row=2, column=0, columnspan=2, padx=20, pady=5)
        button_frame = ctk.CTkFrame(self, fg_color="transparent"); button_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=(10,20))
        ctk.CTkButton(button_frame, text="Schedule Shutdown", command=self.schedule).pack(side="left", expand=True, padx=5); ctk.CTkButton(button_frame, text="Cancel", command=self.destroy).pack(side="left", expand=True, padx=5)
        self.after(250, lambda: self.hours_entry.focus())
    def schedule(self):
        try:
            hours = int(self.hours_entry.get() or 0); minutes = int(self.minutes_entry.get() or 0)
            if hours < 0 or minutes < 0: raise ValueError
            self.master.schedule_shutdown(hours, minutes); self.destroy()
        except ValueError: self.status_label.configure(text="Please enter valid, positive numbers.", text_color="#E57373")

class ServerIconWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master); self.title("Server Icon Editor"); self.transient(master); self.grab_set(); self.master = master
        center_window(self, 450, 300); self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=1)
        self.new_image_obj = None
        ctk.CTkLabel(self, text="Current Icon", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, pady=(10,5))
        self.current_icon_label = ctk.CTkLabel(self, text="No server-icon.png found.", width=100, height=100); self.current_icon_label.grid(row=1, column=0); self._load_current_icon()
        ctk.CTkLabel(self, text="New Icon Preview", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=1, pady=(10,5))
        self.new_icon_label = ctk.CTkLabel(self, text="Import an image to preview.", width=100, height=100); self.new_icon_label.grid(row=1, column=1)
        button_frame = ctk.CTkFrame(self, fg_color="transparent"); button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        ctk.CTkButton(button_frame, text="Import Image...", command=self._import_image).pack(side="left", padx=10)
        self.save_button = ctk.CTkButton(button_frame, text="Save as server-icon.png", state="disabled", command=self._save_icon); self.save_button.pack(side="left", padx=10)
        self.status_label = ctk.CTkLabel(self, text=""); self.status_label.grid(row=3, column=0, columnspan=2, pady=(0,10))
    def _load_current_icon(self):
        try: img = Image.open("server-icon.png"); self.current_icon_label.configure(text="", image=ctk.CTkImage(img, size=(64,64)))
        except FileNotFoundError: self.current_icon_label.configure(text="No icon found.", image=None)
        except Exception as e: self.current_icon_label.configure(text=f"Error: {e}", image=None)
    def _import_image(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if not filepath: return
        try:
            img = Image.open(filepath).resize((64, 64), Image.Resampling.LANCZOS)
            self.new_image_obj = img; self.new_icon_label.configure(text="", image=ctk.CTkImage(img, size=(64,64))); self.save_button.configure(state="normal"); self.status_label.configure(text="")
        except Exception: self.status_label.configure(text=f"Error: Could not load image.", text_color="#E57373")
    def _save_icon(self):
        if not self.new_image_obj: return
        try: self.new_image_obj.save("server-icon.png", "PNG"); self.status_label.configure(text="Icon saved successfully!", text_color="#66BB6A"); self._load_current_icon(); self.save_button.configure(state="disabled")
        except Exception: self.status_label.configure(text=f"Error: Could not save icon.", text_color="#E57373")

class AutoStopWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master); self.title("Automation Settings"); self.transient(master); self.grab_set(); self.master = master
        center_window(self, 400, 200); self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Auto-Stop When Server is Empty", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(20,10))
        self.autostop_checkbox = ctk.CTkCheckBox(self, text="Enable auto-stop", command=self.toggle_entry_state); self.autostop_checkbox.grid(row=1, column=0, padx=20, pady=5)
        self.autostop_checkbox.select() if self.master.config.get("autostop_enabled") else self.autostop_checkbox.deselect()
        timer_frame = ctk.CTkFrame(self, fg_color="transparent"); timer_frame.grid(row=2, column=0, padx=20, pady=5)
        ctk.CTkLabel(timer_frame, text="Stop after").pack(side="left")
        self.minutes_entry = ctk.CTkEntry(timer_frame, width=50); self.minutes_entry.pack(side="left", padx=5)
        self.minutes_entry.insert(0, str(self.master.config.get("autostop_minutes", 15)))
        ctk.CTkLabel(timer_frame, text="minutes of inactivity.").pack(side="left")
        ctk.CTkButton(self, text="Save Settings", command=self.save).grid(row=3, column=0, padx=20, pady=(10,20))
        self.toggle_entry_state()
    def toggle_entry_state(self): self.minutes_entry.configure(state="normal" if self.autostop_checkbox.get() else "disabled")
    def save(self):
        try:
            minutes = int(self.minutes_entry.get())
            if minutes <= 0: raise ValueError
            self.master.config["autostop_enabled"] = bool(self.autostop_checkbox.get()); self.master.config["autostop_minutes"] = minutes
            self.master._save_config_to_file(); self.master.log_message("Automation settings saved.", "LAUNCHER")
            self.master._cancel_autostop_timer(); self.destroy()
        except ValueError: MessageBox(self, "Invalid Input", "Please enter a valid, positive number for minutes.")

# --- Main Application Class ---
class MinecraftLauncher(ctk.CTk):
    def __init__(self):
        super().__init__(); self.title("PyLaunch MC - Server Dashboard"); self.server_process = None; self.config = {}; self.server_ip = "N/A"; self.server_port = "N/A"; self.server_running = False
        self.shutdown_timer_thread = None; self.shutdown_event = threading.Event(); self.shutdown_time = None
        self.autostop_timer_thread = None; self.autostop_end_time = None
        center_window(self, 1000, 650); self.minsize(850, 600); self.protocol("WM_DELETE_WINDOW", self.on_closing)
        if not os.path.exists(CONFIG_FILE): self.wait_window(SetupWindow(self))
        self.load_config()
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        self._create_sidebar(); self._create_main_dashboard()
        self.update_ui_from_config()
        self.log_message("Welcome to PyLaunch MC! Ready to start.", "LAUNCHER")
        threading.Thread(target=self._fetch_server_info, daemon=True).start()
        self._find_existing_server_process()

    def on_closing(self):
        if self.server_running: MessageBox(self, title="Cannot Close", message="The server is still running.\nPlease stop the server before closing the launcher.")
        else: self.destroy()

    def _create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0); self.sidebar_frame.grid(row=0, column=0, sticky="nsew"); self.sidebar_frame.grid_rowconfigure(4, weight=1)
        logo_label = ctk.CTkLabel(self.sidebar_frame, text="PyLaunch MC", font=ctk.CTkFont(size=20, weight="bold")); logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        controls_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent"); controls_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(controls_frame, text="Server Controls", font=ctk.CTkFont(weight="bold")).pack()
        self.start_button = ctk.CTkButton(controls_frame, text="Start Server", command=self.start_server_thread); self.start_button.pack(fill="x", pady=5)
        self.stop_button = ctk.CTkButton(controls_frame, text="Stop Server", command=self.stop_server, state="disabled"); self.stop_button.pack(fill="x", pady=(0,5))
        actions_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent"); actions_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(actions_frame, text="Server Actions", font=ctk.CTkFont(weight="bold")).pack()
        self.save_button = ctk.CTkButton(actions_frame, text="Save World", command=self._save_world); self.save_button.pack(fill="x", pady=5)
        self.say_button = ctk.CTkButton(actions_frame, text="Broadcast Message", command=self.open_say_window); self.say_button.pack(fill="x", pady=(0,5))
        self.schedule_stop_button = ctk.CTkButton(actions_frame, text="Schedule Stop", command=self.open_shutdown_window); self.schedule_stop_button.pack(fill="x", pady=5)
        management_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent"); management_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(management_frame, text="Management", font=ctk.CTkFont(weight="bold")).pack()
        self.backup_button = ctk.CTkButton(management_frame, text="Create Backup", command=self.create_backup_thread); self.backup_button.pack(fill="x", pady=5)
        self.settings_button = ctk.CTkButton(management_frame, text="Edit Settings", command=self.open_settings); self.settings_button.pack(fill="x", pady=(0,5))
        self.automation_button = ctk.CTkButton(management_frame, text="Automation", command=self.open_autostop_window); self.automation_button.pack(fill="x", pady=5)
        self.server_icon_button = ctk.CTkButton(management_frame, text="Server Icon", command=self.open_server_icon_window); self.server_icon_button.pack(fill="x", pady=(5,5))
        console_view_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent"); console_view_frame.grid(row=4, column=0, padx=20, pady=20, sticky="sew")
        self.console_switch = ctk.CTkSwitch(console_view_frame, text="Show Full Log", command=self.toggle_console_view); self.console_switch.pack(pady=10)

    def _create_main_dashboard(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent"); self.main_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1); self.main_frame.grid_rowconfigure(2, weight=1)
        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent"); top_frame.grid(row=0, column=0, sticky="ew"); top_frame.grid_columnconfigure(0, weight=1)
        status_info_frame = ctk.CTkFrame(top_frame, fg_color="transparent"); status_info_frame.grid(row=0, column=0, sticky="w")
        self.server_status_label = ctk.CTkLabel(status_info_frame, text="Server is Offline", font=ctk.CTkFont(size=24, weight="bold"), text_color="#E57373"); self.server_status_label.pack(anchor="w", padx=10)
        self.shutdown_status_frame = ctk.CTkFrame(status_info_frame, fg_color="transparent"); self.shutdown_status_frame.pack(anchor="w", padx=10, pady=2, fill="x")
        self.shutdown_status_label = ctk.CTkLabel(self.shutdown_status_frame, text="", text_color="gray70"); self.shutdown_status_label.pack(side="left")
        self.cancel_shutdown_button = ctk.CTkButton(self.shutdown_status_frame, text="Cancel", width=60, height=20, text_color="gray70", command=self.cancel_shutdown); self.cancel_shutdown_button.pack(side="left", padx=10)
        self.autostop_status_label = ctk.CTkLabel(status_info_frame, text="", text_color="gray70"); self.autostop_status_label.pack(anchor="w", padx=10, pady=2)
        self.shutdown_status_frame.pack_forget(); self.autostop_status_label.pack_forget()
        conn_frame = ctk.CTkFrame(top_frame); conn_frame.grid(row=0, column=1, sticky="e")
        self.ip_address_entry = ctk.CTkEntry(conn_frame, placeholder_text="Address (IP:Port)", font=ctk.CTkFont(size=14), width=220); self.ip_address_entry.pack(side="left", fill="x", padx=(10,5), pady=10)
        self.ip_address_entry.configure(state="readonly")
        self.copy_addr_button = ctk.CTkButton(conn_frame, text="Copy Address", height=28, width=110, command=self._copy_addr); self.copy_addr_button.pack(side="left", padx=(0,10), pady=10)
        self.player_list_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Online Players"); self.player_list_frame.grid(row=1, column=0, padx=0, pady=10, sticky="nsew")
        console_container = ctk.CTkFrame(self.main_frame); console_container.grid(row=2, column=0, sticky="nsew"); console_container.grid_rowconfigure(0, weight=1); console_container.grid_columnconfigure(0, weight=1)
        self.full_console = ctk.CTkTextbox(console_container, font=("Courier New", 12));
        self.simple_console_frame = ctk.CTkScrollableFrame(console_container, label_text="Event Log");
        self.command_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Enter server command and press Enter..."); self.command_entry.grid(row=3, column=0, pady=(10, 0), sticky="ew"); self.command_entry.bind("<Return>", self.send_command)
        self.toggle_console_view()

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f: self.config = json.load(f)
            if "autostop_enabled" not in self.config: self.config["autostop_enabled"] = False
            if "autostop_minutes" not in self.config: self.config["autostop_minutes"] = 15
            if "properties_path" not in self.config: self.config["properties_path"] = "server.properties"
        except (FileNotFoundError, json.JSONDecodeError): self.log_message("FATAL: config.json is missing or corrupted.", "ERROR"); self.config = {"backups_enabled": False}
    def _save_config_to_file(self):
        with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=4)

    def update_properties_path(self, new_path):
        relative_path = os.path.relpath(new_path, os.getcwd()); self.config["properties_path"] = relative_path
        self._save_config_to_file(); self.log_message("Updated server.properties location.", "LAUNCHER")

    def update_ui_from_config(self):
        if not self.config.get("backups_enabled"): self.backup_button.configure(state="disabled")
        self.set_server_action_buttons_state()

    def set_server_action_buttons_state(self):
        state = "normal" if self.server_running else "disabled"
        self.schedule_stop_button.configure(state=state)
        self.save_button.configure(state=state)
        self.say_button.configure(state=state)

    def toggle_console_view(self):
        if self.console_switch.get() == 1: self.full_console.grid(row=0, column=0, sticky="nsew"); self.simple_console_frame.grid_remove()
        else: self.simple_console_frame.grid(row=0, column=0, sticky="nsew"); self.full_console.grid_remove()

    def log_message(self, message, tag="INFO"):
        colors = {"ERROR": "#E57373", "WARN": "#FFCA28", "INFO": "gray80", "CHAT": "#FFFFFF", "JOIN": "#4DD0E1", "LEAVE": "#4DD0E1", "LAUNCHER": "#BDBDBD"}
        timestamp = datetime.now().strftime('%H:%M:%S'); 
        log_entry = ctk.CTkLabel(self.simple_console_frame, text=f"[{timestamp}] {message}", text_color=colors.get(tag, "gray80"), wraplength=800, justify="left", font=ctk.CTkFont(size=13))
        log_entry.pack(anchor="w", padx=5, pady=1)
        self.after(100, self.simple_console_frame._parent_canvas.yview_moveto, 1.0)

    def _fetch_server_info(self):
        properties = {}
        try:
            with open(self.config.get("properties_path", "server.properties"), 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'): key, value = line.strip().split('=', 1); properties[key] = value
            self.server_port = properties.get("server-port", "25565"); self.server_ip = properties.get("server-ip", "")
            if not self.server_ip:
                try: self.server_ip = requests.get('https://api.ipify.org', timeout=3).text
                except Exception: self.server_ip = "127.0.0.1"
            self.ip_address_entry.configure(state="normal"); self.ip_address_entry.delete(0, "end"); self.ip_address_entry.insert(0, f"{self.server_ip}:{self.server_port}"); self.ip_address_entry.configure(state="readonly")
        except FileNotFoundError: self.log_message("Could not read server.properties.", "WARN")

    def _copy_addr(self):
        self.clipboard_clear(); self.clipboard_append(self.ip_address_entry.get()); self.copy_addr_button.configure(text="Copied!")
        self.after(2000, lambda: self.copy_addr_button.configure(text="Copy Address"))

    def _update_player_list_ui(self, count, max_players, player_names):
        self.player_list_frame.configure(label_text=f"Online Players ({count}/{max_players})")
        for widget in self.player_list_frame.winfo_children(): widget.destroy()
        if not player_names: ctk.CTkLabel(self.player_list_frame, text="No players online.", text_color="gray60").pack(anchor="w", padx=5)
        else:
            for name in player_names:
                player_row = ctk.CTkFrame(self.player_list_frame, fg_color="transparent"); player_row.pack(fill="x", pady=2)
                ctk.CTkLabel(player_row, text=name, font=ctk.CTkFont(size=14)).pack(side="left", padx=5)
                ctk.CTkButton(player_row, text="De-OP", height=20, width=50, command=lambda n=name: self.send_command(command=f"deop {n}")).pack(side="right", padx=(2,5))
                ctk.CTkButton(player_row, text="OP", height=20, width=40, command=lambda n=name: self.send_command(command=f"op {n}")).pack(side="right", padx=2)
                ctk.CTkButton(player_row, text="Kick", height=20, width=50, command=lambda n=name: self.send_command(command=f"kick {n}")).pack(side="right", padx=2)
        if self.config.get("autostop_enabled") and self.server_running:
            if count == "0" and not self.autostop_end_time: self._start_autostop_timer()
            elif count != "0" and self.autostop_end_time: self._cancel_autostop_timer()

    def _player_list_updater_thread(self):
        while self.server_running: self.send_command(command="list"); time.sleep(30)
        
    def _find_existing_server_process(self):
        jar_name = self.config.get("jar_file");
        if not jar_name: return
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.name().lower() in ['java.exe', 'javaw.exe']:
                    cmdline = proc.cmdline()
                    if '-jar' in cmdline and jar_name in cmdline:
                        self.server_process = proc; self.server_running = True
                        self.start_button.configure(state="disabled"); self.stop_button.configure(state="normal"); self.backup_button.configure(state="disabled"); self.settings_button.configure(state="disabled")
                        self.set_server_action_buttons_state(); self.server_status_label.configure(text="Detected Running Server", text_color="#66BB6A")
                        self.log_message("An existing server process was found running.", "WARN"); self.log_message("Please stop it for a clean restart.", "WARN")
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): pass

    def parse_and_display_simple_log(self, line):
        self.full_console.insert("end", line); self.full_console.see("end")
        line = line.strip()
        match_list = re.search(r'There are (\d+) of a max of (\d+) players online: ?(.*)', line)
        if match_list:
            count, max_p, players_str = match_list.groups()
            players = sorted(players_str.split(', ')) if players_str else []
            self.after(0, self._update_player_list_ui, count, max_p, players)
            return
        match_chat = re.search(r'<(\w+)> (.*)', line); match_join_leave = re.search(r'(\w+) (joined|left) the game', line)
        match_done = re.search(r'Done \((.*s)\)!', line); match_error = re.search(r'\[.*ERROR\]: (.*)', line); match_warn = re.search(r'\[.*WARN\]: (.*)', line)
        if match_done: self.server_status_label.configure(text="Server is Online", text_color="#66BB6A"); self.log_message(f"Server loaded successfully in {match_done.group(1)}", "JOIN")
        elif match_chat: self.log_message(f"<{match_chat.group(1)}> {match_chat.group(2)}", "CHAT")
        elif match_join_leave:
            tag = "JOIN" if match_join_leave.group(2) == "joined" else "LEAVE"; self.log_message(f"{match_join_leave.group(1)} {match_join_leave.group(2)} the game", tag)
        elif match_error: self.log_message(f"[ERROR] {match_error.group(1)}", "ERROR")
        elif match_warn: self.log_message(f"[WARN] {match_warn.group(1)}", "WARN")

    def open_say_window(self):
        if self.server_running: SayWindow(self)
        else: self.log_message("Cannot broadcast: Server is not running.", "WARN")
    def _save_world(self):
        self.send_command(command="save-all"); self.save_button.configure(text="Saved!")
        self.after(2000, lambda: self.save_button.configure(text="Save World"))
    def open_shutdown_window(self):
        if self.server_running: ShutdownWindow(self)
        else: self.log_message("Cannot schedule stop: Server is not running.", "WARN")
    def open_autostop_window(self): AutoStopWindow(self)
    def open_server_icon_window(self): ServerIconWindow(self)
    def open_settings(self):
        path = self.config.get("properties_path", "server.properties")
        absolute_path = os.path.join(os.getcwd(), path)
        SettingsWindow(self, absolute_path)

    def schedule_shutdown(self, hours, minutes):
        total_seconds = (hours * 3600) + (minutes * 60)
        if total_seconds <= 0: return
        if self.shutdown_timer_thread and self.shutdown_timer_thread.is_alive():
            self.log_message("A shutdown is already scheduled. Please cancel it first.", "WARN"); return
        self.shutdown_time = datetime.now() + timedelta(seconds=total_seconds); self.shutdown_event.clear()
        self.shutdown_timer_thread = threading.Thread(target=self._shutdown_timer_logic, args=(total_seconds, hours, minutes), daemon=True); self.shutdown_timer_thread.start()
        self.shutdown_status_frame.pack(anchor="w", padx=10, pady=2, fill="x")
        threading.Thread(target=self._update_countdown_label, daemon=True).start()

    def cancel_shutdown(self):
        if self.shutdown_timer_thread and self.shutdown_timer_thread.is_alive():
            self.shutdown_event.set(); self.shutdown_status_frame.pack_forget()
            self.log_message("Scheduled server shutdown has been cancelled.", "LAUNCHER")

    def _update_countdown_label(self):
        while self.server_running and self.shutdown_time and not self.shutdown_event.is_set():
            remaining = self.shutdown_time - datetime.now()
            if remaining.total_seconds() < 0: break
            hours, rem = divmod(int(remaining.total_seconds()), 3600); mins, secs = divmod(rem, 60)
            self.shutdown_status_label.configure(text=f"Shutdown in: {hours:02d}:{mins:02d}:{secs:02d}")
            time.sleep(1)
        self.shutdown_status_frame.pack_forget()

    def _shutdown_timer_logic(self, total_seconds, hours, minutes):
        duration_str = f"{hours} hour(s)" if hours > 0 else f"{minutes} minute(s)"
        self.send_command(command=f"say SERVER SHUTDOWN SCHEDULED IN {duration_str.upper()}")
        halfway_point_seconds = total_seconds / 2; one_minute_warning_seconds = 60
        announced_halfway = False; announced_one_minute = False
        for i in range(total_seconds):
            if self.shutdown_event.is_set(): return
            remaining = total_seconds - i
            if not announced_halfway and remaining <= halfway_point_seconds: self.send_command(command=f"say Server is shutting down in approximately {round(halfway_point_seconds / 60)} minutes."); announced_halfway = True
            if not announced_one_minute and remaining <= one_minute_warning_seconds: self.send_command(command=f"say FINAL WARNING: Server is shutting down in 1 minute."); announced_one_minute = True
            time.sleep(1)
        if not self.shutdown_event.is_set(): self.after(0, self._execute_safe_shutdown)

    def _start_autostop_timer(self):
        if self.autostop_timer_thread and self.autostop_timer_thread.is_alive(): return
        self.log_message(f"Server is empty. Auto-stopping in {self.config.get('autostop_minutes')} minutes.", "WARN")
        self.autostop_end_time = datetime.now() + timedelta(minutes=self.config.get('autostop_minutes', 15))
        self.autostop_timer_thread = threading.Thread(target=self._update_autostop_countdown_label, daemon=True); self.autostop_timer_thread.start()
        self.autostop_status_label.pack(anchor="w", padx=10, pady=2)

    def _cancel_autostop_timer(self): self.autostop_end_time = None; self.autostop_status_label.pack_forget()
    
    def _update_autostop_countdown_label(self):
        while self.server_running and self.autostop_end_time:
            remaining = self.autostop_end_time - datetime.now()
            if remaining.total_seconds() < 0:
                if self.server_running and self.autostop_end_time: self.after(0, self._execute_safe_shutdown)
                break
            mins, secs = divmod(int(remaining.total_seconds()), 60)
            self.autostop_status_label.configure(text=f"Auto-stopping in: {mins:02d}:{secs:02d}")
            time.sleep(1)
        self.autostop_status_label.pack_forget()

    def _execute_safe_shutdown(self):
        self.log_message("Executing safe shutdown...", "LAUNCHER")
        if isinstance(self.server_process, subprocess.Popen): self.send_command(command="save-all"); time.sleep(3)
        self.stop_server()

    def start_server_thread(self): threading.Thread(target=self.start_server, daemon=True).start()

    def start_server(self):
        self.server_running = True; self.set_server_action_buttons_state()
        self.start_button.configure(state="disabled"); self.stop_button.configure(state="normal"); self.backup_button.configure(state="disabled"); self.settings_button.configure(state="disabled")
        self.server_status_label.configure(text="Starting...", text_color="#FFCA28"); self.log_message("Starting server...", "LAUNCHER")
        threading.Thread(target=self._player_list_updater_thread, daemon=True).start()
        command = ["java", *self.config.get("java_args", "").split(), "-jar", self.config.get("jar_file", "server.jar"), "nogui"]
        try:
            self.server_process = subprocess.Popen(command, cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            for line in iter(self.server_process.stdout.readline, ''): self.parse_and_display_simple_log(line)
            self.server_process.wait()
        except FileNotFoundError: self.log_message(f"Error: '{self.config.get('jar_file')}' not found. Check config.json.", "ERROR"); 
        except Exception as e: self.log_message(f"An error occurred: {e}", "ERROR")
        finally:
            self.server_running = False; self.server_process = None
            self.cancel_shutdown(); self._cancel_autostop_timer()
            self.log_message("Server has stopped.", "LAUNCHER"); self.server_status_label.configure(text="Server is Offline", text_color="#E57373")
            self._update_player_list_ui(0, 0, []); self.set_server_action_buttons_state()
            self.start_button.configure(state="normal"); self.stop_button.configure(state="disabled"); self.settings_button.configure(state="normal")
            if self.config.get("backups_enabled"): self.backup_button.configure(state="normal")

    def stop_server(self):
        self.cancel_shutdown(); self._cancel_autostop_timer()
        if not self.server_process: return
        if isinstance(self.server_process, subprocess.Popen):
            self.log_message("Sending 'stop' command to server...", "LAUNCHER")
            try: self.server_process.stdin.write("stop\n"); self.server_process.stdin.flush()
            except Exception as e: self.log_message(f"Could not send stop command: {e}", "ERROR")
        elif isinstance(self.server_process, psutil.Process):
            self.log_message("Terminating existing server process...", "LAUNCHER")
            try:
                self.server_process.terminate()
                self.server_running = False; self.server_process = None
                self.log_message("Server has stopped.", "LAUNCHER"); self.server_status_label.configure(text="Server is Offline", text_color="#E57373")
                self.start_button.configure(state="normal"); self.stop_button.configure(state="disabled"); self.settings_button.configure(state="normal"); self.set_server_action_buttons_state()
                if self.config.get("backups_enabled"): self.backup_button.configure(state="normal")
            except psutil.NoSuchProcess: self.log_message("Process already terminated.", "WARN")
            except Exception as e: self.log_message(f"Could not terminate process: {e}", "ERROR")

    def send_command(self, event=None, command=None):
        if command is None: command = self.command_entry.get()
        if self.server_running and isinstance(self.server_process, subprocess.Popen) and self.server_process.poll() is None and command:
            if not command.startswith("list"): self.log_message(f"Sent command: /{command}", "LAUNCHER")
            try: self.server_process.stdin.write(command + '\n'); self.server_process.stdin.flush(); self.command_entry.delete(0, "end")
            except Exception as e: self.log_message(f"Failed to send command: {e}", "ERROR")
        elif not self.server_running: self.log_message("Cannot send command: Server is not running.", "WARN")
        elif isinstance(self.server_process, psutil.Process): self.log_message("Cannot send commands to a detected server. Please restart it.", "WARN")

    def create_backup_thread(self): threading.Thread(target=self.create_backup, daemon=True).start()

    def create_backup(self):
        self.backup_button.configure(state="disabled"); self.log_message("Starting backup...", "LAUNCHER")
        world_dir = os.path.join(os.getcwd(), self.config.get("world_name", "world")); backup_dir = os.path.join(os.getcwd(), "backups"); gdrive_path = self.config.get("gdrive_sync_path")
        if not os.path.isdir(world_dir): self.log_message(f"Backup failed: World folder '{self.config.get('world_name')}' not found.", "ERROR"); self.backup_button.configure(state="normal"); return
        os.makedirs(backup_dir, exist_ok=True); timestamp = datetime.now().strftime('%Y_%m_%d-%H%M%S'); backup_name = f"{self.config.get('world_name', 'world')}_backup_{timestamp}.zip"; backup_path = os.path.join(backup_dir, backup_name)
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(world_dir):
                    for file in files: zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), world_dir))
            self.log_message(f"Successfully created backup: {backup_name}", "LAUNCHER")
            self.log_message("Copying backup to local cloud sync folder...", "LAUNCHER"); os.makedirs(gdrive_path, exist_ok=True); shutil.copy(backup_path, gdrive_path)
            self.log_message("Copy complete. Your cloud service will now sync the file.", "LAUNCHER")
        except Exception as e: self.log_message(f"Backup process failed: {e}", "ERROR")
        finally: self.backup_button.configure(state="normal")

def show_critical_error_and_exit(title, message):
    root = ctk.CTk(); root.withdraw()
    msg_box = MessageBox(root, title=title, message=message)
    root.wait_window(msg_box)
    sys.exit()

if __name__ == "__main__":
    # --- Pre-flight Check ---
    required_files = ["eula.txt", "server.properties"]
    for filename in required_files:
        if not os.path.exists(filename):
            show_critical_error_and_exit(
                "Server File Not Found",
                f"Please make sure PyLaunchMC is in a valid Minecraft server folder."
            )
    
    app = MinecraftLauncher()
    app.mainloop()
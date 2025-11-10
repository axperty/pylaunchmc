import customtkinter as ctk
from customtkinter import filedialog
import json
import os
from utils import center_window

CONFIG_FILE = "config.json"

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
        config_data = {
            "setup_complete": True, "world_name": "world", "jar_file": self.jar_file, 
            "java_args": "-Xmx2G -Xms1G", "backups_enabled": bool(self.backup_checkbox.get()), 
            "gdrive_sync_path": self.backup_path, "autostop_enabled": False, 
            "autostop_minutes": 15, "properties_path": "server.properties"
        }
        with open(CONFIG_FILE, 'w') as f: json.dump(config_data, f, indent=4)
        self.destroy()
import customtkinter as ctk
import threading
import requests
import time
from queue import Queue, Empty
from customtkinter import filedialog
from PIL import Image
from utils import center_window

class MessageBox(ctk.CTkToplevel):
    def __init__(self, master, title, message):
        super().__init__(master); self.title(title); self.transient(master); self.grab_set(); center_window(self, 400, 150)
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1)
        ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=14), wraplength=350).grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        ctk.CTkButton(self, text="OK", command=self.destroy, width=100).grid(row=1, column=0, padx=20, pady=(0,20))
        self.after(250, self.focus)

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
        hours_frame = ctk.CTkFrame(self, fg_color="transparent"); hours_frame.grid(row=1, column=0, padx=(20,5), pady=5)
        ctk.CTkLabel(hours_frame, text="Hours").pack(); self.hours_entry = ctk.CTkEntry(hours_frame, width=100); self.hours_entry.pack()
        minutes_frame = ctk.CTkFrame(self, fg_color="transparent"); minutes_frame.grid(row=1, column=1, padx=(5,20), pady=5)
        ctk.CTkLabel(minutes_frame, text="Minutes").pack(); self.minutes_entry = ctk.CTkEntry(minutes_frame, width=100); self.minutes_entry.pack()
        self.hours_entry.insert(0, "0"); self.minutes_entry.insert(0, "0")
        self.status_label = ctk.CTkLabel(self, text=""); self.status_label.grid(row=2, column=0, columnspan=2, padx=20, pady=5)
        button_frame = ctk.CTkFrame(self, fg_color="transparent"); button_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=(10,20))
        ctk.CTkButton(button_frame, text="Schedule Shutdown", command=self.schedule).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=self.destroy).pack(side="left", expand=True, padx=5)
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
        self.current_icon_label = ctk.CTkLabel(self, text="No server-icon.png found.", width=100, height=100); self.current_icon_label.grid(row=1, column=0)
        self._load_current_icon()
        ctk.CTkLabel(self, text="New Icon Preview", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=1, pady=(10,5))
        self.new_icon_label = ctk.CTkLabel(self, text="Import an image to preview.", width=100, height=100); self.new_icon_label.grid(row=1, column=1)
        button_frame = ctk.CTkFrame(self, fg_color="transparent"); button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        ctk.CTkButton(button_frame, text="Import Image...", command=self._import_image).pack(side="left", padx=10)
        self.save_button = ctk.CTkButton(button_frame, text="Save as server-icon.png", state="disabled", command=self._save_icon); self.save_button.pack(side="left", padx=10)
        self.status_label = ctk.CTkLabel(self, text=""); self.status_label.grid(row=3, column=0, columnspan=2, pady=(0,10))
    def _load_current_icon(self):
        try:
            img = Image.open("server-icon.png"); ctk_img = ctk.CTkImage(img, size=(64,64))
            self.current_icon_label.configure(text="", image=ctk_img)
        except FileNotFoundError: self.current_icon_label.configure(text="No icon found.", image=None)
        except Exception as e: self.current_icon_label.configure(text=f"Error: {e}", image=None)
    def _import_image(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if not filepath: return
        try:
            img = Image.open(filepath).resize((64, 64), Image.Resampling.LANCZOS)
            self.new_image_obj = img; ctk_img = ctk.CTkImage(img, size=(64,64))
            self.new_icon_label.configure(text="", image=ctk_img); self.save_button.configure(state="normal"); self.status_label.configure(text="")
        except Exception: self.status_label.configure(text=f"Error: Could not load image.", text_color="#E57373")
    def _save_icon(self):
        if not self.new_image_obj: return
        try:
            self.new_image_obj.save("server-icon.png", "PNG")
            self.status_label.configure(text="Icon saved successfully!", text_color="#66BB6A"); self._load_current_icon(); self.save_button.configure(state="disabled")
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
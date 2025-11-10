import customtkinter as ctk
from customtkinter import filedialog
import os
from utils import center_window

class SettingsWindow(ctk.CTkToplevel):
    PROPERTY_INFO = {
        # ... [The PROPERTY_INFO dictionary remains exactly the same as before, no need to copy it here again] ...
        "motd": {"desc": "The 'message of the day' displayed in the server list.", "cat": "General"}, "server-port": {"desc": "The network port the server listens on. Default is 25565.", "cat": "General"}, "view-distance": {"desc": "Sets the server-side render distance in chunks (3-32).", "cat": "General"}, "simulation-distance": {"desc": "Distance in chunks that the server will tick entities (3-32).", "cat": "General"}, "gamemode": {"desc": "Default game mode for new players (survival, creative, etc.).", "cat": "World"}, "difficulty": {"desc": "Defines the game difficulty (peaceful, easy, normal, hard).", "cat": "World"}, "level-name": {"desc": "The name of your primary world folder.", "cat": "World"}, "level-seed": {"desc": "The seed used to generate the world. Leave blank for random.", "cat": "World"}, "generate-structures": {"desc": "Defines if structures like villages and temples generate.", "cat": "World", "type": "boolean"}, "hardcore": {"desc": "If true, players who die are set to Spectator mode.", "cat": "World", "type": "boolean"}, "allow-nether": {"desc": "Allows players to travel to the Nether dimension.", "cat": "World", "type": "boolean"}, "max-world-size": {"desc": "Maximum radius of the world border in blocks.", "cat": "World"}, "max-players": {"desc": "The maximum number of players that can join the server.", "cat": "Player"}, "pvp": {"desc": "Enable or disable Player vs. Player combat.", "cat": "Player", "type": "boolean"}, "online-mode": {"desc": "Recommended 'true'. Set to 'false' only for offline/cracked servers.", "cat": "Player", "type": "boolean"}, "white-list": {"desc": "If true, only players on the whitelist can join.", "cat": "Player", "type": "boolean"}, "allow-flight": {"desc": "Allows players to use flight (e.g., in Creative/Spectator).", "cat": "Player", "type": "boolean"}, "spawn-protection": {"desc": "Radius of blocks around spawn protected from non-OP players.", "cat": "Player"}, "spawn-animals": {"desc": "Determines if friendly animals can spawn naturally.", "cat": "Advanced", "type": "boolean"}, "spawn-monsters": {"desc": "Determines if hostile monsters can spawn naturally.", "cat": "Advanced", "type": "boolean"}, "spawn-npcs": {"desc": "Determines if villagers can spawn in villages.", "cat": "Advanced", "type": "boolean"}, "enable-command-block": {"desc": "Enables the use of command blocks.", "cat": "Advanced", "type": "boolean"}, "op-permission-level": {"desc": "Sets the permission level for server operators (1-4).", "cat": "Advanced"}, "enable-query": {"desc": "Enables the GameSpy4 protocol server listener.", "cat": "Advanced", "type": "boolean"}, "resource-pack": {"desc": "URL to a server-side resource pack.", "cat": "Advanced"}, "resource-pack-sha1": {"desc": "SHA-1 hash of the resource pack to verify its integrity.", "cat": "Advanced"},
    }

    def __init__(self, master, properties_path):
        super().__init__(master); self.title("Server Properties Editor"); self.master = master
        self.properties_path = properties_path; self.entries = {}
        center_window(self, 700, 550); self.rowconfigure(0, weight=1); self.columnconfigure(0, weight=1)
        
        # Main container for tabs
        self.tab_view = ctk.CTkTabview(self);
        self.tab_frames = {
            "General": ctk.CTkScrollableFrame(self.tab_view.add("General")), "World": ctk.CTkScrollableFrame(self.tab_view.add("World")),
            "Player": ctk.CTkScrollableFrame(self.tab_view.add("Player")), "Advanced": ctk.CTkScrollableFrame(self.tab_view.add("Advanced")),
            "Miscellaneous": ctk.CTkScrollableFrame(self.tab_view.add("Miscellaneous"))
        }
        for frame in self.tab_frames.values():
            frame.pack(expand=True, fill="both"); frame.grid_columnconfigure(1, weight=1)

        # Frame for the "locate file" UI
        self.locate_frame = ctk.CTkFrame(self)
        
        self.save_button = ctk.CTkButton(self, text="Save and Close", command=self.save_and_close)
        
        self.load_properties()

    def _show_locate_ui(self):
        self.tab_view.grid_remove() # Hide tabs
        self.save_button.grid_remove()

        self.locate_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.locate_frame.grid_columnconfigure(0, weight=1)
        self.locate_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.locate_frame, text="File Not Found", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20,10))
        ctk.CTkLabel(self.locate_frame, text=f"server.properties could not be found at:\n{os.path.basename(self.properties_path)}", wraplength=500).pack(pady=10)
        ctk.CTkButton(self.locate_frame, text="Locate File Manually...", command=self._locate_file).pack(pady=20)

    def _locate_file(self):
        filepath = filedialog.askopenfilename(title="Locate server.properties", initialdir=os.getcwd(), filetypes=[("Properties File", "server.properties")])
        if filepath:
            self.properties_path = filepath
            self.master.update_properties_path(filepath) # Tell main window to save the new path
            self.locate_frame.grid_remove() # Hide the locate UI
            self.tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="nsew") # Show tabs again
            self.save_button.grid(row=1, column=0, padx=10, pady=10)
            self.load_properties() # Retry loading

    def load_properties(self):
        try:
            # Clear any previous widgets before loading
            for frame in self.tab_frames.values():
                for widget in frame.winfo_children(): widget.destroy()

            with open(self.properties_path, 'r') as f: lines = f.readlines()
            
            self.tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            self.save_button.grid(row=1, column=0, padx=10, pady=10)

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
            
            for cat in list(self.tab_frames.keys()): # Use list to allow deletion
                if row_counters[cat] == 0:
                    try: self.tab_view.delete(cat)
                    except Exception: pass
        except FileNotFoundError:
            self._show_locate_ui()
        except Exception as e:
            ctk.CTkLabel(self, text=f"An unexpected error occurred: {e}").pack(expand=True)
    
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
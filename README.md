# PyLaunchMC

[![GitHub Release](https://img.shields.io/github/v/release/axperty/pylaunchmc?style=flat&logo=github&logoColor=%23FFFFFF&label=Latest%20Release&labelColor=2D2C2C&color=%234e992e)](https://github.com/axperty/pylaunchmc/releases/alpha)
[![GitHub Issues](https://img.shields.io/github/issues/axperty/pylaunchmc?style=flat&logo=github&logoColor=%23FFFFFF&label=Issues&labelColor=2D2C2C&color=%23c13030)](https://github.com/axperty/pylaunchmc/issues)
[![Discord](https://img.shields.io/discord/1194733791818821663?style=flat&logo=discord&logoColor=%23FFFFFF&label=Discord&labelColor=2D2C2C&color=%234e992e)](https://discord.gg/e2BQx4bbsU)
[![PayPal](https://img.shields.io/badge/Donate%20on%20PayPal-0079C1?style=flat&logo=paypal)](https://paypal.me/kevgelhorn)

![PyLaunchMC Banner](https://i.imgur.com/IDzFsA6.png)

---

### Overview

**PyLaunchMC** is a simple yet powerful Minecraft server dashboard for Windows, designed for everyone from first-time server owners to experienced administrators. It replaces the complex command line with a clean, intuitive, and modern user interface.

It's a true "plug-and-play" solution: just drop the executable into an existing server folder, and you get instant access to a full suite of management tools.

### Contributing

Your contributions make PyLaunchMC better for everyone. Whether you're reporting a bug, suggesting a new feature, or submitting a code improvement, all help is welcome. Please feel free to open an issue or a pull request!

### Features

PyLaunchMC is packed with features that simplify every aspect of server management:

*   **🖥️ Intuitive Dashboard**
    *   A single, clean view showing server status, IP address, and a live player list.
    *   Color-coded status updates (Offline, Starting, Online).

*   **👥 Effortless Player Management**
    *   See a list of all online players, updated automatically.
    *   Kick, OP, or De-OP any player with a single click next to their name.

*   **🔔 Easy-Read Event Log**
    *   A simplified, color-coded console that shows player chat, joins/leaves, and important warnings.
    *   A "Show Full Log" switch for advanced users who need to see the raw server output.

*   **🤖 Powerful Automation**
    *   **Schedule Shutdowns:** Stop your server at a specific time with automatic in-game warnings for players.
    *   **Auto-Stop on Empty:** Intelligently stops the server if it's been empty for a configurable amount of time, saving resources.

*   **⚙️ Simple Configuration**
    *   **Optimized Properties Editor:** A lag-free, tabbed UI to edit `server.properties` with helpful descriptions.
    *   **Server Icon Editor:** Import any image, get a live 64x64 preview, and save it as your `server-icon.png`.

*   **🛡️ Safety & Reliability**
    *   **Safe Shutdown:** Prevents closing the app while the server is running to protect your world from corruption.
    *   **Orphan Process Detection:** Finds and allows you to stop a server that was left running after a crash.
    *   **Startup Check:** Ensures the app is in a valid server folder before it launches.

---

### Getting Started

Getting your server running with PyLaunchMC takes less than a minute.

#### Prerequisites
*   A **Windows 10/11** PC.
*   **Java 17 or newer.** Required to run modern Minecraft servers. You can get it from [Adoptium](https://adoptium.net/temurin/releases/).
*   An **existing Minecraft server folder** containing a `server.jar`, `eula.txt`, and `server.properties`.

#### Installation
1.  **Download:** Go to the [**Releases Page**](https://github.com/axperty/pylaunchmc/releases/tag/alpha).
2.  **Place the `.exe`:** Move `PyLaunchMC.exe` into your Minecraft server folder.
3.  **Run:** Double-click `PyLaunchMC.exe`. A one-time setup will ask you to confirm your `server.jar` file.
4.  You're done! Click "Start Server" and enjoy.

### Building from Source
If you want to modify the code or build the executable yourself:

1.  Clone the repository: `git clone https://github.com/axperty/pylaunchmc.git`
2.  Install dependencies: `pip install -r requirements.txt`
3.  Run the app: `python launch_server.py`
4.  To build the `.exe`, run: `pyinstaller --onefile --windowed --name "PyLaunchMC" --icon="icon.ico" launch_server.py`
    The final executable will be in the `dist` folder.

# BatchLeagueReplays 🚀

A blazing fast, modern PyQt6 desktop utility to batch browse historical League of Legends match history data and trigger old replay file downloads directly through Riot's local Client UX (LCU) API framework. 

Built natively on top of the ultra-fast Python packaging manager `uv`.

---

## ✨ Features

* **Subprocess `curl` Fetching:** Outpasses traditional script boundaries and network handshake errors by querying the local game engine data via Windows' native terminal pipelines.
* **Side-by-Side Viewports:** Spawns independent, dedicated viewer windows for each separate query session so you can parse old match details without wiping your workspace.
* **Data Dragon Integration:** Automatically pulls official live game version assets on application startup to cleanly map numeric index IDs into string character names (e.g., *Sett*, *Jax*, *Kayn*).
* **Automatic Workspace Syncing:** Saves real-time snapshot historical structures directly to your system's localized `%APPDATA%` mapping path with clean timestamp labels.
* **Fallback Command Logging:** Automatically prints exact execution syntax codes into an active UI console feed, making quick manual command copy-pasting a breeze.

---

## 🛠️ Installation & Setup

Ensure you have [uv](https://astral.sh/uv) installed on your machine.

### For Developers (Building the Package)
If you want to compile and package changes to the repository:

1. Open a terminal inside the project directory.
2. Build the distribution wheel package:
   ```powershell
   uv build
    ```

*This bundles the workspace cleanly inside a local `dist/` directory.*

### For Your Friend (Installing the Executable)

To install the compiled `.whl` bundle directly as a standalone system program:

1. Open PowerShell inside the project directory.
2. Run the tool installation macro:
    ```powershell
    uv tool install dist/batchleaguereplays-0.4.0-py3-none-any.whl
    ```


3. Generate a fast Desktop Shortcut icon by running this single macro command:
    ```powershell
    $s = (New-Object -ComObject WScript.Shell).CreateShortcut("$Home\Desktop\BatchLeagueReplays.lnk"); $s.TargetPath = "$env:USERPROFILE\.local\bin\batchleaguereplays.exe"; $s.Save()
    ```



---

## 🕹️ How to Use
⚠️ **Important Patch Notice:** Due to how League of Legends handles game assets, replays are strictly locked to the patch they were played on. The app displays your current client patch version on startup. Attempting to download or launch a replay from an older patch will fail.

1. Launch your **League of Legends Client** and log into your account.
2. Double-click your new **BatchLeagueReplays** Desktop shortcut.
3. **To Grab a Single Replay:** Paste a known Match ID directly into the target box and click `Download Replay`.
4. **To Batch Browse History:** Click `Fetch and Spawn History Viewer`. A new window will pop up containing up to 100 scrollable, searchable matches displaying your match stats, game outcomes, and played champions.
5. **Download via Browsing:** Simply double-click any match item inside a history browser viewport to instantly trigger its replay download process in the background.

---

## 📂 Diagnostics & Cache Storage

* **System Logs:** Error configurations and diagnostic tracking arrays write live outputs to `app.log` in your current runtime working directory.
* **Match Backups:** Every historical query creates a unique JSON snapshot archive inside your user roaming path:
    ```text
    %APPDATA%\BatchLeagueReplays\
    ```
*(To jump here directly, press `Win + R`, paste the folder path above, and hit Enter).*

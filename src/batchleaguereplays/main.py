import os
import re
import sys
import json
import logging
import subprocess
from datetime import datetime
import requests
import urllib3
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QTextEdit, QLabel, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt

# Configure log file stream tracking
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Global variable container to store the ID-to-Name conversion map
CHAMPION_MAPPING = {}

def load_champion_data():
    """Fetches the latest champion ID-to-Name dictionary from Riot's Data Dragon."""
    global CHAMPION_MAPPING
    try:
        logging.info("Fetching latest champion mapping metadata from Data Dragon...")
        # Get the latest game version payload first
        version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
        version = requests.get(version_url, timeout=5).json()[0]
        
        # Pull down the complete champion data dictionary
        data_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
        response = requests.get(data_url, timeout=5).json()
        
        # Invert the dictionary data structural layout so we can look up by numeric key string
        for champ_name, champ_info in response.get("data", {}).items():
            key_id = int(champ_info.get("key"))
            CHAMPION_MAPPING[key_id] = champ_info.get("name")
            
        logging.info(f"Loaded mappings for {len(CHAMPION_MAPPING)} champions successfully.")
    except Exception as e:
        logging.error(f"Failed loading Data Dragon champion database context: {e}")

class MatchHistoryViewer(QWidget):
    """A standalone window that displays a specific JSON batch of matches."""
    def __init__(self, title, games_list, download_callback):
        super().__init__()
        self.games_list = games_list
        self.download_callback = download_callback
        self.setWindowTitle(title)
        self.setMinimumSize(550, 450)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.header = QLabel(f"Showing {len(self.games_list)} match records:")
        layout.addWidget(self.header)

        self.match_list_widget = QListWidget()
        layout.addWidget(self.match_list_widget)

        # Trigger downloads directly out of this dynamic sub-view instance
        self.match_list_widget.itemDoubleClicked.connect(self.download_selected)

        self.footer = QLabel("Double-click any game to send download command to LCU.")
        layout.addWidget(self.footer)

        self.setLayout(layout)
        self.populate_list()

    def populate_list(self):
        for match in self.games_list:
            game_id = match.get("gameId")
            game_mode = match.get("gameMode", "UNKNOWN")
            creation_date = match.get("gameCreationDate", "Unknown Date")[:10] 
            
            # Extract player specific index positions
            participants = match.get("participants", [{}])
            participant = participants[0] if participants else {}
            
            # LOOKUP CHAMPION ID HERE:
            champ_id = participant.get("championId", 0)
            champ_name = CHAMPION_MAPPING.get(champ_id, f"Unknown ({champ_id})")
            
            stats = participant.get("stats", {})
            kills = stats.get("kills", 0)
            deaths = stats.get("deaths", 0)
            assists = stats.get("assists", 0)
            win = "WIN" if stats.get("win") else "LOSS"

            # Add champ_name string straight into the window line output formatting!
            display_text = f"[{creation_date}] ID: {game_id} | {game_mode} ({win}) | {champ_name} - KDA: {kills}/{deaths}/{assists}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, game_id)
            self.match_list_widget.addItem(item)

    def download_selected(self, item):
        game_id = item.data(Qt.ItemDataRole.UserRole)
        if game_id:
            self.download_callback(str(game_id))


class ReplayDownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.spawned_windows = []  # Keeps secondary UI object references alive in RAM
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("League Replay Grabber Pro")
        self.setMinimumWidth(500)
        
        main_layout = QVBoxLayout()
        input_layout = QHBoxLayout()
        
        self.label = QLabel("Game ID:")
        self.match_id_input = QLineEdit()
        self.match_id_input.setPlaceholderText("Paste ID or browse history")
        
        self.download_btn = QPushButton("Download Replay")
        self.download_btn.clicked.connect(lambda: self.handle_download(self.match_id_input.text().strip()))
        
        input_layout.addWidget(self.label)
        input_layout.addWidget(self.match_id_input)
        input_layout.addWidget(self.download_btn)
        
        self.browse_btn = QPushButton("Fetch and Spawn History Viewer")
        self.browse_btn.clicked.connect(self.fetch_and_spawn_history)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.append("System ready.")
        
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.browse_btn)
        main_layout.addWidget(self.log_output)
        
        self.setLayout(main_layout)

    def log_message(self, message, level="info"):
        if level == "error":
            logging.error(message)
            self.log_output.append(f"<font color='red'>[Error] {message}</font>")
        elif level == "warning":
            logging.warning(message)
            self.log_output.append(f"<font color='orange'>[Warning] {message}</font>")
        else:
            logging.info(message)
            self.log_output.append(f"[Info] {message}")

    def get_client_credentials(self):
        try:
            output = subprocess.check_output(["powershell", "-Command", "(Get-CimInstance Win32_Process -Filter \"Name = 'LeagueClientUx.exe'\").CommandLine"], text=True)
            token = re.search(r'--remoting-auth-token=([^\s"]+)', output)
            port = re.search(r'--app-port=(\d+)', output)
            if token and port:
                return token.group(1), port.group(1)
        except Exception as e:
            self.log_message(f"Failed process scanning mapping: {e}", level="error")
        return None, None

    def fetch_and_spawn_history(self):
        token, port = self.get_client_credentials()
        if not token or not port:
            self.log_message("Cannot execute batch query without active client framework.", level="warning")
            return

        # Setup AppData target output paths cleanly
        appdata_dir = os.path.join(os.environ.get("APPDATA", ""), "BatchLeagueReplays")
        os.makedirs(appdata_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"matches_{timestamp}.json"
        target_file = os.path.join(appdata_dir, filename)
        
        # Hardcoding the index stretch boundary query to pull large scopes down at once
        url = f"https://127.0.0.1:{port}/lol-match-history/v1/products/lol/current-summoner/matches?begIndex=0&endIndex=100"
        
        curl_args = [
            "curl", "--insecure", 
            "--user", f"riot:{token}", 
            "-X", "GET", url
        ]
        
        self.log_message("Executing native curl subprocess snapshot data pull...")
        
        try:
            result = subprocess.run(curl_args, capture_output=True, text=True, check=True)
            raw_json = result.stdout
            
            # Save the backup dump directly into AppData for traceability
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(raw_json)
            
            self.log_message(f"Snapshot written to AppData file location: {filename}", level="info")
            
            # Parse the text string payload and spin up a dedicated, isolated viewer window context
            self.parse_and_spawn_viewer(raw_json, filename_context=filename)
            
        except subprocess.CalledProcessError as e:
            self.log_message(f"Native Windows curl executable threw a runtime error: {e.stderr}", level="error")
        except Exception as e:
            self.log_message(f"Failed parsing raw pipeline payload: {e}", level="error")

    def parse_and_spawn_viewer(self, raw_json_string, filename_context="Current Session"):
        try:
            data = json.loads(raw_json_string)
            matches = data.get("games", {}).get("games", [])
            
            if not matches:
                self.log_message(f"No match array index data located inside: {filename_context}", level="warning")
                return

            window_title = f"Match Records - {filename_context}"
            viewer = MatchHistoryViewer(window_title, matches, self.handle_download)
            
            # Append reference array pointer to prevent Python's garbage collector from deleting the UI reference
            self.spawned_windows.append(viewer)
            viewer.show()
            
            self.log_message(f"Successfully generated independent match viewport: {window_title}", level="info")
        except Exception as e:
            self.log_message(f"Failed rendering data target matrix structure: {e}", level="error")

    def handle_download(self, game_id):
        if not game_id:
            self.log_message("Replay download trigger attempted with empty Game ID text slot.", level="warning")
            return
            
        token, port = self.get_client_credentials()
        if not token or not port:
            self.log_message("Unable to run downloader; game client appears closed.", level="error")
            return
            
        url = f"https://127.0.0.1:{port}/lol-replays/v1/rofls/{game_id}/download/graceful"
        
        # Display the equivalent raw curl statement for quick copy/pasting if needed
        curl_cmd = f'curl --insecure --user "riot:{token}" -X POST "{url}" -H "Content-Type: application/json" -d "{{}}"'
        logging.info(f"Manual Execution Syntax: {curl_cmd}")
        self.log_output.append(f"<font color='cyan'><code>{curl_cmd}</code></font>")
        
        self.log_message(f"Sending background POST fetch request for match ID: {game_id}...")
        
        try:
            response = requests.post(url, auth=("riot", token), headers={"Content-Type": "application/json"}, json={}, verify=False)
            if response.status_code in [200, 204]:
                self.log_message(f"Download command accepted by client endpoint for ID {game_id}!", level="info")
            else:
                self.log_message(f"LCU rejected target request tracking payload. Code {response.status_code}: {response.text}", level="error")
        except Exception as e:
            self.log_message(f"Network crash executing POST command sequence: {e}", level="error")


def run_app():
    logging.info("Starting League Replay Grabber Application Instance.")
    app = QApplication(sys.argv)
    
    load_champion_data()
    
    window = ReplayDownloaderApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
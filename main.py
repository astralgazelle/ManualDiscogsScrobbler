import sys

APP_VERSION = "0.1"

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox
)
from PySide6.QtCore import Qt

from api_clients import ApiClients
import config

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Last.fm login")

        self.lastfm_user = QLineEdit()
        self.lastfm_pass = QLineEdit()
        self.lastfm_pass.setEchoMode(QLineEdit.Password)

        form_layout = QFormLayout()
        form_layout.addRow("Username:", self.lastfm_user)
        form_layout.addRow("Password:", self.lastfm_pass)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

    def get_data(self):
        return (self.lastfm_user.text(), self.lastfm_pass.text())


class ScrobblerApp(QMainWindow):
    def __init__(self, api_handler: ApiClients):
        super().__init__()
        self.api_handler = api_handler
        self.setWindowTitle(f"Manual Discogs Scrobbler v{APP_VERSION}")
        self.setGeometry(100, 100, 800, 600)

        self.release_id_input = QLineEdit()
        self.release_id_input.setPlaceholderText("Enter full release ID, e.g. [r123456789]")
        
        self.fetch_button = QPushButton("IMPORT")
        self.clear_button = QPushButton("CLEAR")
        self.scrobble_button = QPushButton("SCROBBLE")
        
        self.artist_label = QLabel("<b>ALBUM ARTIST:</b>")
        self.album_label = QLabel("<b>ALBUM:</b>")
        
        self.track_table = QTableWidget()
        self.track_table.setColumnCount(4)
        self.track_table.setHorizontalHeaderLabels(["", "#", "TITLE", "DURATION"])
        self.track_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.track_table.setColumnWidth(0, 50)
        self.track_table.setColumnWidth(1, 50)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.release_id_input)
        input_layout.addWidget(self.fetch_button)
        input_layout.addWidget(self.clear_button)

        info_layout = QVBoxLayout()
        info_layout.addWidget(self.artist_label)
        info_layout.addWidget(self.album_label)
        
        main_layout.addLayout(input_layout)
        main_layout.addLayout(info_layout)
        main_layout.addWidget(self.track_table)
        main_layout.addWidget(self.scrobble_button)
        
        self.setCentralWidget(central_widget)
        
        self.artist_name = ""
        self.album_title = ""
        self.fetch_button.clicked.connect(self.fetch_release_data)
        self.scrobble_button.clicked.connect(self.scrobble_tracks)
        self.clear_button.clicked.connect(self.clear_data) # ZMIANA 1: Połączenie przycisku z funkcją

    def clear_data(self):
        self.release_id_input.clear()
        self.artist_label.setText("<b>ALBUM ARTIST:</b>")
        self.album_label.setText("<b>ALBUM:</b>")
        self.track_table.setRowCount(0)
        self.artist_name = ""
        self.album_title = ""

    def fetch_release_data(self):
        raw_text = self.release_id_input.text().strip()
        release_id = raw_text.replace('r', '').replace('[', '').replace(']', '')

        if not release_id.isdigit():
            QMessageBox.warning(self, "ERROR", "Incorrect release ID format.")
            return

        data = self.api_handler.get_discogs_release(release_id)

        if data:
            self.artist_name, self.album_title = data['artist'], data['album']
            self.artist_label.setText(f"<b>ALBUM ARTIST:</b> {self.artist_name}")
            self.album_label.setText(f"<b>ALBUM:</b> {self.album_title}")
            self.populate_table(data['tracks'])
        else:
            QMessageBox.critical(self, "ERROR", "Couldn't download metadata - please check the release ID.")

    def populate_table(self, tracklist):
        self.track_table.setRowCount(len(tracklist))
        for row, track in enumerate(tracklist):
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            check_item.setCheckState(Qt.Checked)
            pos_item = QTableWidgetItem(track['position'])
            title_item = QTableWidgetItem(track['title'])
            duration_item = QTableWidgetItem(track['duration'])
            duration_item.setFlags(duration_item.flags() & ~Qt.ItemIsEditable)
            self.track_table.setItem(row, 0, check_item)
            self.track_table.setItem(row, 1, pos_item)
            self.track_table.setItem(row, 2, title_item)
            self.track_table.setItem(row, 3, duration_item)

    def scrobble_tracks(self):
        if not self.artist_name:
            QMessageBox.warning(self, "NO DATA", "Please import metadata first.")
            return

        tracks_to_scrobble = []
        for row in range(self.track_table.rowCount()):
            if self.track_table.item(row, 0).checkState() == Qt.Checked:
                title = self.track_table.item(row, 2).text()
                duration_str = self.track_table.item(row, 3).text()
                duration_sec = 0
                if duration_str and ':' in duration_str:
                    try:
                        parts = duration_str.split(':')
                        duration_sec = int(parts[0]) * 60 + int(parts[1])
                    except (ValueError, IndexError):
                        duration_sec = 180
                tracks_to_scrobble.append({'title': title, 'duration': duration_sec})

        if not tracks_to_scrobble:
            QMessageBox.information(self, "INFORMATION", "No tracks selected to scrobble.")
            return

        self.api_handler.scrobble_to_lastfm(self.artist_name, self.album_title, tracks_to_scrobble)
        QMessageBox.information(self, "SUCCESS", "Scrobbling process completed.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    user_credentials = config.load_config()
    
    if user_credentials is None:
        dialog = SettingsDialog()
        if dialog.exec() == QDialog.Accepted:
            config.save_config(*dialog.get_data())
            user_credentials = config.load_config()
        else:
            sys.exit()

    if user_credentials is None:
        QMessageBox.critical(None, "ERROR", "No user data found. The application will now close.")
        sys.exit()

    try:
        api_handler = ApiClients(lastfm_username=user_credentials[0], lastfm_password=user_credentials[1])
        window = ScrobblerApp(api_handler)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "ERROR", f"A critical error occurred: {e}\nPlease check your login details.")
        import os
        if os.path.exists(config.CONFIG_FILE):
            os.remove(config.CONFIG_FILE)
        sys.exit()
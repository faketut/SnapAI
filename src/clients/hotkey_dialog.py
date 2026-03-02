from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QMessageBox)
from PyQt5.QtCore import Qt

class HotkeyConfigDialog(QDialog):
    """Dialog for configuring application hotkeys in real-time"""
    
    def __init__(self, hotkey_manager, parent=None):
        super().__init__(parent)
        self.hotkey_manager = hotkey_manager
        self.inputs = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("SnapAI Hotkey Configuration")
        self.setFixedWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1117;
                color: #f0f6fc;
            }
            QLabel {
                color: #f0f6fc;
            }
            QLineEdit {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 5px;
                color: #f0f6fc;
            }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px 16px;
                color: #c9d1d9;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #8b949e;
            }
            QPushButton#saveButton {
                background-color: #238636;
                color: #ffffff;
                border-color: rgba(240, 246, 252, 0.1);
            }
            QPushButton#saveButton:hover {
                background-color: #2ea043;
            }
        """)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Create inputs for each hotkey
        for action in self.hotkey_manager.hotkeys.keys():
            label_text = action.replace('_', ' ').title()
            current_key = self.hotkey_manager.get_hotkey(action)
            
            line_edit = QLineEdit(current_key)
            line_edit.setPlaceholderText("e.g. f7, ctrl+f7")
            
            self.inputs[action] = line_edit
            form_layout.addRow(label_text + ":", line_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save & Apply")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)

    def get_configured_hotkeys(self):
        """Returns a dict of the new hotkey settings"""
        return {action: input_field.text().strip() for action, input_field in self.inputs.items()}

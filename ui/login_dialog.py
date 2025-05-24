from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QSpinBox, QCheckBox, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.browser import Browser
from utils.logger import Logger

class LoginWidget(QWidget):
    """
    로그인 정보 입력을 위한 공통 위젯
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 로그인 정보 입력 영역
        form_layout = QVBoxLayout()
        
        # 아이디 입력
        id_layout = QHBoxLayout()
        id_label = QLabel("아이디:")
        self.id_input = QLineEdit()
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_input)
        
        # 비밀번호 입력
        pw_layout = QHBoxLayout()
        pw_label = QLabel("비밀번호:")
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.Password)
        pw_layout.addWidget(pw_label)
        pw_layout.addWidget(self.pw_input)
        
        # 로그인 정보 저장 체크박스
        self.save_login_checkbox = QCheckBox("로그인 정보 저장")
        
        form_layout.addLayout(id_layout)
        form_layout.addLayout(pw_layout)
        form_layout.addWidget(self.save_login_checkbox)
        
        layout.addLayout(form_layout)
        self.setLayout(layout)
        
    def get_credentials(self):
        """로그인 정보 반환"""
        return {
            "username": self.id_input.text(),
            "password": self.pw_input.text(),
            "save": self.save_login_checkbox.isChecked()
        }
        
    def set_credentials(self, username, password, save=False):
        """로그인 정보 설정"""
        self.id_input.setText(username)
        self.pw_input.setText(password)
        self.save_login_checkbox.setChecked(save)

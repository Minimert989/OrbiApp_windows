from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QSpinBox, QGroupBox, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.login_dialog import LoginWidget
from utils.browser import Browser
from utils.logger import Logger

class CommenterWorker(QThread):
    """
    댓글 작성 작업을 수행하는 워커 스레드
    """
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, username, password, article_number, comment_text, num_comments):
        super().__init__()
        self.username = username
        self.password = password
        self.article_number = article_number
        self.comment_text = comment_text
        self.num_comments = num_comments
        self.logger = Logger()
        self.running = True
        
    def run(self):
        """스레드 실행"""
        self.update_signal.emit("댓글 작성 작업을 시작합니다...")
        
        # 브라우저 초기화
        browser = Browser(headless=True)
        if not browser.start():
            self.finished_signal.emit(False, "브라우저를 시작할 수 없습니다.")
            return
            
        try:
            driver = browser.get_driver()
            
            # 로그인
            self.update_signal.emit("오르비 로그인 중...")
            browser.get("https://login.orbi.kr/login")
            
            # 아이디/비밀번호 입력
            driver.find_element("name", "username").send_keys(self.username)
            driver.find_element("name", "password").send_keys(self.password)
            driver.find_element("name", "password").send_keys("\n")
            time.sleep(3)
            
            # 로그인 성공 확인
            if "login" in driver.current_url:
                self.finished_signal.emit(False, "로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.")
                browser.stop()
                return
                
            self.update_signal.emit("로그인 성공!")
            
            # 게시글 페이지로 이동
            article_url = f"https://orbi.kr/{self.article_number}"
            self.update_signal.emit(f"게시글 페이지로 이동 중... ({article_url})")
            browser.get(article_url)
            time.sleep(3)
            
            # 게시글 존재 확인
            if "error" in driver.current_url or "404" in driver.page_source:
                self.finished_signal.emit(False, f"게시글을 찾을 수 없습니다: {self.article_number}")
                browser.stop()
                return
                
            # 댓글 작성
            for i in range(self.num_comments):
                if not self.running:
                    self.finished_signal.emit(False, "사용자에 의해 중단되었습니다.")
                    browser.stop()
                    return
                    
                try:
                    self.update_signal.emit(f"댓글 {i+1}/{self.num_comments} 작성 중...")
                    
                    # 댓글 입력 필드 찾기
                    comment_area = driver.find_element("name", "content")
                    comment_area.click()
                    time.sleep(1)
                    
                    # 댓글 내용 입력
                    comment_area.clear()
                    comment_area.send_keys(self.comment_text)
                    
                    # 게시 버튼 클릭
                    post_button = driver.find_element("class name", "send")
                    post_button.click()
                    
                    self.update_signal.emit(f"댓글 {i+1}/{self.num_comments} 작성 완료!")
                    time.sleep(2)  # 댓글 작성 간 딜레이
                    
                except Exception as e:
                    self.update_signal.emit(f"댓글 {i+1}/{self.num_comments} 작성 중 오류 발생: {e}")
                    time.sleep(2)  # 오류 발생 시 잠시 대기
                    
            self.finished_signal.emit(True, f"{self.num_comments}개의 댓글 작성이 완료되었습니다.")
                
        except Exception as e:
            self.finished_signal.emit(False, f"댓글 작성 중 오류 발생: {e}")
        finally:
            browser.stop()
            
    def stop(self):
        """작업 중단"""
        self.running = False

class CommenterWidget(QWidget):
    """
    댓글 작성 기능을 위한 위젯
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        self.worker = None
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 로그인 위젯
        login_group = QGroupBox("로그인 정보")
        self.login_widget = LoginWidget()
        login_layout = QVBoxLayout()
        login_layout.addWidget(self.login_widget)
        login_group.setLayout(login_layout)
        
        # 댓글 설정
        settings_group = QGroupBox("댓글 설정")
        settings_layout = QVBoxLayout()
        
        # 게시글 번호
        article_layout = QHBoxLayout()
        article_label = QLabel("게시글 번호:")
        self.article_input = QLineEdit()
        article_layout.addWidget(article_label)
        article_layout.addWidget(self.article_input)
        
        # 댓글 내용
        comment_layout = QHBoxLayout()
        comment_label = QLabel("댓글 내용:")
        self.comment_input = QTextEdit()
        self.comment_input.setMaximumHeight(100)
        comment_layout.addWidget(comment_label)
        comment_layout.addWidget(self.comment_input)
        
        # 댓글 수
        count_layout = QHBoxLayout()
        count_label = QLabel("댓글 수:")
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setMinimum(1)
        self.count_spinbox.setMaximum(100)
        self.count_spinbox.setValue(1)
        count_layout.addWidget(count_label)
        count_layout.addWidget(self.count_spinbox)
        
        settings_layout.addLayout(article_layout)
        settings_layout.addLayout(comment_layout)
        settings_layout.addLayout(count_layout)
        settings_group.setLayout(settings_layout)
        
        # 실행 버튼
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("댓글 작성 시작")
        self.start_button.clicked.connect(self.start_commenter)
        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_commenter)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        
        # 로그 출력 영역
        log_group = QGroupBox("실행 로그")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        # 레이아웃 구성
        layout.addWidget(login_group)
        layout.addWidget(settings_group)
        layout.addLayout(button_layout)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
        
    def log(self, message):
        """로그 출력"""
        from datetime import datetime
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.logger.info(message)
        
    def start_commenter(self):
        """댓글 작성 시작"""
        # 로그인 정보 확인
        credentials = self.login_widget.get_credentials()
        if not credentials["username"] or not credentials["password"]:
            QMessageBox.warning(self, "경고", "아이디와 비밀번호를 입력해주세요.")
            return
            
        # 게시글 번호 확인
        article_number = self.article_input.text().strip()
        if not article_number:
            QMessageBox.warning(self, "경고", "게시글 번호를 입력해주세요.")
            return
            
        # 댓글 내용 확인
        comment_text = self.comment_input.toPlainText().strip()
        if not comment_text:
            QMessageBox.warning(self, "경고", "댓글 내용을 입력해주세요.")
            return
            
        # 댓글 수 확인
        num_comments = self.count_spinbox.value()
        
        # UI 상태 변경
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 로그 초기화
        self.log_text.clear()
        self.log(f"댓글 작성 작업 준비 중... (게시글: {article_number}, 댓글 수: {num_comments})")
        
        # 워커 스레드 시작
        self.worker = CommenterWorker(
            credentials["username"],
            credentials["password"],
            article_number,
            comment_text,
            num_comments
        )
        self.worker.update_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_commenter_finished)
        self.worker.start()
        
    def stop_commenter(self):
        """댓글 작성 중지"""
        if self.worker and self.worker.isRunning():
            self.log("댓글 작성 중지 요청...")
            self.worker.stop()
            
    def on_commenter_finished(self, success, message):
        """댓글 작성 완료 처리"""
        if success:
            self.log(f"✅ {message}")
        else:
            self.log(f"❌ {message}")
            
        # UI 상태 복원
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

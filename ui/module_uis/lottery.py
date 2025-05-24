from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QSpinBox, QGroupBox, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.login_dialog import LoginWidget
from utils.browser import Browser
from utils.logger import Logger

class LotteryWorker(QThread):
    """
    복권 구매 작업을 수행하는 워커 스레드
    """
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, username, password, num_clicks):
        super().__init__()
        self.username = username
        self.password = password
        self.num_clicks = num_clicks
        self.logger = Logger()
        self.running = True
        
    def run(self):
        """스레드 실행"""
        self.update_signal.emit(f"복권 구매 작업을 시작합니다... (클릭 횟수: {self.num_clicks})")
        
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
            
            # 복권 페이지로 이동
            self.update_signal.emit("복권 페이지로 이동 중...")
            browser.get("https://orbi.kr/amusement/lottery")
            time.sleep(3)
            
            # 복권 클릭
            success_count = 0
            for i in range(self.num_clicks):
                if not self.running:
                    self.finished_signal.emit(False, "사용자에 의해 중단되었습니다.")
                    browser.stop()
                    return
                    
                try:
                    self.update_signal.emit(f"복권 클릭 {i+1}/{self.num_clicks} 시도 중...")
                    
                    # 풍선 요소 찾기
                    balloon = driver.find_element("class name", "balloon")
                    balloon.click()
                    time.sleep(1)
                    
                    # 알림창 처리
                    try:
                        alert = driver.switch_to.alert
                        alert_text = alert.text
                        alert.accept()
                        self.update_signal.emit(f"알림창 처리: {alert_text}")
                    except:
                        pass
                        
                    success_count += 1
                    self.update_signal.emit(f"복권 클릭 {i+1}/{self.num_clicks} 성공!")
                    time.sleep(2)  # 클릭 간 딜레이
                    
                except Exception as e:
                    self.update_signal.emit(f"복권 클릭 {i+1}/{self.num_clicks} 실패: {e}")
                    time.sleep(2)  # 오류 발생 시 잠시 대기
                    
            self.finished_signal.emit(True, f"복권 구매 작업이 완료되었습니다. {success_count}/{self.num_clicks}회 성공했습니다.")
                
        except Exception as e:
            self.finished_signal.emit(False, f"복권 구매 중 오류 발생: {e}")
        finally:
            browser.stop()
            
    def stop(self):
        """작업 중단"""
        self.running = False

class LotteryWidget(QWidget):
    """
    복권 구매 기능을 위한 위젯
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
        
        # 복권 설정
        settings_group = QGroupBox("복권 설정")
        settings_layout = QVBoxLayout()
        
        # 클릭 횟수
        clicks_layout = QHBoxLayout()
        clicks_label = QLabel("클릭 횟수:")
        self.clicks_spinbox = QSpinBox()
        self.clicks_spinbox.setMinimum(1)
        self.clicks_spinbox.setMaximum(100)
        self.clicks_spinbox.setValue(5)
        clicks_layout.addWidget(clicks_label)
        clicks_layout.addWidget(self.clicks_spinbox)
        
        settings_layout.addLayout(clicks_layout)
        settings_group.setLayout(settings_layout)
        
        # 실행 버튼
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("복권 구매 시작")
        self.start_button.clicked.connect(self.start_lottery)
        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_lottery)
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
        
    def start_lottery(self):
        """복권 구매 시작"""
        # 로그인 정보 확인
        credentials = self.login_widget.get_credentials()
        if not credentials["username"] or not credentials["password"]:
            QMessageBox.warning(self, "경고", "아이디와 비밀번호를 입력해주세요.")
            return
            
        # 클릭 횟수 확인
        num_clicks = self.clicks_spinbox.value()
        
        # UI 상태 변경
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 로그 초기화
        self.log_text.clear()
        self.log(f"복권 구매 작업 준비 중... (클릭 횟수: {num_clicks})")
        
        # 워커 스레드 시작
        self.worker = LotteryWorker(
            credentials["username"],
            credentials["password"],
            num_clicks
        )
        self.worker.update_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_lottery_finished)
        self.worker.start()
        
    def stop_lottery(self):
        """복권 구매 중지"""
        if self.worker and self.worker.isRunning():
            self.log("복권 구매 중지 요청...")
            self.worker.stop()
            
    def on_lottery_finished(self, success, message):
        """복권 구매 완료 처리"""
        if success:
            self.log(f"✅ {message}")
        else:
            self.log(f"❌ {message}")
            
        # UI 상태 복원
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

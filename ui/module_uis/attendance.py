from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QTimeEdit, QGroupBox, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTime
import os
import sys
import time
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.login_dialog import LoginWidget
from utils.browser import Browser
from utils.logger import Logger

class AttendanceWorker(QThread):
    """
    출석 체크 작업을 수행하는 워커 스레드
    """
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, username, password, message="q", target_time=None):
        super().__init__()
        self.username = username
        self.password = password
        self.message = message
        self.target_time = target_time
        self.logger = Logger()
        self.running = True
        
    def run(self):
        """스레드 실행"""
        self.update_signal.emit("출석 체크 작업을 시작합니다...")
        
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
            
            # 출석 페이지로 이동
            self.update_signal.emit("출석 페이지로 이동 중...")
            browser.get("https://orbi.kr/amusement/attendance")
            time.sleep(2)
            
            # 출석 메시지 입력
            try:
                input_box = driver.find_element("css selector", ".greets-wrap .input-wrap")
                input_box.send_keys(self.message)
                self.update_signal.emit(f"출석 메시지 입력 완료: {self.message}")
            except Exception as e:
                self.update_signal.emit(f"출석 메시지 입력 중 오류 발생: {e}")
                
            # 목표 시간까지 대기
            if self.target_time:
                now = datetime.now()
                target = datetime.combine(now.date(), self.target_time)
                
                # 목표 시간이 현재보다 이전이면 다음 날로 설정
                if target < now:
                    target = datetime.combine(now.date() + timedelta(days=1), self.target_time)
                    
                wait_seconds = (target - now).total_seconds()
                self.update_signal.emit(f"목표 시간({target.strftime('%H:%M:%S')})까지 {wait_seconds:.1f}초 대기 중...")
                
                # 1초 단위로 업데이트하며 대기
                while wait_seconds > 0 and self.running:
                    time.sleep(1)
                    wait_seconds -= 1
                    if wait_seconds % 10 == 0 or wait_seconds < 10:  # 10초마다 또는 10초 미만일 때 업데이트
                        self.update_signal.emit(f"목표 시간까지 {wait_seconds:.1f}초 남음...")
                        
            # 중단되었는지 확인
            if not self.running:
                self.finished_signal.emit(False, "사용자에 의해 중단되었습니다.")
                browser.stop()
                return
                
            # 출석 버튼 클릭
            try:
                submit_button = driver.find_element("css selector", ".greets-wrap button.submit")
                submit_button.click()
                self.update_signal.emit("출석 버튼 클릭 완료!")
                time.sleep(2)
                
                # 결과 확인
                self.update_signal.emit("출석 체크 결과 확인 중...")
                # 여기서 출석 성공 여부를 확인하는 로직 추가 (페이지 내용 분석 등)
                
                self.finished_signal.emit(True, "출석 체크가 완료되었습니다.")
            except Exception as e:
                self.finished_signal.emit(False, f"출석 버튼 클릭 중 오류 발생: {e}")
                
        except Exception as e:
            self.finished_signal.emit(False, f"출석 체크 중 오류 발생: {e}")
        finally:
            browser.stop()
            
    def stop(self):
        """작업 중단"""
        self.running = False

class AttendanceWidget(QWidget):
    """
    출석 체크 기능을 위한 위젯
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
        
        # 출석 설정
        settings_group = QGroupBox("출석 설정")
        settings_layout = QVBoxLayout()
        
        # 출석 메시지
        message_layout = QHBoxLayout()
        message_label = QLabel("출석 메시지:")
        self.message_input = QLineEdit("q")  # 기본값 "q"
        message_layout.addWidget(message_label)
        message_layout.addWidget(self.message_input)
        
        # 출석 시간
        time_layout = QHBoxLayout()
        time_label = QLabel("출석 시간:")
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(0, 0, 0))  # 기본값 00:00:00 (자정)
        self.time_edit.setDisplayFormat("HH:mm:ss")
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_edit)
        
        settings_layout.addLayout(message_layout)
        settings_layout.addLayout(time_layout)
        settings_group.setLayout(settings_layout)
        
        # 실행 버튼
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("출석 체크 시작")
        self.start_button.clicked.connect(self.start_attendance)
        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_attendance)
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
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.logger.info(message)
        
    def start_attendance(self):
        """출석 체크 시작"""
        # 로그인 정보 확인
        credentials = self.login_widget.get_credentials()
        if not credentials["username"] or not credentials["password"]:
            QMessageBox.warning(self, "경고", "아이디와 비밀번호를 입력해주세요.")
            return
            
        # 출석 메시지 확인
        message = self.message_input.text()
        if not message:
            message = "q"  # 기본값
            
        # 출석 시간 설정
        target_time = self.time_edit.time().toPyTime()
        
        # UI 상태 변경
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 로그 초기화
        self.log_text.clear()
        self.log(f"출석 체크 작업 준비 중... (목표 시간: {target_time.strftime('%H:%M:%S')})")
        
        # 워커 스레드 시작
        self.worker = AttendanceWorker(
            credentials["username"],
            credentials["password"],
            message,
            target_time
        )
        self.worker.update_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_attendance_finished)
        self.worker.start()
        
    def stop_attendance(self):
        """출석 체크 중지"""
        if self.worker and self.worker.isRunning():
            self.log("출석 체크 중지 요청...")
            self.worker.stop()
            
    def on_attendance_finished(self, success, message):
        """출석 체크 완료 처리"""
        if success:
            self.log(f"✅ {message}")
        else:
            self.log(f"❌ {message}")
            
        # UI 상태 복원
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QGroupBox, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
import sys
import time
import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import Logger

class IminScraperWorker(QThread):
    """
    아이민 글 제목 추출 작업을 수행하는 워커 스레드
    """
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, str)  # 성공 여부, 메시지, 결과 파일 경로
    
    def __init__(self, imin_number, save_path):
        super().__init__()
        self.imin_number = imin_number
        self.save_path = save_path
        self.logger = Logger()
        self.running = True
        
    def run(self):
        """스레드 실행"""
        self.update_signal.emit(f"아이민 {self.imin_number}의 글 제목 추출 작업을 시작합니다...")
        
        try:
            base_url = "https://orbi.kr/search"
            page = 1
            titles = []
            
            while self.running:
                # 검색 파라미터 구성
                params = {
                    "type": "imin",
                    "q": self.imin_number,
                    "page": page
                }
                
                self.update_signal.emit(f"페이지 {page} 가져오는 중...")
                
                # GET 요청
                response = requests.get(base_url, params=params)
                if response.status_code != 200:
                    self.update_signal.emit(f"페이지 {page} 가져오기 실패. HTTP 상태 코드: {response.status_code}")
                    break
                    
                # HTML 파싱
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 'post-list' 클래스 컨테이너 찾기
                post_list = soup.find("ul", class_="post-list")
                if not post_list:
                    self.update_signal.emit("더 이상 'post-list'를 찾을 수 없습니다. 중지합니다.")
                    break
                    
                # 모든 리스트 아이템 찾기
                list_items = post_list.find_all("li")
                
                # 'notice' 클래스가 있는 첫 3개 항목 제외
                valid_posts = [
                    li for li in list_items
                    if "notice" not in li.get("class", [])
                ][3:]  # 첫 3개 유효 게시물 건너뛰기
                
                # 'title' 클래스가 있는 <p> 태그에서 제목 추출
                page_titles = [
                    post.find("p", class_="title").text.strip()
                    for post in valid_posts
                    if post.find("p", class_="title")
                ]
                
                # 유효한 제목이 없으면 중지
                if not page_titles:
                    self.update_signal.emit("이 페이지에서 제목을 찾을 수 없습니다. 중지합니다.")
                    break
                    
                # 빈 제목 필터링하고 리스트에 추가
                titles.extend([title for title in page_titles if title])
                self.update_signal.emit(f"페이지 {page}에서 {len(page_titles)}개의 제목을 찾았습니다.")
                
                page += 1  # 다음 페이지로 이동
                time.sleep(1)  # 요청 간 딜레이
                
                # 중단 요청 확인
                if not self.running:
                    self.update_signal.emit("사용자에 의해 중단되었습니다.")
                    break
                    
            # 결과를 텍스트 파일로 저장
            if titles:
                try:
                    with open(self.save_path, "w", encoding="utf-8") as file:
                        file.write("\n".join(titles))
                    self.update_signal.emit(f"총 {len(titles)}개의 제목을 {self.save_path}에 저장했습니다.")
                    self.finished_signal.emit(True, f"총 {len(titles)}개의 제목 추출 완료", self.save_path)
                except Exception as e:
                    self.finished_signal.emit(False, f"파일 저장 중 오류 발생: {e}", "")
            else:
                self.finished_signal.emit(False, "추출된 제목이 없습니다.", "")
                
        except Exception as e:
            self.finished_signal.emit(False, f"제목 추출 중 오류 발생: {e}", "")
            
    def stop(self):
        """작업 중단"""
        self.running = False

class IminScraperWidget(QWidget):
    """
    아이민 글 제목 추출 기능을 위한 위젯
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        self.worker = None
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 아이민 설정
        settings_group = QGroupBox("아이민 설정")
        settings_layout = QVBoxLayout()
        
        # 아이민 번호
        imin_layout = QHBoxLayout()
        imin_label = QLabel("아이민 번호:")
        self.imin_input = QLineEdit()
        imin_layout.addWidget(imin_label)
        imin_layout.addWidget(self.imin_input)
        
        # 저장 경로
        path_layout = QHBoxLayout()
        path_label = QLabel("저장 경로:")
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.browse_button = QPushButton("찾아보기")
        self.browse_button.clicked.connect(self.browse_save_path)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        
        settings_layout.addLayout(imin_layout)
        settings_layout.addLayout(path_layout)
        settings_group.setLayout(settings_layout)
        
        # 실행 버튼
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("제목 추출 시작")
        self.start_button.clicked.connect(self.start_scraper)
        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_scraper)
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
        layout.addWidget(settings_group)
        layout.addLayout(button_layout)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
        
    def log(self, message):
        """로그 출력"""
        from datetime import datetime
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.logger.info(message)
        
    def browse_save_path(self):
        """저장 경로 선택"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "저장 경로 선택",
            os.path.expanduser("~/Desktop"),
            "텍스트 파일 (*.txt)",
            options=options
        )
        
        if file_path:
            # 확장자가 없으면 .txt 추가
            if not file_path.endswith('.txt'):
                file_path += '.txt'
            self.path_input.setText(file_path)
        
    def start_scraper(self):
        """제목 추출 시작"""
        # 아이민 번호 확인
        imin_number = self.imin_input.text().strip()
        if not imin_number:
            QMessageBox.warning(self, "경고", "아이민 번호를 입력해주세요.")
            return
            
        # 저장 경로 확인
        save_path = self.path_input.text().strip()
        if not save_path:
            # 기본 저장 경로 설정
            save_path = os.path.join(os.path.expanduser("~"), f"{imin_number}_log.txt")
            self.path_input.setText(save_path)
            
        # UI 상태 변경
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 로그 초기화
        self.log_text.clear()
        self.log(f"아이민 {imin_number}의 글 제목 추출 작업 준비 중...")
        
        # 워커 스레드 시작
        self.worker = IminScraperWorker(imin_number, save_path)
        self.worker.update_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_scraper_finished)
        self.worker.start()
        
    def stop_scraper(self):
        """제목 추출 중지"""
        if self.worker and self.worker.isRunning():
            self.log("제목 추출 중지 요청...")
            self.worker.stop()
            
    def on_scraper_finished(self, success, message, file_path):
        """제목 추출 완료 처리"""
        if success:
            self.log(f"✅ {message}")
            # 파일 열기 옵션 제공
            reply = QMessageBox.question(
                self,
                "완료",
                f"{message}\n\n결과 파일을 열어보시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # 플랫폼에 따라 파일 열기
                if sys.platform == 'win32':
                    os.startfile(file_path)
                elif sys.platform == 'darwin':  # macOS
                    import subprocess
                    subprocess.call(['open', file_path])
                else:  # Linux
                    import subprocess
                    subprocess.call(['xdg-open', file_path])
        else:
            self.log(f"❌ {message}")
            
        # UI 상태 복원
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

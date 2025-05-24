from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QSpinBox, QGroupBox, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
import sys
import time
import requests
from datetime import datetime

# 최신 Selenium API를 위한 import 추가
from selenium.webdriver.common.by import By

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.login_dialog import LoginWidget
from utils.browser import Browser
from utils.logger import Logger

class ImageDownloaderWorker(QThread):
    """
    이미지 다운로드 작업을 수행하는 워커 스레드
    """
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, str)  # 성공 여부, 메시지, 다운로드 폴더 경로
    
    def __init__(self, run_time_minutes, download_dir):
        super().__init__()
        self.run_time_minutes = run_time_minutes
        self.download_dir = download_dir
        self.logger = Logger()
        self.running = True
        
    def run(self):
        """스레드 실행"""
        self.update_signal.emit(f"이미지 다운로드 작업을 시작합니다... (실행 시간: {self.run_time_minutes}분)")
        
        # 다운로드 디렉토리 생성
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 브라우저 초기화
        browser = Browser(headless=True)
        if not browser.start():
            self.finished_signal.emit(False, "브라우저를 시작할 수 없습니다.", self.download_dir)
            return
            
        try:
            driver = browser.get_driver()
            base_url = "https://orbi.kr/list"
            visited_urls = set()
            start_time = time.time()
            run_time_seconds = self.run_time_minutes * 60
            downloaded_count = 0
            
            while time.time() - start_time < run_time_seconds and self.running:
                # 남은 시간 계산
                elapsed_seconds = time.time() - start_time
                remaining_seconds = run_time_seconds - elapsed_seconds
                remaining_minutes = remaining_seconds / 60
                
                self.update_signal.emit(f"게시글 목록 페이지 로드 중... (남은 시간: {remaining_minutes:.1f}분)")
                browser.get(base_url)
                time.sleep(2)
                
                try:
                    # 게시글 목록에서 공지사항이 아닌 항목 찾기
                    # 수정: find_elements_by_css_selector -> find_elements(By.CSS_SELECTOR, ...)
                    articles = driver.find_elements(By.CSS_SELECTOR, "ul.post-list > li:not(.notice)")
                    
                    if not articles:
                        self.update_signal.emit("게시글을 찾을 수 없습니다. 다시 시도합니다.")
                        time.sleep(3)
                        continue
                        
                    self.update_signal.emit(f"{len(articles)}개의 게시글을 찾았습니다.")
                    
                    # 각 게시글 처리
                    for article in articles:
                        if not self.running or time.time() - start_time >= run_time_seconds:
                            break
                            
                        try:
                            # 게시글 링크 가져오기
                            # 수정: find_element_by_css_selector -> find_element(By.CSS_SELECTOR, ...)
                            title_element = article.find_element(By.CSS_SELECTOR, "p.title a")
                            link = title_element.get_attribute("href")
                            
                            # 이미 방문한 링크 건너뛰기
                            if not link or link in visited_urls:
                                continue
                                
                            visited_urls.add(link)  # 방문 표시
                            
                            # 게시글 방문
                            self.update_signal.emit(f"게시글 방문 중: {link}")
                            browser.get(link)
                            time.sleep(2)
                            
                            # 게시글 내용에서 이미지 찾기
                            # Selenium explicit wait을 사용하여 content-wrap 및 이미지 로드 대기
                            from selenium.webdriver.support.ui import WebDriverWait
                            from selenium.webdriver.support import expected_conditions as EC

                            content_wrap = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "content-wrap"))
                            )

                            WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".content-wrap img"))
                            )

                            images = content_wrap.find_elements(By.TAG_NAME, "img")
                            
                            if not images:
                                self.update_signal.emit("이미지가 없는 게시글입니다.")
                                continue
                                
                            self.update_signal.emit(f"{len(images)}개의 이미지를 찾았습니다.")
                            
                            # 이미지 다운로드
                            article_id = link.split('/')[-1]
                            for idx, img in enumerate(images):
                                if not self.running:
                                    break
                                    
                                img_url = img.get_attribute("src")
                                if not img_url:
                                    continue
                                    
                                # 이미지 파일명 생성
                                file_ext = img_url.split('.')[-1].split('?')[0]
                                if file_ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                                    file_ext = 'jpg'  # 기본 확장자
                                    
                                save_path = os.path.join(self.download_dir, f"{article_id}_img{idx}.{file_ext}")
                                
                                # 이미지 다운로드
                                try:
                                    self.update_signal.emit(f"이미지 다운로드 중: {img_url}")
                                    response = requests.get(img_url, stream=True)
                                    
                                    if response.status_code == 200:
                                        with open(save_path, 'wb') as file:
                                            for chunk in response.iter_content(1024):
                                                file.write(chunk)
                                        self.update_signal.emit(f"이미지 저장 완료: {save_path}")
                                        downloaded_count += 1
                                    else:
                                        self.update_signal.emit(f"이미지 다운로드 실패. 상태 코드: {response.status_code}")
                                except Exception as e:
                                    self.update_signal.emit(f"이미지 다운로드 중 오류 발생: {e}")
                                    
                        except Exception as e:
                            self.update_signal.emit(f"게시글 처리 중 오류 발생: {e}")
                            
                except Exception as e:
                    self.update_signal.emit(f"게시글 목록 처리 중 오류 발생: {e}")
                    
                # 잠시 대기 후 다시 목록 페이지로
                time.sleep(2)
                
            # 작업 완료
            if not self.running:
                self.finished_signal.emit(False, "사용자에 의해 중단되었습니다.", self.download_dir)
            else:
                self.finished_signal.emit(True, f"이미지 다운로드 작업이 완료되었습니다. 총 {downloaded_count}개의 이미지를 다운로드했습니다.", self.download_dir)
                
        except Exception as e:
            self.finished_signal.emit(False, f"이미지 다운로드 중 오류 발생: {e}", self.download_dir)
        finally:
            browser.stop()
            
    def stop(self):
        """작업 중단"""
        self.running = False

class ImageDownloaderWidget(QWidget):
    """
    이미지 다운로드 기능을 위한 위젯
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        self.worker = None
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 다운로드 설정
        settings_group = QGroupBox("다운로드 설정")
        settings_layout = QVBoxLayout()
        
        # 실행 시간
        time_layout = QHBoxLayout()
        time_label = QLabel("실행 시간(분):")
        self.time_spinbox = QSpinBox()
        self.time_spinbox.setMinimum(1)
        self.time_spinbox.setMaximum(120)
        self.time_spinbox.setValue(10)
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_spinbox)
        
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
        
        settings_layout.addLayout(time_layout)
        settings_layout.addLayout(path_layout)
        settings_group.setLayout(settings_layout)
        
        # 실행 버튼
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("이미지 다운로드 시작")
        self.start_button.clicked.connect(self.start_downloader)
        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_downloader)
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
        
        # 기본 저장 경로 설정
        default_path = os.path.join(os.path.expanduser("~"), "Downloads", "orbi_images")
        self.path_input.setText(default_path)
        
    def log(self, message):
        """로그 출력"""
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.logger.info(message)
        
    def browse_save_path(self):
        """저장 경로 선택"""
        options = QFileDialog.Options()
        directory = QFileDialog.getExistingDirectory(
            self,
            "저장 경로 선택",
            self.path_input.text() or os.path.expanduser("~/Downloads"),
            options=options
        )
        
        if directory:
            self.path_input.setText(directory)
        
    def start_downloader(self):
        """이미지 다운로드 시작"""
        # 실행 시간 확인
        run_time_minutes = self.time_spinbox.value()
        
        # 저장 경로 확인
        download_dir = self.path_input.text().strip()
        if not download_dir:
            # 기본 저장 경로 설정
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "orbi_images")
            self.path_input.setText(download_dir)
            
        # UI 상태 변경
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 로그 초기화
        self.log_text.clear()
        self.log(f"이미지 다운로드 작업 준비 중... (실행 시간: {run_time_minutes}분, 저장 경로: {download_dir})")
        
        # 워커 스레드 시작
        self.worker = ImageDownloaderWorker(run_time_minutes, download_dir)
        self.worker.update_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_downloader_finished)
        self.worker.start()
        
    def stop_downloader(self):
        """이미지 다운로드 중지"""
        if self.worker and self.worker.isRunning():
            self.log("이미지 다운로드 중지 요청...")
            self.worker.stop()
            
    def on_downloader_finished(self, success, message, download_dir):
        """이미지 다운로드 완료 처리"""
        if success:
            self.log(f"✅ {message}")
            # 폴더 열기 옵션 제공
            reply = QMessageBox.question(
                self,
                "완료",
                f"{message}\n\n다운로드 폴더를 열어보시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # 플랫폼에 따라 폴더 열기
                if sys.platform == 'win32':
                    os.startfile(download_dir)
                elif sys.platform == 'darwin':  # macOS
                    import subprocess
                    subprocess.call(['open', download_dir])
                else:  # Linux
                    import subprocess
                    subprocess.call(['xdg-open', download_dir])
        else:
            self.log(f"❌ {message}")
            
        # UI 상태 복원
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

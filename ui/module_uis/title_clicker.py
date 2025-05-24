from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QListWidget, QListWidgetItem, QGroupBox, QMessageBox, QAbstractItemView
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.login_dialog import LoginWidget
from utils.browser import Browser
from utils.logger import Logger

class TitleClickerWorker(QThread):
    """
    글 삭제 작업을 수행하는 워커 스레드
    """
    update_signal = pyqtSignal(str)
    posts_found_signal = pyqtSignal(list)  # 게시글 목록 전달
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, username, password, post_ids=None):
        super().__init__()
        self.username = username
        self.password = password
        self.post_ids = post_ids  # 삭제할 게시글 ID 목록
        self.logger = Logger()
        self.running = True
        self.mode = "fetch" if post_ids is None else "delete"
        
    def run(self):
        """스레드 실행"""
        if self.mode == "fetch":
            self.update_signal.emit("내 게시글 목록을 가져오는 중...")
        else:
            self.update_signal.emit(f"선택한 게시글 삭제 작업을 시작합니다... (게시글 수: {len(self.post_ids)})")
        
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
            
            if self.mode == "fetch":
                # 내 게시글 목록 가져오기
                posts = self.extract_posts(browser)
                if posts:
                    self.posts_found_signal.emit(posts)
                    self.finished_signal.emit(True, f"{len(posts)}개의 게시글을 찾았습니다.")
                else:
                    self.finished_signal.emit(False, "게시글을 찾을 수 없습니다.")
            else:
                # 선택한 게시글 삭제
                success_count = 0
                for i, post_id in enumerate(self.post_ids):
                    if not self.running:
                        self.finished_signal.emit(False, "사용자에 의해 중단되었습니다.")
                        browser.stop()
                        return
                        
                    try:
                        self.update_signal.emit(f"게시글 삭제 {i+1}/{len(self.post_ids)} 시도 중... (ID: {post_id})")
                        
                        # 게시글 수정 페이지로 이동
                        modify_url = f"https://orbi.kr/modify/{post_id}"
                        browser.get(modify_url)
                        time.sleep(2)
                        
                        # 삭제 버튼 찾기
                        delete_button = driver.find_element("css selector", ".button.delete")
                        delete_button.click()
                        time.sleep(1)
                        
                        # 확인 알림창 처리
                        try:
                            alert = driver.switch_to.alert
                            alert.accept()
                            self.update_signal.emit("삭제 확인 알림창 처리 완료")
                        except:
                            self.update_signal.emit("삭제 확인 알림창이 나타나지 않았습니다.")
                            
                        time.sleep(2)
                        success_count += 1
                        self.update_signal.emit(f"게시글 삭제 {i+1}/{len(self.post_ids)} 성공!")
                        
                    except Exception as e:
                        self.update_signal.emit(f"게시글 삭제 {i+1}/{len(self.post_ids)} 실패: {e}")
                        time.sleep(2)  # 오류 발생 시 잠시 대기
                        
                self.finished_signal.emit(True, f"게시글 삭제 작업이 완료되었습니다. {success_count}/{len(self.post_ids)}개 삭제 성공!")
                
        except Exception as e:
            self.finished_signal.emit(False, f"작업 중 오류 발생: {e}")
        finally:
            browser.stop()
            
    def extract_posts(self, browser):
        """내 게시글 목록 추출"""
        posts = []
        page = 1
        
        while self.running:
            self.update_signal.emit(f"게시글 목록 페이지 {page} 가져오는 중...")
            browser.get(f"https://orbi.kr/my/post?page={page}")
            time.sleep(2)
            
            driver = browser.get_driver()
            
            try:
                # 게시글 목록 요소 찾기
                post_elements = driver.find_elements("css selector", "ul.post-list > li")
                
                if not post_elements:
                    self.update_signal.emit(f"페이지 {page}에서 게시글을 찾을 수 없습니다.")
                    break
                    
                valid_posts_found = False
                for post in post_elements:
                    try:
                        # 제목 요소 찾기
                        title_element = post.find_element("css selector", "p.title")
                        title = title_element.text.strip()
                        
                        # 링크 요소 찾기
                        link_element = post.find_element("tag name", "a")
                        href = link_element.get_attribute("href")
                        post_id = href.split('/')[-1] if href else None
                        
                        if title and post_id:
                            posts.append({"title": title, "id": post_id})
                            valid_posts_found = True
                            self.update_signal.emit(f"게시글 발견: {title} (ID: {post_id})")
                    except Exception as e:
                        self.update_signal.emit(f"게시글 정보 추출 중 오류: {e}")
                        
                if not valid_posts_found:
                    self.update_signal.emit("더 이상 유효한 게시글이 없습니다.")
                    break
                    
                page += 1
                
            except Exception as e:
                self.update_signal.emit(f"게시글 목록 처리 중 오류: {e}")
                break
                
        return posts
            
    def stop(self):
        """작업 중단"""
        self.running = False

class TitleClickerWidget(QWidget):
    """
    글 삭제 기능을 위한 위젯
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        self.worker = None
        self.posts = []
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 로그인 위젯
        login_group = QGroupBox("로그인 정보")
        self.login_widget = LoginWidget()
        login_layout = QVBoxLayout()
        login_layout.addWidget(self.login_widget)
        login_group.setLayout(login_layout)
        
        # 게시글 목록
        posts_group = QGroupBox("내 게시글 목록")
        posts_layout = QVBoxLayout()
        
        self.posts_list = QListWidget()
        self.posts_list.setSelectionMode(QAbstractItemView.MultiSelection)
        posts_layout.addWidget(self.posts_list)
        
        # 게시글 목록 버튼
        list_button_layout = QHBoxLayout()
        self.fetch_button = QPushButton("게시글 목록 가져오기")
        self.fetch_button.clicked.connect(self.fetch_posts)
        list_button_layout.addWidget(self.fetch_button)
        posts_layout.addLayout(list_button_layout)
        
        posts_group.setLayout(posts_layout)
        
        # 실행 버튼
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("선택한 게시글 삭제")
        self.start_button.clicked.connect(self.start_title_clicker)
        self.start_button.setEnabled(False)
        self.stop_button = QPushButton("중지")
        self.stop_button.clicked.connect(self.stop_title_clicker)
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
        layout.addWidget(posts_group)
        layout.addLayout(button_layout)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
        
    def log(self, message):
        """로그 출력"""
        from datetime import datetime
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.logger.info(message)
        
    def fetch_posts(self):
        """내 게시글 목록 가져오기"""
        # 로그인 정보 확인
        credentials = self.login_widget.get_credentials()
        if not credentials["username"] or not credentials["password"]:
            QMessageBox.warning(self, "경고", "아이디와 비밀번호를 입력해주세요.")
            return
            
        # UI 상태 변경
        self.fetch_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 로그 초기화
        self.log_text.clear()
        self.log("내 게시글 목록을 가져오는 중...")
        
        # 게시글 목록 초기화
        self.posts_list.clear()
        self.posts = []
        
        # 워커 스레드 시작
        self.worker = TitleClickerWorker(
            credentials["username"],
            credentials["password"]
        )
        self.worker.update_signal.connect(self.log)
        self.worker.posts_found_signal.connect(self.update_posts_list)
        self.worker.finished_signal.connect(self.on_fetch_finished)
        self.worker.start()
        
    def update_posts_list(self, posts):
        """게시글 목록 업데이트"""
        self.posts = posts
        self.posts_list.clear()
        
        for post in posts:
            item = QListWidgetItem(f"{post['title']} (ID: {post['id']})")
            item.setData(Qt.UserRole, post['id'])
            self.posts_list.addItem(item)
            
        self.log(f"{len(posts)}개의 게시글을 목록에 추가했습니다.")
        
    def start_title_clicker(self):
        """글 삭제 시작"""
        # 선택한 게시글 확인
        selected_items = self.posts_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "경고", "삭제할 게시글을 선택해주세요.")
            return
            
        # 선택한 게시글 ID 추출
        post_ids = [item.data(Qt.UserRole) for item in selected_items]
        
        # 로그인 정보 확인
        credentials = self.login_widget.get_credentials()
        if not credentials["username"] or not credentials["password"]:
            QMessageBox.warning(self, "경고", "아이디와 비밀번호를 입력해주세요.")
            return
            
        # 삭제 확인
        reply = QMessageBox.question(
            self,
            "삭제 확인",
            f"선택한 {len(post_ids)}개의 게시글을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # UI 상태 변경
        self.fetch_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 로그 초기화
        self.log_text.clear()
        self.log(f"선택한 {len(post_ids)}개의 게시글 삭제 작업 준비 중...")
        
        # 워커 스레드 시작
        self.worker = TitleClickerWorker(
            credentials["username"],
            credentials["password"],
            post_ids
        )
        self.worker.update_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_delete_finished)
        self.worker.start()
        
    def stop_title_clicker(self):
        """작업 중지"""
        if self.worker and self.worker.isRunning():
            self.log("작업 중지 요청...")
            self.worker.stop()
            
    def on_fetch_finished(self, success, message):
        """게시글 목록 가져오기 완료 처리"""
        if success:
            self.log(f"✅ {message}")
            self.start_button.setEnabled(len(self.posts) > 0)
        else:
            self.log(f"❌ {message}")
            self.start_button.setEnabled(False)
            
        # UI 상태 복원
        self.fetch_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
    def on_delete_finished(self, success, message):
        """게시글 삭제 완료 처리"""
        if success:
            self.log(f"✅ {message}")
            # 게시글 목록 다시 가져오기 제안
            reply = QMessageBox.question(
                self,
                "완료",
                f"{message}\n\n게시글 목록을 다시 가져오시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.fetch_posts()
                return
        else:
            self.log(f"❌ {message}")
            
        # UI 상태 복원
        self.fetch_button.setEnabled(True)
        self.start_button.setEnabled(len(self.posts) > 0)
        self.stop_button.setEnabled(False)

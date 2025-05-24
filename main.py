import os, sys
app_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(app_dir)
sys.path.append(app_dir)



import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QStatusBar, QMessageBox, QStackedWidget
from PyQt5.QtCore import Qt

# 각 기능 모듈 UI 가져오기
from ui.module_uis.attendance import AttendanceWidget
from ui.module_uis.commenter import CommenterWidget
from ui.module_uis.imin_scraper import IminScraperWidget
from ui.module_uis.image_downloader import ImageDownloaderWidget
from ui.module_uis.lottery import LotteryWidget
from ui.module_uis.title_clicker import TitleClickerWidget

class OrbiApp(QMainWindow):
    """
    오르비 프로젝트 앱의 메인 윈도우 클래스
    """
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        """UI 초기화"""
        # 기본 윈도우 설정
        self.setWindowTitle('오르비 프로젝트')
        self.setGeometry(100, 100, 800, 600)
        
        # 상태바 설정
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('준비됨')
        
        # 메뉴바 설정
        menubar = self.menuBar()
        
        # 파일 메뉴
        fileMenu = menubar.addMenu('파일')
        
        exitAction = QAction('종료', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('앱 종료')
        exitAction.triggered.connect(self.close)
        
        settingsAction = QAction('설정', self)
        settingsAction.setStatusTip('앱 설정')
        settingsAction.triggered.connect(self.openSettings)
        
        fileMenu.addAction(settingsAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)
        
        # 기능 메뉴
        functionsMenu = menubar.addMenu('기능')
        
        attendanceAction = QAction('출석 체크', self)
        attendanceAction.setStatusTip('오르비 자동 출석 체크')
        attendanceAction.triggered.connect(self.openAttendance)
        
        commenterAction = QAction('댓글 작성', self)
        commenterAction.setStatusTip('오르비 자동 댓글 작성')
        commenterAction.triggered.connect(self.openCommenter)
        
        iminScraperAction = QAction('아이민 글 제목 추출', self)
        iminScraperAction.setStatusTip('아이민으로 작성된 글 제목 추출')
        iminScraperAction.triggered.connect(self.openIminScraper)
        
        imageDownloaderAction = QAction('이미지 다운로드', self)
        imageDownloaderAction.setStatusTip('오르비 게시글 이미지 자동 다운로드')
        imageDownloaderAction.triggered.connect(self.openImageDownloader)
        
        lotteryAction = QAction('복권 구매', self)
        lotteryAction.setStatusTip('오르비 복권 자동 구매')
        lotteryAction.triggered.connect(self.openLottery)
        
        titleClickerAction = QAction('글 삭제', self)
        titleClickerAction.setStatusTip('자신이 작성한 글 자동 삭제')
        titleClickerAction.triggered.connect(self.openTitleClicker)
        
        functionsMenu.addAction(attendanceAction)
        functionsMenu.addAction(commenterAction)
        functionsMenu.addAction(iminScraperAction)
        functionsMenu.addAction(imageDownloaderAction)
        functionsMenu.addAction(lotteryAction)
        functionsMenu.addAction(titleClickerAction)
        
        # 도움말 메뉴
        helpMenu = menubar.addMenu('도움말')
        
        aboutAction = QAction('정보', self)
        aboutAction.setStatusTip('앱 정보')
        aboutAction.triggered.connect(self.showAbout)
        
        helpMenu.addAction(aboutAction)
        
        # 스택 위젯 설정 (각 기능별 위젯을 스택으로 관리)
        self.stackedWidget = QStackedWidget()
        self.setCentralWidget(self.stackedWidget)
        
        # 각 기능별 위젯 생성 및 스택에 추가
        self.attendanceWidget = AttendanceWidget()
        self.commenterWidget = CommenterWidget()
        self.iminScraperWidget = IminScraperWidget()
        self.imageDownloaderWidget = ImageDownloaderWidget()
        self.lotteryWidget = LotteryWidget()
        self.titleClickerWidget = TitleClickerWidget()
        
        self.stackedWidget.addWidget(self.attendanceWidget)
        self.stackedWidget.addWidget(self.commenterWidget)
        self.stackedWidget.addWidget(self.iminScraperWidget)
        self.stackedWidget.addWidget(self.imageDownloaderWidget)
        self.stackedWidget.addWidget(self.lotteryWidget)
        self.stackedWidget.addWidget(self.titleClickerWidget)
        
        # 기본 화면 설정
        self.welcomeWidget = self.createWelcomeWidget()
        self.stackedWidget.addWidget(self.welcomeWidget)
        self.stackedWidget.setCurrentWidget(self.welcomeWidget)
        
    def createWelcomeWidget(self):
        """시작 화면 위젯 생성"""
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 제목 라벨
        titleLabel = QLabel("오르비 프로젝트")
        titleLabel.setAlignment(Qt.AlignCenter)
        titleFont = QFont()
        titleFont.setPointSize(24)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        
        # 설명 라벨
        descLabel = QLabel("왼쪽 상단의 '기능' 메뉴에서 원하는 기능을 선택하세요.")
        descLabel.setAlignment(Qt.AlignCenter)
        descFont = QFont()
        descFont.setPointSize(12)
        descLabel.setFont(descFont)
        
        # 버전 라벨
        versionLabel = QLabel("버전 1.0")
        versionLabel.setAlignment(Qt.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(titleLabel)
        layout.addWidget(descLabel)
        layout.addWidget(versionLabel)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
        
    def openSettings(self):
        """설정 창 열기"""
        self.statusBar.showMessage('설정 창 열기')
        # TODO: 설정 다이얼로그 구현
        QMessageBox.information(self, '알림', '설정 기능은 아직 구현되지 않았습니다.')
        
    def openAttendance(self):
        """출석 체크 기능 열기"""
        self.statusBar.showMessage('출석 체크 기능 열기')
        self.stackedWidget.setCurrentWidget(self.attendanceWidget)
        
    def openCommenter(self):
        """댓글 작성 기능 열기"""
        self.statusBar.showMessage('댓글 작성 기능 열기')
        self.stackedWidget.setCurrentWidget(self.commenterWidget)
        
    def openIminScraper(self):
        """아이민 글 제목 추출 기능 열기"""
        self.statusBar.showMessage('아이민 글 제목 추출 기능 열기')
        self.stackedWidget.setCurrentWidget(self.iminScraperWidget)
        
    def openImageDownloader(self):
        """이미지 다운로드 기능 열기"""
        self.statusBar.showMessage('이미지 다운로드 기능 열기')
        self.stackedWidget.setCurrentWidget(self.imageDownloaderWidget)
        
    def openLottery(self):
        """복권 구매 기능 열기"""
        self.statusBar.showMessage('복권 구매 기능 열기')
        self.stackedWidget.setCurrentWidget(self.lotteryWidget)
        
    def openTitleClicker(self):
        """글 삭제 기능 열기"""
        self.statusBar.showMessage('글 삭제 기능 열기')
        self.stackedWidget.setCurrentWidget(self.titleClickerWidget)
        
    def showAbout(self):
        """앱 정보 표시"""
        QMessageBox.about(self, '오르비 프로젝트 정보', 
                          '오르비 프로젝트 앱 v1.0\n\n'
                          '오르비 사이트 관련 자동화 기능을 제공하는 애플리케이션입니다.\n'
                          '© 2025 오르비 프로젝트')

def main():
    app = QApplication(sys.argv)
    window = OrbiApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

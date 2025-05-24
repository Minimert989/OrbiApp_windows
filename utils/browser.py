from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
import os

class Browser:
    """
    브라우저 관리를 위한 유틸리티 클래스
    """
    def __init__(self, chromedriver_path=None, headless=True):
        """
        브라우저 관리자 초기화
        
        Args:
            chromedriver_path (str, optional): ChromeDriver 경로
            headless (bool): 헤드리스 모드 사용 여부
        """
        self.chromedriver_path = chromedriver_path
        self.headless = headless
        self.driver = None
        
    def start(self):
        """
        브라우저 시작
        
        Returns:
            bool: 성공 여부
        """
        try:
            chrome_options = webdriver.ChromeOptions()
            
            if self.headless:
                chrome_options.add_argument("--headless")
                
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920x1080")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # ChromeDriver 경로가 지정되었으면 사용, 아니면 자동 감지
            if self.chromedriver_path and os.path.exists(self.chromedriver_path):
                service = Service(executable_path=self.chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
                
            return True
        except WebDriverException as e:
            print(f"브라우저 시작 중 오류 발생: {e}")
            return False
            
    def stop(self):
        """
        브라우저 종료
        """
        if self.driver:
            self.driver.quit()
            self.driver = None
            
    def get(self, url):
        """
        URL 이동
        
        Args:
            url (str): 이동할 URL
            
        Returns:
            bool: 성공 여부
        """
        if not self.driver:
            if not self.start():
                return False
                
        try:
            self.driver.get(url)
            return True
        except Exception as e:
            print(f"URL 이동 중 오류 발생: {e}")
            return False
            
    def get_driver(self):
        """
        WebDriver 인스턴스 반환
        
        Returns:
            WebDriver: 현재 WebDriver 인스턴스
        """
        if not self.driver:
            self.start()
            
        return self.driver

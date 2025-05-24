import os
import logging
from datetime import datetime

class Logger:
    """
    로깅 기능을 제공하는 유틸리티 클래스
    """
    def __init__(self, log_dir="logs"):
        """
        로거 초기화
        
        Args:
            log_dir (str): 로그 파일이 저장될 디렉토리
        """
        # 로그 디렉토리 생성
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 로그 파일명 설정 (현재 날짜 기준)
        log_filename = f"{datetime.now().strftime('%Y-%m-%d')}.log"
        log_path = os.path.join(log_dir, log_filename)
        
        # 로거 설정
        self.logger = logging.getLogger("OrbiApp")
        self.logger.setLevel(logging.INFO)
        
        # 파일 핸들러 설정
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷 설정
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 핸들러 추가
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def info(self, message):
        """정보 로그 기록"""
        self.logger.info(message)
        
    def warning(self, message):
        """경고 로그 기록"""
        self.logger.warning(message)
        
    def error(self, message):
        """오류 로그 기록"""
        self.logger.error(message)
        
    def debug(self, message):
        """디버그 로그 기록"""
        self.logger.debug(message)

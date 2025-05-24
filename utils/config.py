import os
import json

class Config:
    """
    설정 관리를 위한 유틸리티 클래스
    """
    def __init__(self, config_file="config.json"):
        """
        설정 관리자 초기화
        
        Args:
            config_file (str): 설정 파일 경로
        """
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self):
        """설정 파일 로드"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"설정 파일 로드 중 오류 발생: {e}")
                return self._get_default_config()
        else:
            return self._get_default_config()
            
    def _get_default_config(self):
        """기본 설정 반환"""
        return {
            "login": {
                "remember_credentials": False,
                "username": "",
                "password": ""
            },
            "browser": {
                "chromedriver_path": "",
                "headless": True
            },
            "paths": {
                "download_dir": os.path.expanduser("~/Downloads"),
                "log_dir": "logs"
            }
        }
        
    def save_config(self):
        """설정 파일 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"설정 파일 저장 중 오류 발생: {e}")
            return False
            
    def get(self, section, key=None):
        """
        설정값 가져오기
        
        Args:
            section (str): 설정 섹션
            key (str, optional): 설정 키. None이면 섹션 전체 반환
            
        Returns:
            설정값 또는 섹션 전체
        """
        if section not in self.config:
            return None
            
        if key is None:
            return self.config[section]
            
        if key in self.config[section]:
            return self.config[section][key]
            
        return None
        
    def set(self, section, key, value):
        """
        설정값 설정
        
        Args:
            section (str): 설정 섹션
            key (str): 설정 키
            value: 설정값
            
        Returns:
            bool: 성공 여부
        """
        if section not in self.config:
            self.config[section] = {}
            
        self.config[section][key] = value
        return self.save_config()

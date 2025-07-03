
import os
import locale
from datetime import datetime
import pytz

# 로케일 설정 통일
def setup_locale():
    """표준 로케일 설정"""
    # 한국 시간대 설정
    os.environ['TZ'] = 'Asia/Seoul'
    
    # 한국 로케일 설정
    try:
        locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'ko_KR')
        except:
            pass  # 기본 로케일 사용
    
    return pytz.timezone('Asia/Seoul')

# 표준 시간 포맷
def get_current_time():
    """현재 시간 (한국 시간대)"""
    tz = setup_locale()
    return datetime.now(tz)

def format_datetime(dt, format_str="%Y-%m-%d %H:%M:%S"):
    """표준 시간 포맷"""
    if dt.tzinfo is None:
        dt = setup_locale().localize(dt)
    return dt.strftime(format_str)

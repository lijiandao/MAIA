import getpass
import platform
import time  
import undetected_chromedriver as uc  
from fake_useragent import UserAgent  
from selenium.webdriver.chrome.service import Service  
from selenium.webdriver.chrome.options import Options  
from webdriver_manager.chrome import ChromeDriverManager  
from selenium import webdriver  
import random  
import os
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities  
import ctypes
import sys

def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """以管理员权限重新运行脚本"""
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)



def anti_notification(options):
     # 广告和弹窗屏蔽选项  
    options.add_argument('--disable-popup-blocking')  # 禁用弹窗拦截  
    # options.add_argument('--disable-extensions')  # 禁用浏览器扩展  
    
    # 高级广告和推广屏蔽  
    options.add_experimental_option('prefs', {  
        # 禁用通知  
        'profile.default_content_setting_values.notifications': 2,  
        
        # 禁用推广和广告  
        'profile.managed_default_content_settings.images': 2,  # 屏蔽图片  
        'profile.managed_default_content_settings.ads': 2,  # 屏蔽广告  
        
        # 阻止特定类型的弹窗  
        'profile.default_content_settings.popups': 2,  
        
        # 禁用某些自动播放和推荐内容  
        'profile.managed_default_content_settings.media_stream': 2,  
        'profile.managed_default_content_settings.geolocation': 2,  
    })  
    
    # 额外的广告屏蔽脚本  
    options.add_argument('--disable-background-networking')  
    options.add_argument('--disable-default-apps')  
    
    # 注入广告屏蔽脚本  
    options.add_experimental_option("excludeSwitches", [  
        "enable-automation",  # 禁用自动化提示  
        "enable-logging",  # 禁用日志  
    ])  
    
    # JS广告屏蔽  
    adblock_script = """  
    // 屏蔽常见广告元素  
    const style = document.createElement('style');  
    style.innerHTML = `  
        .ad, .advertisement,   
        [class*='ad'], [class*='popup'],   
        [id*='ad'], [id*='popup'],  
        [class*='banner'], [id*='banner'] {  
            display: none !important;  
            visibility: hidden !important;  
            opacity: 0 !important;  
            height: 0 !important;  
            width: 0 !important;  
        }  
    `;  
    document.head.appendChild(style);  

    // 移除推广内容  
    function removePromotionalContent() {  
        const selectors = [  
            '[class*="promo"]',   
            '[id*="promo"]',  
            '[class*="recommend"]',   
            '[id*="recommend"]',  
            '[class*="suggestion"]',   
            '[id*="suggestion"]'  
        ];  

        selectors.forEach(selector => {  
            document.querySelectorAll(selector).forEach(el => {  
                el.remove();  
            });  
        });  
    }  

    // 定期清理  
    setInterval(removePromotionalContent, 1000);  
    """  
    return adblock_script




def get_chrome_user_data_dir():  
    """获取当前用户的Chrome用户数据目录"""  
    system = platform.system()  
    username = getpass.getuser()  
    
    if system == "Windows":  
        return f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data"  
    elif system == "Darwin":  # macOS  
        return f"/Users/{username}/Library/Application Support/Google/Chrome"  
    elif system == "Linux":  
        return f"/home/{username}/.config/google-chrome"  
    else:  
        return None  


def create_normal_chrome_driver(temp_user_data = r'C:\Users\25131\AppData\Local\Temp\chrome_user_data_1feee483',
                             extension_path=r'./browser_extensions/v3.2.5.crx'):  
    """创建反反爬的Chrome浏览器驱动
    Args:
        temp_user_data (str, optional): 自定义临时用户数据目录路径. Defaults to None.
        extension_path (str, optional): 浏览器扩展文件路径 (.crx 或 .zip). Defaults to None.
    """  
    # # 检查管理员权限
    # if not is_admin():
    #     print("请求管理员权限...")
    #     run_as_admin()
    #     sys.exit(0)  # 退出当前非管理员进程
    from proxy_detector import get_system_proxy
    system_proxy = get_system_proxy()
    if system_proxy:
        print(f"检测到系统代理: {system_proxy}")
        # 设置环境变量
        os.environ['http_proxy'] = f'http://{system_proxy}'
        os.environ['https_proxy'] = f'http://{system_proxy}'
    else:   
        print("未检测到系统代理")
    # 创建选项  
    options = Options()  
    
   


    # 基本配置  
    options.use_chromium = True  
    
    # # 如果提供了扩展路径
    # if extension_path and os.path.exists(extension_path):
        # options.add_extension(extension_path)
        # print(f"已加载浏览器扩展: {extension_path}")
    
    # 获取用户数据目录
    user_data_dir = get_chrome_user_data_dir()
    print(f"用户数据目录: {user_data_dir}")
    
    # 如果获取到用户数据目录
    if user_data_dir:
        # 仅在临时目录不存在时才复制
        if not os.path.exists(temp_user_data):
            # 复制用户数据到临时目录
            import shutil
            try:
                shutil.copytree(user_data_dir, temp_user_data)
                print(f"已将用户数据从 {user_data_dir} 复制到 {temp_user_data}")
            except Exception as e:
                print(f"无法复制用户数据: {str(e)}")
                return None
        else:
            print(f"临时用户数据已存在: {temp_user_data}")
        
        options.add_argument(f"--user-data-dir={temp_user_data}")
        options.add_argument("--profile-directory=Default")
    else:
        print("无法获取Chrome用户数据目录")

    # 常用反反爬参数  
    options.add_argument("--disable-blink-features=AutomationControlled") # 禁用自动化控制，可能某些网站加载缓慢
    options.add_argument("--disable-infobars")  # 禁用信息栏 "是否保存密码"、"是否保存密码"、"是否保存密码"
    # 随机窗口大小  
    screen_resolutions = [  
        "1366,768",   
        "1920,1080",   
        "1600,900",   
        "1440,900",   
        "1280,720"  
    ]  
    random_resolution = random.choice(screen_resolutions)  
    options.add_argument(f'--window-size={random_resolution}')  
    

    # 启动无头模式
    # options.add_argument("--headless")

    # 禁用自动化特征  
    options.add_experimental_option("excludeSwitches", ["enable-automation"])  
    options.add_experimental_option("useAutomationExtension", False)  
    
    # 性能和安全相关参数  
    options.add_argument("--disable-gpu")  # 禁用GPU加速
    options.add_argument("--no-sandbox")  # 禁用沙盒
    options.add_argument("--disable-dev-shm-usage")  # 禁用共享内存
    options.add_argument("--ignore-certificate-errors")  # 忽略证书错误
    
    # 禁用日志输出  
    options.add_experimental_option('excludeSwitches', ['enable-logging'])  # 禁用日志输出
    
    # 额外的SSL和网络相关选项  
    options.add_argument('--disable-web-security')  # 禁用网络安全限制  
    options.add_argument('--disable-site-isolation-trials')  # 禁用站点隔离  
    
    # 随机用户代理（仅限桌面版）
    ua = UserAgent()
    random_user_agent = ua.chrome  # 直接获取桌面版Chrome UA
    print(f"随机用户代理: {random_user_agent}") # 随机用户代理
    # 电脑版的ua
    random_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'

    options.add_argument(f'user-agent={random_user_agent}')  
    
    # WebRTC和隐私保护  
    options.add_argument("--disable-webrtc")  # 禁用WebRTC
    options.add_argument("--disable-webrtc-encryption")  # 禁用WebRTC加密
    options.add_argument("--disable-webrtc-hw-encoding")  # 禁用WebRTC硬件编码
    options.add_argument("--disable-webrtc-hw-decoding")  # 禁用WebRTC硬件解码
    
    # 性能优化  
    options.add_argument("--disable-background-networking")  # 禁用后台网络： 自动更新检查、崩溃报告上传、遥测数据收集、同步服务、插件更新、安全检查
    # options.add_argument("--disable-default-apps")  # 禁用默认应用：默认应用包括 PDF阅读器、书签管理、下载管理器、Chrome应用商店、内置扩展程序、同步服务
    options.page_load_strategy = 'eager'  
    options.add_argument("--disable-images")  # 禁用图片加载
    options.add_argument("--blink-settings=imagesEnabled=false")  # 另一种禁用图片的方式
    options.add_argument("--disable-java")  # 禁用Java
    options.add_argument("--disable-audio")  # 禁用音频
    options.add_argument("--disable-video")  # 禁用视频
    options.add_argument("--disable-animations")  # 禁用动画
    options.add_argument("--disable-gl-drawing-for-tests")  # 禁用GL绘图
    options.add_argument("--disable-2d-canvas-clip-aa")  # 禁用2D画布剪辑抗锯齿
    options.add_argument("--disable-canvas-aa")  # 禁用画布抗锯齿
    options.add_argument("--disable-accelerated-mjpeg-decode")  # 禁用加速MJPEG解码
    options.add_argument("--disable-accelerated-jpeg-decoding")  # 禁用加速JPEG解码
    options.add_argument("--disable-font-subpixel-positioning")  # 禁用字体子像素定位
    options.add_argument("--disable-smooth-scrolling")  # 禁用平滑滚动
    options.add_argument("--disable-3d-apis")  # 禁用3D API
    options.add_argument("--disable-speech-api")  # 禁用语音API
    options.add_argument("--disable-sync")  # 禁用同步
    options.add_argument("--disable-smooth-scrolling")  # 禁用平滑滚动
    options.add_argument("--disable-remote-fonts")  # 禁用远程字体
    options.add_argument("--disable-component-update")  # 禁用组件更新
    options.add_argument("--disable-features=TranslateUI")  # 禁用翻译UI
    options.add_argument("--disable-hang-monitor")  # 禁用挂起监视器
    options.add_argument("--disable-ipc-flooding-protection")  # 禁用IPC洪水保护
    options.add_argument("--disable-notifications")  # 禁用通知
    options.add_argument("--allow-running-insecure-content") # 允许运行不安全的资源


    # 随机化一些参数  
    options.add_argument(f"--proxy-server='direct://'")  # 直接连接
    options.add_argument("--proxy-bypass-list=*")  # 绕过代理

    # 创建驱动  
    # 注入广告屏蔽脚本  
    adblock_script = anti_notification(options)
    try:
        service = Service(ChromeDriverManager().install())  
        driver = webdriver.Chrome(  
            service=service,  
            options=options
        )  
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {  
            "source": adblock_script  
        })  
        # 额外的反检测策略  
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {  
            "source": """  
            Object.defineProperty(navigator, 'webdriver', {  
                get: () => undefined  
            })  
            """  
        })  
        # 额外的 Chrome 属性移除  
        driver.execute_cdp_cmd("Network.setUserAgentOverride", {  
            "userAgent": random_user_agent,  
            "platform": "Windows"  
        })  
        
        return driver
        
    except Exception as e:
        print(f"无法启动Chrome浏览器: {str(e)}")
        # 如果启动失败，删除临时数据
        if temp_user_data and os.path.exists(temp_user_data):
            try:
                import shutil
                shutil.rmtree(temp_user_data)
                print(f"删除失败的临时用户数据: {temp_user_data}")
            except Exception as cleanup_error:
                print(f"无法删除临时用户数据: {cleanup_error}")
        
        raise RuntimeError(f"无法启动Chrome浏览器: {str(e)}") from e
    

def safe_copy_user_data(src_dir: str, dst_dir: str) -> dict:
    """
    安全地复制用户数据目录
    Args:
        src_dir: 源目录路径
        dst_dir: 目标目录路径
    Returns:
        dict: {
            'status': 'success'|'failed'|'in_progress',
            'error': str|None,
            'src_dir': str,
            'dst_dir': str,
            'retry_count': int
        }
    """
    import shutil
    import time
    import psutil
    from typing import Dict, Optional
    
    result: Dict[str, Optional[str | int]] = {
        'status': 'in_progress',
        'error': None,
        'src_dir': src_dir,
        'dst_dir': dst_dir,
        'retry_count': 0
    }
    
    max_retries = 3
    retry_delay = 1  # seconds
    
    try:
        # 确保所有浏览器进程退出
        for proc in psutil.process_iter(['pid', 'name']):
            # psutil.process_iter(['pid', 'name'])：获取系统中所有正在运行的进程，并只获取进程的 PID 和名称信息
            try:
                if 'chrome' in proc.info['name'].lower():
                    # 'chrome' in ...：检查进程名称中是否包含 "chrome"（Chrome 浏览器的主进程名称）
                    proc.terminate()
                    proc.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue
        
        # 重试机制
        for attempt in range(max_retries):
            result['retry_count'] = attempt + 1
            try:
                # 如果目标目录存在，先删除
                if os.path.exists(dst_dir):
                    shutil.rmtree(dst_dir)
                
                # 复制目录
                shutil.copytree(src_dir, dst_dir)
                result['status'] = 'success'
                return result
                
            except Exception as e:
                if attempt == max_retries - 1:
                    result['status'] = 'failed'
                    result['error'] = str(e)
                else:
                    time.sleep(retry_delay)
        
        return result
        
    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
        return result
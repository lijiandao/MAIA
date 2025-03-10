import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler('crawler.log')  # 输出到文件
    ]
)
import bs4
from httpcore import TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
 # 发送 Alt+R 组合键  
from selenium.webdriver.common.action_chains import ActionChains  
from selenium.webdriver.common.keys import Keys  
from bs4 import BeautifulSoup
import time
import os
import re
import urllib.parse
import platform
from selenium.webdriver.common.by import By  
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.common.exceptions import TimeoutException  
import urllib.parse  
import time  
import re
from crawler_tools.svg_processor import process_svg_element
from simplify_tools.special_extractor import is_special_url
from shared_content import SPECIAL_URL_PATTERNS
from crawler_tools.fail_detector import fail_load_detect
from crawler_tools.url_processor import process_url_attribute



def dom_after_calculate_div_area(driver):
    """
    返回经过计算div的面积后的dom的内容
    """
    div_area_start = time.time()

    # 合并JavaScript操作
    combined_script = """
    let divs = document.getElementsByTagName('div');
    let results = [];
    for (let i = 0; i < divs.length; i++) {
        let div = divs[i];
        div.setAttribute('data-div-id', 'div-' + i);
        
        // 新增可见性检测
        let style = window.getComputedStyle(div);
        let isVisible = style.display !== 'none' 
            && style.visibility !== 'hidden' 
            && style.opacity !== '0'
            && div.offsetWidth > 0
            && div.offsetHeight > 0;
        
        let area = 0;
        if (isVisible) {
            area = Math.round(div.getBoundingClientRect().width * div.getBoundingClientRect().height);
        } else {
            div.setAttribute('data-invisible', 'true');  // 添加不可见标记
        }
        
        results.push({
            id: div.getAttribute('data-div-id'),
            area: area
        });
    }
    return results;
    """

    try:
        # 一次性执行所有JavaScript操作
        divs_data = driver.execute_script(combined_script)
        
        # 创建id到面积的映射
        area_map = {item['id']: item['area'] for item in divs_data}
        
        # 使用lxml的快速解析模式
        page_source = driver.execute_script("return document.documentElement.outerHTML") # 执行了js ，修改了driver的 dom 之后应该立马更新这里的html字符串和对应的soap
        soup = BeautifulSoup(page_source, 'lxml')
        #  parse_only=bs4.SoupStrainer('div')
        
        # 使用字典加速查找
        div_dict = {div.get('data-div-id'): div for div in soup.find_all('div') if div.get('data-div-id')}
        # 批量处理div更新
        for div_data in divs_data:
            div_id = div_data['id']
            if div_id in div_dict:
                div = div_dict[div_id]
                area = div_data['area']
                div['data-area'] = str(area)  # 强制记录所有面积值
                # 删除临时的div-id标记
                del div['data-div-id']
        
        print(f"成功处理了 {len(area_map)} 个div的面积")
        
    except Exception as e:
        print(f"计算div面积时出错: {e}")
    
    div_area_end = time.time()
    print(f"div面积计算完成，耗时: {div_area_end - div_area_start:.3f}秒")
    return soup




def wait_and_get_html_dom(driver, url, start_time, max_retries=30):
    """
    等待页面加载并获取DOM内容
    
    Args:
        driver: WebDriver实例
        url: 要访问的URL
        start_time: 开始时间
        max_retries: 最大重试次数
    
    Returns:
        str: 页面HTML内容，如果失败则返回错误提示
    """
    try:
        driver.get(url)
        # 首先等待DOM加载完成
        try:
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            print("页面加载超时")
            return '<p>页面加载5s超时</p>'

        # 处理iframe
        print("开始处理iframe...")
        iframe_start = time.time()
        iframe_content = ""  # 初始化变量

        try:
            # 获取所有iframe
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"找到 {len(iframes)} 个iframe")
            
            for index, iframe in enumerate(iframes):
                try:
                    # 切换到iframe
                    driver.switch_to.frame(iframe)
                    
                    # 获取iframe中的HTML内容
                    iframe_html = driver.execute_script("return document.documentElement.outerHTML")
                    
                    # 切回主文档
                    driver.switch_to.parent_frame()
                    
                    # 使用BeautifulSoup解析iframe内容
                    iframe_soup = BeautifulSoup(iframe_html, 'lxml')
                    body_content = iframe_soup.find('body')
                    
                    if body_content:
                        # 提取body中的内容（不包含body标签本身）
                        iframe_content = ''.join(str(tag) for tag in body_content.contents)
                        
                        # 使用JavaScript替换iframe为其内容
                        script = f"""
                        let iframes = document.getElementsByTagName('iframe');
                        let targetIframe = iframes[{index}];
                        let div = document.createElement('div');
                        div.innerHTML = `"""+iframe_content.replace('`', '\\`')+"""`;
                        div.className = 'iframe-content';
                        targetIframe.parentNode.replaceChild(div, targetIframe);
                        """
                        driver.execute_script(script)
                        
                except Exception as e:
                    print(f"处理第 {index + 1} 个iframe时出错: {e}")
                    continue
                    
        except Exception as e:
            print(f"处理iframe时发生错误: {e}")

        # 只在有iframe内容时才写入文件
        if iframe_content:
            try:
                with open("iframe_content.html", "w", encoding="utf-8") as f:
                    f.write(iframe_content)
            except Exception as e:
                print(f"写入iframe内容到文件时出错: {e}")

        iframe_end = time.time()
        print(f"iframe处理完成，耗时: {iframe_end - iframe_start:.3f}秒")

        # 解析基础URL
        # url = "https://www.zhihu.com/question/602383209"
        parsed_base_url = urllib.parse.urlparse(url) # urllib.parse.urlparse(url) 用于解析URL字符串，
        # 将其拆分为多个组成部分（协议scheme (http, https, ftp)、域名netloc(www.zhihu.com)、路径path(/question/602383209)等），方便后续处理。
        base_url = f"{parsed_base_url.scheme}://{parsed_base_url.netloc}" # 'https://www.zhihu.com'
        base_path = os.path.dirname(parsed_base_url.path) # '/question/602383209'

        # 检查是否是知乎问题页面并展开内容
        if any(re.match(pattern, url) for pattern in SPECIAL_URL_PATTERNS['zhihu_question']):
            try:
                # 等待"显示全部"按钮出现
                show_more_button = WebDriverWait(driver, 3).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, '.Button.QuestionRichText-more')
                )
                # 点击按钮展开内容
                show_more_button.click()
                # 等待内容加载
                time.sleep(1)
            except Exception as e:
                print(f"展开知乎问题内容时出错: {e}")
                # 继续处理，因为可能本来就是完整内容

        # 处理 Semantic Scholar 页面
        if any(re.match(pattern, url) for pattern in SPECIAL_URL_PATTERNS['semantic_scholar']):
            try:
                # 等待展开按钮出现
                expand_button = WebDriverWait(driver, 3).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, 'button[aria-label="Expand truncated text"]')
                )
                # 点击展开按钮
                expand_button.click()
                # 等待内容加载
                time.sleep(1)
            except Exception as e:
                print(f"展开 Semantic Scholar 内容时出错: {e}")
                # 继续处理，因为可能本来就是完整内容

        # 添加页面滚动逻辑
        scroll_start = time.time()
        while time.time() - scroll_start < 0.3:  # 滚动0.3秒
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.1)  # 每次滚动后等待0.1秒

        # 检查页面加载状态
        html_content = fail_load_detect(driver)
        if html_content:
            return html_content
            
        retry_count = 0
        html_content = '<p>无有效信息</p>'
        
        # 设置总体超时时间（10秒）
        end_time = start_time + 10
        url_speciality = is_special_url(url)
        while time.time() < end_time:
            try:
                page_source = driver.execute_script("return document.documentElement.outerHTML")
                if page_source and len(page_source) > 50:
                    print("开始计算div面积...(排除特殊url)")
                    soup = dom_after_calculate_div_area(driver) if not url_speciality else BeautifulSoup(page_source, 'lxml')
                        
                    # 然后进行其他元素处理
                    from shared_content import REMOVE_SELECTORS
                    
                    # 移除不需要的元素
                    for selector in REMOVE_SELECTORS:
                        for element in soup.select(selector):
                            element.decompose()
                    
                    # 处理SVG元素 - 优化查找过程
                    svg_start_time = time.time()
                    
                    # 使用CSS选择器直接查找SVG元素，这通常比find_all更快
                    svg_elements = soup.select('svg')
                    
                    svg_count = 0
                    processed_count = 0
                    for svg in svg_elements:
                        svg_count += 1
                        
                        # 处理SVG
                        svg_element_start = time.time()
                        print(f"========> 开始处理SVG元素 #{svg_count}")
                        img_tag = process_svg_element(svg_tag=svg, output_dir="static/images",
                                                    min_width=100, min_height=100, min_elements=10,
                                                    driver=driver)
                        svg_element_end = time.time()
                        print(f"========> SVG元素 #{svg_count} 处理完成，耗时: {svg_element_end - svg_element_start:.3f}秒")
                        if img_tag:
                            processed_count += 1
                            svg.replace_with(img_tag)
                    
                    svg_end_time = time.time()
                    print(f"========> 所有SVG元素处理完成，共 {svg_count} 个，实际处理 {processed_count} 个，总耗时: {svg_end_time - svg_start_time:.3f}秒")
                    
                    
                    logging.info(f"url_speciality: {url_speciality}")
                    # 清理属性
                    for tag in soup.find_all(True):
                        preserved_attrs = {}
                        
                        # 保留面积属性
                        if tag.name == 'div' and 'data-area' in tag.attrs:
                            logging.info(f"========> 保留面积属性: {tag['data-area']}")
                            preserved_attrs['data-area'] = tag['data-area']
                            # 同时保留不可见标记
                            if 'data-invisible' in tag.attrs:
                                preserved_attrs['data-invisible'] = tag['data-invisible']
                        
                        for attr, value in list(tag.attrs.items()):
                            if tag.name == 'img' and attr == 'src':
                                if value:
                                    # 跳过base64编码的图像
                                    if value.startswith('data:'):
                                        continue
                                    
                                    # 如果是本地文件路径（SVG转换后的图片），直接保留
                                    if os.path.exists(value):
                                        preserved_attrs[attr] = value
                                        continue
                                    
                                    try:
                                        # 处理网络图片路径
                                        current_url = url.split('#')[0]
                                        current_dir = os.path.dirname(current_url)
                                        # 解析base_url
                                        if value.startswith('//'):  # 处理协议相对URL
                                            preserved_attrs[attr] = f"{parsed_base_url.scheme}:{value}"
                                        elif value.startswith('/'):  # 处理根路径
                                            preserved_attrs[attr] = f"{base_url}{value}"
                                        elif value.startswith('http'):  # 完整URL
                                            preserved_attrs[attr] = value
                                        else:  # 处理相对路径（包括 ./ 和 ../ 的情况）
                                            preserved_attrs[attr] = urllib.parse.urljoin(current_url + '/', value)
                                            
                                    except Exception as e:
                                        print(f"构建图片URL失败: {e}")
                                        continue
                            
                            # 其他属性的处理保持不变
                            elif tag.name == 'img' and attr in ['alt', 'title']:
                                preserved_attrs[attr] = value
                            
                            # 处理其他链接属性
                            elif attr in ['href', 'src'] and value:
                                processed_url = process_url_attribute(value, url, base_url, base_path, parsed_base_url)
                                if processed_url:
                                    preserved_attrs[attr] = processed_url
                            
                            elif attr in ['class','id'] and value and ( not url_speciality ):
                                # 保留在 simplified.py 中需要进行重要元素选定时需要的特殊的class和id；
                                from shared_content import CONTENT_SELECTORS    
                                if isinstance(value, list):
                                    preserved_attrs[attr] = [v for v in value if v in CONTENT_SELECTORS]
                                else:
                                    preserved_attrs[attr] = value if value in CONTENT_SELECTORS else None
                        
                            pass
                        if not url_speciality:
                            # 清除所有属性
                            tag.attrs.clear()
                        # 恢复需要保留的属性
                        tag.attrs.update(preserved_attrs)
                        # tag.attrs.update(preserved_attrs) 是覆盖操作，而不是简单的新增。

                    
                    # 获取body内容，不使用prettify()进行格式化
                    body = soup.find('body')
                    if body:
                        html_content = str(body)  # 直接转换为字符串，不格式化
                        break
                    else:
                        html_content = '<p>无有效信息</p>'
                
                if retry_count >= max_retries:
                    print(f"重试次数达到最大限制: {max_retries}")
                    break
                    
                retry_count += 1
                time.sleep(0.5)
                
            except Exception as e:
                print(f"处理页面内容时出错: {e}")
                # 错误分类
                error_msg = str(e).lower()
                if 'invalid session id' in error_msg:
                    print("检测到1号错误：浏览器连接已关闭")
                    return '<p>错误1：浏览器会话意外终止</p>'
                elif any(err in error_msg for err in ['timeout', 'timed out']):
                    print("检测到2号错误：请求超时")
                    return '<p>错误2：操作超时</p>'
                
                if retry_count >= max_retries:
                    break
                retry_count += 1
                time.sleep(0.5)
        
        return html_content
        
    except TimeoutException:
        print("页面加载超时")
        return '<p>页面加载3s超时</p>'
        
    except Exception as e:
        print(f"获取页面内容时发生错误: {e}")
        
        return f'<p>爬取页面时发生错误</p>'
    
    finally:
        # 确保切回主文档
        try:
            driver.switch_to.default_content()
        except:
            pass


def fetch_html_dom(driver,url):
    """
    获取网页的HTML内容
    
    Args:
        driver: WebDriver实例
        url: 要获取的网页URL
    """
    
    import proxy_detector
    if proxy_detector.get_system_proxy():
        os.environ['https_proxy'] = proxy_detector.get_system_proxy()
    else:
        print("未获取到系统代理")
    html = wait_and_get_html_dom(driver, url, time.time())
    # 保存HTML到本地文件
    base_dir = "html_files"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    # 查找可用的文件名
    num = 1
    while True:
        file_path = os.path.join(base_dir, f"{num}.html")
        if not os.path.exists(file_path):
            break
        num += 1
    
    # 保存HTML内容
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return file_path



# 额外的进程管理  
import atexit  
import os  
import signal  

def cleanup_driver_processes():  
    """尝试清理所有相关的浏览器和驱动进程"""  
    # 根据操作系统选择不同的进程终止方法  
    if platform.system() == "Windows":  
        os.system('taskkill /F /IM msedge.exe /T')  
        os.system('taskkill /F /IM msedgedriver.exe /T')  
    else:  # Unix-like systems  
        os.system('pkill -f msedge')  
        os.system('pkill -f msedgedriver')  

# 注册退出时的清理函数  
atexit.register(cleanup_driver_processes)  

# 处理信号以确保进程被正确终止  
def signal_handler(signum, frame):  
    print(f"\n收到信号 {signum}，正在清理进程...")  
    cleanup_driver_processes()  
    exit(0)  

# 注册信号处理器  
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C  
signal.signal(signal.SIGTERM, signal_handler)  # 终止信号  


# 自动化爬虫
# if __name__ == "__main__":
#     driver_init_start = time.time()  
    
#     try:  
#         from crawler_tools.driver_getter_edge import create_normal_edge_driver
#         # 创建普通Edge驱动  
#         driver = create_normal_edge_driver()  
        
#         driver_init_time = time.time() - driver_init_start  
#         print(f"WebDriver初始化完成，耗时: {driver_init_time:.2f}秒")  
#     except Exception as e:  
#         print(f"WebDriver初始化失败: {str(e)}")  
    
#     # 读取link_id.txt文件中的URL
#     with open('link_id.txt', 'r') as f:
#         urls = [line.split(': ')[1].strip() for line in f.readlines()]
    
#     # 自动爬取并保存HTML文件
#     for url in urls:
#         print(f"正在爬取: {url}")
#         file_path = fetch_html_dom(driver, url)
#         print(f"HTML文件已保存到: {file_path}")
    
#     # 关闭驱动
#     driver.quit()
#     print("所有URL爬取完成，程序已退出")

# 如果直接运行此文件，则启动交互式爬虫
if __name__ == "__main__":
    # 创建普通Edge驱动  
    from crawler_tools.driver_getter_edge import create_normal_edge_driver
    driver = create_normal_edge_driver()  
  
    
    # 交互式爬虫循环
    while True:
        try:
            url = input("\n请输入要爬取的URL（输入q退出）：")
            if url.lower() == 'q':
                print("退出程序...")
                break
            file_path = fetch_html_dom(driver, url)
            print(f"HTML文件已保存到: {file_path}")
        except Exception as e:
            print(f"爬取过程中发生错误: {str(e)}")

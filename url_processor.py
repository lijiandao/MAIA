import urllib.parse

def process_url_attribute(value, url, base_url, base_path, parsed_base_url):
    """
    处理URL属性（href和src），将相对路径转换为绝对路径
    
    Args:
        value: 原始URL值
        url: 当前页面的完整URL
        base_url: 基础URL（例如：https://www.example.com）
        base_path: URL的基础路径
        parsed_base_url: 解析后的基础URL对象
    
    Returns:
        str: 处理后的URL
    """
    if not value:
        return None
        
    if value.startswith('data:'):  # 保留data URI
        return value
    elif value.startswith('//'):  # 处理协议相对URL
        return f"{parsed_base_url.scheme}:{value}"
    elif value.startswith('/'):  # 处理根路径
        return f"{base_url}{value}"
    elif value.startswith('http'):  # 保留完整URL
        return value
    elif value.startswith('./'):  # 处理当前目录相对路径
        value = value[2:]  # 移除./
        return urllib.parse.urljoin(f"{base_url}{base_path}/", value)
    elif value.startswith('../'):  # 处理上级目录
        return urllib.parse.urljoin(f"{base_url}{base_path}/", value)
    elif value.startswith('#'):  # 处理页内锚点
        return f"{url}{value}"
    else:  # 处理纯相对路径
        return urllib.parse.urljoin(f"{base_url}{base_path}/", value)

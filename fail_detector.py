

def fail_load_detect(driver):
    # 1. 检查页面标题和内容是否表明错误
    error_indicators = [
        "当前无法处理此请求", "404", "Not Found", "Error", "无法访问", 
        "服务器错误", "500", "403", "Forbidden", "Access Denied"
    ]
    
    if any(indicator in driver.title for indicator in error_indicators):
        # driver.title 是字符串类型，所以可以用 in 操作符检查是否包含错误关键词。
        print(f"检测到错误页面标题: {driver.title}")
        return '<p>无有效信息</p>'
        
    # 2. 检查 HTTP 状态码
    try:
        navigation_entries = driver.execute_script(
            "return window.performance.getEntriesByType('navigation')[0]"
        )
        if navigation_entries:
            status_code = driver.execute_script(
                "return window.performance.getEntriesByType('navigation')[0].responseStatus"
            )
            # 这是通过JavaScript获取网页导航性能条目中的HTTP响应状态码。window.performance.getEntriesByType('navigation')返回页面导航相关的性能条目，
            # [0]表示第一个条目，.responseStatus则获取该条目的HTTP响应状态码。
            if status_code and status_code >= 400:
                print(f"检测到 HTTP 错误状态码: {status_code}")
                return '<p>无有效信息</p>'
    except Exception as e:
        print(f"获取 HTTP 状态码时出错: {e}")

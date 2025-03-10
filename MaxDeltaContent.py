import logging
from bs4 import BeautifulSoup
from collections import deque
import bs4
from bs4.element import NavigableString

from colorama import Fore

class DivNode:
    def __init__(self, div):
        self.div = div  # 保存div元素
        self.children = []  # 子节点列表
        self.area = self._get_area()  # 获取当前div的面积

    def _get_area(self):
        """从area-self属性获取div的面积"""
        area_str = self.div.get('data-area', '0')
        try:
            return float(area_str)
        except ValueError:
            return 0.0

def add_unique_ids(soup):
    """为所有标签添加唯一ID"""
    id_counter = 0
    for tag in soup.find_all():
        tag['data-unique-id'] = str(id_counter)
        id_counter += 1
    return soup

def remove_invalid_divs(soup):
    """
    1. 将非div元素转换为div元素
    2. 删除无效的div元素
    3. 设置div面积为其子元素面积之和
    """
    # 首先确保根元素（body）被转换为div
    body = soup.find('body')
    if body and body.name != 'div':
        new_div = soup.new_tag('div')
        # 保留body的属性，包括unique-id
        for attr, value in body.attrs.items():
            new_div[attr] = value
        # 保留body的内容
        new_div.extend(body.contents)
        body.replace_with(new_div)
    
    queue = deque([soup])
    while queue:
        current = queue.popleft()
        children = list(current.children)  # 创建子元素列表的副本
        
        for child in children:
            if not isinstance(child, bs4.element.Tag):
                continue
            
            if child.name != 'div':
                # 将非div元素转换为div
                new_div = soup.new_tag('div')
                # 保留原始标签的所有属性，包括unique-id
                for attr, value in child.attrs.items():
                    new_div[attr] = value
                new_div.extend(child.contents)
                child.replace_with(new_div)
                child = new_div

            # 检查div的有效性
            if child.has_attr('data-invisible'):
                child.decompose()
                continue
                
            queue.append(child)
    
    # 第二次遍历：自底向上计算并设置面积
    def calculate_area(element):
        if not isinstance(element, bs4.element.Tag) or element.name != 'div':
            return 0
            
        # 如果已经有data-area属性，直接返回其值
        if element.has_attr('data-area'):
            return float(element.get('data-area'))
            
        # 只有没有data-area属性的div才需要计算面积
        children = element.find_all('div', recursive=False)
        total_area = sum(calculate_area(child) for child in children)
        # 设置计算得到的面积
        element['data-area'] = str(total_area)
        return total_area
    
    # 从根节点开始计算面积
    calculate_area(soup)    
    return soup

def normalize_div_areas(soup):
    """
    规范化div的面积:
    1. 当父div只有一个子div且父div面积小于等于子div面积时，保留子div（删除父div）
    2. 确保父div的面积不小于其子div面积之和
    """
    queue = deque([soup])
    while queue:
        current = queue.popleft()
        children = list(current.find_all('div', recursive=False))  # 只获取直接子div
        
        # 先处理子元素
        for child in children:
            queue.append(child)
        
        # 如果当前元素是div，处理其直接子div
        if isinstance(current, bs4.element.Tag) and current.name == 'div':
            current_area = float(current.get('data-area', '0'))
            
            # 1. 当只有一个子div时，检查面积关系
            if len(children) == 1:
                child = children[0]
                child_area = float(child.get('data-area', '0'))
                if current_area <= child_area:
                    # 将子div替换父div
                    current.replace_with(child)
                    continue  # 跳过后续处理，因为当前div已被删除
            
            # 2. 确保父div面积不小于子div面积之和
            remaining_children = current.find_all('div', recursive=False)
            if remaining_children:
                total_children_area = sum(
                    float(child.get('data-area', '0')) 
                    for child in remaining_children
                )
                if current_area < total_children_area:
                    current['data-area'] = str(total_children_area)

    return soup

def build_div_tree(soup):
    """构建div树并同时收集面积值"""
    remove_invalid_divs(soup)
    normalize_div_areas(soup)
    root_div = soup.find('div') # root_div 是一个 bs4.element.Tag 对象，不是列表。
    with open("soup.html", "w", encoding="utf-8") as f:
        f.write(str(soup))
    
    root = DivNode(root_div)
    if not root:
        return None, []
    # DivNode 用于封装 div 元素，方便构建树形结构并存储相关数据（如面积、子节点等），简化了树的遍历和操作。
    queue = deque([root])
    all_areas = []  # 用于收集所有div的面积值
    
    while queue:
        current_node = queue.popleft()
        all_areas.append(current_node.area)  # 收集面积值
        
        for child_div in current_node.div.find_all('div', recursive=False):
            if not child_div or float(child_div.get('data-area', '0')) <= 0:
                continue
            child_node = DivNode(child_div)
            current_node.children.append(child_node)
            queue.append(child_node)
    
    return root, all_areas

def find_max_delta_parent(root, lower_bound, delta_mode='average'):
    """
    找到父子元素面积增量最大的父元素
    delta_mode: 
        'max' - 使用最大增量（父节点面积 - 子节点面积中最大值）
        'average' - 使用平均增量（最大增量 / 子节点数量）
    """
    if not root:
        return None
    
    max_value = 0
    max_parent = None
    
    queue = deque([root])
    
    while queue:
        current_node = queue.popleft()
        
        # 将所有子节点添加到队列，无论当前节点是否有效
        queue.extend(current_node.children)
        
        # 如果当前节点面积小于下界，跳过它
        if current_node.area < lower_bound:
            continue
        
        # 过滤出有效的子节点
        valid_children = [child for child in current_node.children 
                         if child.area >= lower_bound]
        
        # 只有当有有效子节点时才计算delta
        if valid_children:
            children_area = sum(child.area for child in valid_children)
            # 根据模式调整delta计算
            if delta_mode == 'average' and len(valid_children) > 0:
                delta = current_node.area - children_area / len(valid_children)
            elif delta_mode == 'max':
                delta = current_node.area - max(children_area)
            # 只记录正的delta值（父节点面积大于子节点面积总和）
            if delta > max_value:
                max_value = delta
                max_parent = current_node
    
    return max_parent

def process_html_file(file_path, delta_mode='average'):
    """处理HTML文件的主函数"""
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 使用html5lib解析器修复HTML代码
    original_soup = BeautifulSoup(html_content, 'html5lib')
    # 为原始HTML添加唯一ID
    original_soup = add_unique_ids(original_soup)
    # 保存带有ID的原始HTML
    original_html = str(original_soup)
    
    # 删除无效标签和空标签
    for tag in original_soup.find_all():
        if not tag.contents or not tag.get_text(strip=True):
            tag.decompose()
   
    
    # 使用修复后的HTML构建div树并收集面积值
    root, all_areas = build_div_tree(original_soup)
    print("all_areas", all_areas)
    if not root:
        print("无法构建有效的div树")
        return None
    
    # 计算仅过滤小面积异常值（保留大面积）
    sorted_areas = sorted(all_areas)
    n = len(sorted_areas)
    q1 = sorted_areas[int(0.25 * n)]
    q3 = sorted_areas[int(0.75 * n)]
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = float('inf')  # 不设上限
    

    # 找到面积增量最大的父元素
    max_parent = find_max_delta_parent(root, lower_bound, delta_mode)
    
    if max_parent:
        # 获取最大增量div的unique-id
        max_parent_id = max_parent.div.get('data-unique-id')
        # 从原始HTML中找回对应的元素
        original_element = BeautifulSoup(original_html, 'html.parser').find(attrs={'data-unique-id': max_parent_id})
        
        print(f"找到面积增量最大的父元素，其面积为: {max_parent.area}")
        print(f"该元素的HTML内容为: {original_element.prettify()}")
        with open("max_parent.html", "w", encoding="utf-8") as f:
            f.write(original_element.prettify())
        return original_element
    else:
        print("未找到符合条件的父元素")
        return None

if __name__ == "__main__":
    # 测试HTML文件路径
    test_html_path = "./html_files/13.html"
    # 使用示例：计算平均增量
    max_parent = process_html_file(test_html_path, 
                                 delta_mode='average')  # 可切换为'max'
    print("处理完成！")

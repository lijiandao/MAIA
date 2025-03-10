
# HTML Content Extractor

一个基于面积增量算法的智能网页主要内容提取工具。该工具能够自动识别和提取网页中最重要的内容区块，并将其转换为结构化的 Markdown 格式。

## 核心特性

- 🔍 智能识别：使用面积增量算法自动定位网页主要内容区域
- 📝 格式转换：支持将 HTML 内容优雅地转换为 Markdown 格式
- 🎯 精准提取：支持图片、表格、数学公式、代码块等复杂内容的转换
- 🌐 通用性强：适用于各类网页，包括新闻文章、技术文档、博客等
- 🛠 可定制化：支持特殊网站的定制提取规则

## 工作原理

该工具使用创新的面积增量（Delta）算法来识别网页中最重要的内容区块：

1. 构建 DOM 树并计算每个节点的内容面积
2. 使用四分位数（IQR）方法过滤无效区域
3. 计算父子节点间的面积增量，定位最优内容区块
4. 智能保留完整的内容结构，确保提取内容的完整性

## 使用示例

```python
# 从本地HTML文件提取内容
extractor = WebPageExtractor("./example.html")
markdown_content = extractor.save_markdown("output.md")

# 处理单个HTML文件
simplify_single_html(
    html_file_path='./input.html',
    output_file_path='./output.md'
)
```

## 安装依赖

```bash
pip install beautifulsoup4 markdown2 requests
```

## 特殊网站支持

工具内置了对多个特殊网站的支持，可以更精确地提取这些网站的内容：

- 技术文档网站
- 学术论文网站
- 知识分享平台
- 新闻媒体网站

## 贡献指南

欢迎提交 Pull Request 或创建 Issue 来帮助改进这个项目。特别欢迎以下方面的贡献：

- 添加新的特殊网站支持
- 改进内容提取算法
- 优化 Markdown 转换规则
- 修复 bug 和改进性能

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。


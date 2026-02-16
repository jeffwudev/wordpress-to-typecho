# WordPress古腾堡编辑器内容转Markdown脚本使用说明

## 功能说明

将 typecho_contents 表中的 WordPress 古腾堡编辑器格式转换为 Markdown 格式。

支持转换的元素：
- ✓ 代码块（自动识别语言）
- ✓ 标题（H1-H6）
- ✓ 段落
- ✓ 有序列表和无序列表
- ✓ 引用块
- ✓ 图片
- ✓ 加粗、斜体、行内代码
- ✓ 链接

## 使用方法

### 1. 预览单篇文章的转换结果

先找一篇文章测试转换效果：

```bash
# 预览 ID 为 3 的文章
python3 convert_gutenberg_to_markdown.py preview 3
```

这会显示：
- 原始内容（前500字符）
- 转换后内容（前500字符）
- 长度对比

### 2. 预览所有文章（不修改数据库）

查看哪些文章会被转换，不会实际修改数据库：

```bash
python3 convert_gutenberg_to_markdown.py dry-run
```

输出示例：
```
找到 613 篇包含古腾堡块的文章

[1/613] 处理: WordPress禁用指定endpoints，防止用户信息泄露
  预览转换
  原始长度: 1234 字符
  转换后长度: 1150 字符
...
```

### 3. 执行实际转换

确认无误后，执行实际转换：

```bash
python3 convert_gutenberg_to_markdown.py
```

转换特点：
- 每10篇文章提交一次到数据库
- 如果内容没有古腾堡块或已经是Markdown，会自动跳过
- 转换过程中会显示进度
- 安全：转换前会检查，转换失败会保留原内容

## 转换示例

### 代码块转换

**转换前：**
```html
<!-- wp:code {"className":"wp-block-code language-bash","language":"bash"} -->
<pre class="wp-block-code language-bash"><code>sudo apt update
sudo apt install nginx</code></pre>
<!-- /wp:code -->
```

**转换后：**
````markdown
```bash
sudo apt update
sudo apt install nginx
```
````

### 标题转换

**转换前：**
```html
<!-- wp:heading {"level":2} -->
<h2>安装步骤</h2>
<!-- /wp:heading -->
```

**转换后：**
```markdown
## 安装步骤
```

### 列表转换

**转换前：**
```html
<!-- wp:list -->
<ul>
  <li>第一步</li>
  <li>第二步</li>
</ul>
<!-- /wp:list -->
```

**转换后：**
```markdown
- 第一步
- 第二步
```

## 注意事项

1. **备份数据**：转换前确保已备份数据库
2. **测试先行**：先用 `dry-run` 模式测试
3. **不可逆**：转换是直接修改数据库，无法撤销
4. **部分转换**：如果只想转换部分文章，可以修改SQL查询条件
5. **编码问题**：脚本会自动处理HTML实体编码

## 常见问题

### Q: 会影响已经是Markdown的文章吗？
A: 不会。脚本会检查内容是否包含 `<!-- wp:` 块，没有的话会跳过。

### Q: 转换失败怎么办？
A: 如果转换出错，脚本会保留原内容并打印错误信息，不会破坏数据。

### Q: 可以重复运行吗？
A: 可以。转换后的内容不包含古腾堡块标记，重复运行会自动跳过。

### Q: 如何只转换特定分类的文章？
A: 修改脚本中的 SQL 查询，添加分类条件。

## 技术细节

- 自动识别20+种代码语言
- 保留HTML实体解码
- 智能处理嵌套标签
- 支持多行代码块
- 清理多余空行

## 执行流程

```
连接数据库
  ↓
查询包含古腾堡块的文章
  ↓
逐篇处理：
  - 转换代码块
  - 转换标题
  - 转换列表
  - 转换引用
  - 转换图片
  - 清理HTML标签
  ↓
更新数据库（每10篇提交一次）
  ↓
显示统计结果
```

## 相关文件

- `convert_gutenberg_to_markdown.py` - 转换脚本
- `migrate_wordpress_to_typecho.py` - 数据迁移脚本
- `config.inc.php` - Typecho配置文件

# WordPress to Typecho Migration Script

一个将WordPress博客数据迁移到Typecho博客系统的Python脚本。

A Python script to migrate WordPress blog data to Typecho blogging system.

## 功能特性 (Features)

- ✅ 支持WordPress WXR导出文件解析 (Parse WordPress WXR export files)
- ✅ 转换文章和页面 (Convert posts and pages)
- ✅ 转换分类和标签 (Convert categories and tags)
- ✅ 转换评论 (Convert comments)
- ✅ 生成Typecho SQL导入文件 (Generate Typecho SQL import file)
- ✅ 支持自定义表前缀 (Support custom table prefix)
- ✅ 保留文章发布状态 (Preserve post status)

## 系统要求 (Requirements)

- Python 3.6+
- WordPress WXR导出文件 (WordPress WXR export file)
- Typecho 1.0+

## 安装 (Installation)

```bash
# 克隆仓库 (Clone repository)
git clone https://github.com/jeffwudev/wordpress-to-typecho.git
cd wordpress-to-typecho

# 脚本无需额外依赖，直接运行 (No additional dependencies needed)
chmod +x wp2typecho.py
```

## 使用方法 (Usage)

### 1. 从WordPress导出数据 (Export from WordPress)

在WordPress管理后台:
1. 进入 "工具" → "导出" (Tools → Export)
2. 选择 "所有内容" (All content)
3. 点击 "下载导出文件" (Download Export File)
4. 保存WXR文件 (Save WXR file)

### 2. 运行转换脚本 (Run Conversion Script)

基本用法 (Basic usage):
```bash
python3 wp2typecho.py wordpress_export.xml
```

指定输出文件 (Specify output file):
```bash
python3 wp2typecho.py wordpress_export.xml -o my_typecho_import.sql
```

自定义表前缀 (Custom table prefix):
```bash
python3 wp2typecho.py wordpress_export.xml -p my_prefix_
```

查看帮助 (View help):
```bash
python3 wp2typecho.py -h
```

### 3. 导入到Typecho (Import to Typecho)

**方法一：使用phpMyAdmin (Method 1: Using phpMyAdmin)**

1. 登录phpMyAdmin
2. 选择Typecho数据库
3. 点击 "导入" (Import)
4. 上传生成的SQL文件
5. 执行导入

**方法二：使用命令行 (Method 2: Using Command Line)**

```bash
mysql -u username -p database_name < typecho_import.sql
```

## 参数说明 (Parameters)

| 参数 (Parameter) | 说明 (Description) | 默认值 (Default) |
|-----------------|-------------------|-----------------|
| `wxr_file` | WordPress WXR导出文件路径 (Required) | - |
| `-o, --output` | 输出SQL文件路径 | `typecho_import.sql` |
| `-p, --prefix` | Typecho数据库表前缀 | `typecho_` |

## 示例 (Examples)

### 示例1：基本转换 (Example 1: Basic Conversion)

```bash
python3 wp2typecho.py my_wordpress_export.xml
```

输出:
```
==================================================
WordPress to Typecho Migration Script
==================================================
Parsing WordPress export file: my_wordpress_export.xml
Parsed 50 posts, 5 categories, 20 tags
Generating SQL file: typecho_import.sql
SQL file generated successfully: typecho_import.sql
Total posts: 50
Total categories: 5
Total tags: 20
==================================================
Conversion completed successfully!
Import SQL file: typecho_import.sql
==================================================
```

### 示例2：自定义输出和前缀 (Example 2: Custom Output and Prefix)

```bash
python3 wp2typecho.py wordpress.xml -o blog_import.sql -p blog_
```

## 注意事项 (Important Notes)

⚠️ **备份数据库 (Backup Database)**
- 导入前请务必备份Typecho数据库 (Always backup your Typecho database before importing)

⚠️ **表前缀 (Table Prefix)**
- 确保使用正确的表前缀，与Typecho安装时设置的一致 (Ensure correct table prefix matching your Typecho installation)

⚠️ **用户ID (User ID)**
- 所有文章将分配给ID为1的用户 (All posts will be assigned to user with ID 1)
- 请确保该用户存在 (Ensure this user exists)

⚠️ **附件和图片 (Attachments and Images)**
- 本脚本仅转换文本内容 (This script only converts text content)
- 图片和附件需要手动迁移到Typecho的上传目录 (Images and attachments need manual migration)
- 可能需要更新文章中的图片链接 (May need to update image links in posts)

## 数据库结构映射 (Database Structure Mapping)

| WordPress | Typecho | 说明 (Description) |
|-----------|---------|-------------------|
| Posts | contents | 文章和页面 (Posts and pages) |
| Categories | metas (type=category) | 分类 (Categories) |
| Tags | metas (type=tag) | 标签 (Tags) |
| Comments | comments | 评论 (Comments) |

## 故障排除 (Troubleshooting)

### 问题：导入SQL时出错 (Issue: SQL Import Error)

**解决方案 (Solution):**
1. 检查表前缀是否正确 (Check table prefix)
2. 确保Typecho表结构存在 (Ensure Typecho tables exist)
3. 检查MySQL版本兼容性 (Check MySQL version compatibility)

### 问题：中文乱码 (Issue: Chinese Garbled Text)

**解决方案 (Solution):**
1. 确保数据库字符集为UTF-8 (Ensure database charset is UTF-8)
2. 在导入前执行: `SET NAMES utf8mb4;` (Execute before import)

### 问题：文章不显示 (Issue: Posts Not Showing)

**解决方案 (Solution):**
1. 检查文章状态 (Check post status)
2. 清除Typecho缓存 (Clear Typecho cache)
3. 重建索引 (Rebuild index)

## 贡献 (Contributing)

欢迎提交Issue和Pull Request！

Issues and Pull Requests are welcome!

## 许可证 (License)

MIT License - 详见 [LICENSE](LICENSE) 文件

## 作者 (Author)

jeff.wu

## 相关项目 (Related Projects)

- [WordPress](https://wordpress.org/)
- [Typecho](http://typecho.org/)

## 更新日志 (Changelog)

### v1.0.0 (2026-02-16)
- 初始版本发布 (Initial release)
- 支持基本的WordPress到Typecho迁移功能 (Support basic WordPress to Typecho migration)
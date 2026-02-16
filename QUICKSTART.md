# Quick Start Guide | 快速入门指南

## English Version

### Step 1: Export from WordPress
1. Login to WordPress admin panel
2. Go to **Tools** → **Export**
3. Select **All content**
4. Click **Download Export File**

### Step 2: Run Conversion
```bash
python3 wp2typecho.py your_wordpress_export.xml
```

### Step 3: Import to Typecho
```bash
mysql -u username -p database_name < typecho_import.sql
```

That's it! Your blog is migrated.

---

## 中文版本

### 第一步：从WordPress导出
1. 登录WordPress管理后台
2. 进入 **工具** → **导出**
3. 选择 **所有内容**
4. 点击 **下载导出文件**

### 第二步：运行转换脚本
```bash
python3 wp2typecho.py 你的wordpress导出文件.xml
```

### 第三步：导入到Typecho
```bash
mysql -u 用户名 -p 数据库名 < typecho_import.sql
```

完成！你的博客已经迁移成功。

---

## Common Options | 常用选项

### Custom output file | 自定义输出文件
```bash
python3 wp2typecho.py input.xml -o my_output.sql
```

### Custom table prefix | 自定义表前缀
```bash
python3 wp2typecho.py input.xml -p my_prefix_
```

### Get help | 获取帮助
```bash
python3 wp2typecho.py --help
```

---

## Troubleshooting | 故障排除

### Issue: Permission denied | 问题：权限拒绝
**Solution | 解决方案:**
```bash
chmod +x wp2typecho.py
```

### Issue: Module not found | 问题：模块未找到
**Solution | 解决方案:**
Make sure you're using Python 3.6+
```bash
python3 --version
```

### Issue: Database import error | 问题：数据库导入错误
**Solution | 解决方案:**
Check table prefix matches your Typecho installation
```bash
python3 wp2typecho.py input.xml -p your_correct_prefix_
```

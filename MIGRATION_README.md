# WordPress 到 Typecho 数据迁移说明

## 准备工作

### 1. 安装 Python 依赖
```bash
pip3 install pymysql
```

### 2. 备份数据库
在执行迁移前，请确保已经备份了 Typecho 数据库！

## 使用步骤

### 第一步：分析数据库结构
首先运行分析脚本，查看两个数据库的结构和数据情况：

```bash
python3 analyze_db_structure.py
```

这个脚本会显示：
- WordPress 和 Typecho 的表结构
- 各表的记录数
- 文章状态和类型统计
- 数据映射关系说明

### 第二步：执行数据迁移
确认无误后，运行迁移脚本：

```bash
python3 migrate_wordpress_to_typecho.py
```

## 迁移配置

可以在 `migrate_wordpress_to_typecho.py` 文件中修改 `MIGRATION_CONFIG` 配置：

```python
MIGRATION_CONFIG = {
    'migrate_users': True,        # 是否迁移用户
    'migrate_categories': True,   # 是否迁移分类
    'migrate_tags': True,         # 是否迁移标签
    'migrate_posts': True,        # 是否迁移文章
    'migrate_pages': True,        # 是否迁移页面
    'migrate_comments': True,     # 是否迁移评论
    'only_published': True,       # 只迁移已发布的内容
    'default_password': 'typecho123',  # 默认用户密码
}
```

## 迁移内容

脚本会迁移以下内容：

### 1. 用户 (wp_users → typecho_users)
- 用户名、邮箱、URL
- 注册时间
- 显示名称
- ⚠️ 密码会重置为默认密码（需要登录后修改）

### 2. 分类 (wp_terms + wp_term_taxonomy → typecho_metas)
- 分类名称、别名
- 分类描述
- 父子分类关系

### 3. 标签 (wp_terms + wp_term_taxonomy → typecho_metas)
- 标签名称、别名
- 标签描述

### 4. 文章 (wp_posts → typecho_contents)
- 文章标题、内容
- 发布时间、修改时间
- 文章状态（发布、草稿等）
- 评论开关设置
- URL 别名（slug）
- 摘要（如果有）

### 5. 页面 (wp_posts → typecho_contents)
- 页面标题、内容
- 发布时间、修改时间
- 页面排序

### 6. 评论 (wp_comments → typecho_comments)
- 评论内容、作者信息
- 评论时间
- IP 地址和 User Agent
- 父子评论关系

### 7. 关联关系 (wp_term_relationships → typecho_relationships)
- 文章与分类的关联
- 文章与标签的关联

## 注意事项

### 数据格式差异
1. **时间格式**：WordPress 使用 datetime 格式，Typecho 使用 Unix 时间戳
2. **密码加密**：WordPress 使用 bcrypt，Typecho 使用 MD5，因此用户密码会重置
3. **分类标签**：WordPress 分开存储，Typecho 统一存储在 metas 表
4. **URL 别名**：会自动清理特殊字符

### 迁移策略
- 默认只迁移已发布(publish)的内容
- 已存在的数据会被跳过（基于 slug 判断）
- 文章和评论的关联关系会自动维护
- 分类和标签的计数会自动更新

### 安全性
- 脚本会检查重复数据，避免重复导入
- 不会删除 Typecho 中已有的数据
- 建议先在测试环境运行

## 迁移后的工作

1. **登录后台**：使用 WordPress 用户名和默认密码 `typecho123` 登录
2. **修改密码**：立即修改管理员密码
3. **检查内容**：
   - 检查文章是否正确显示
   - 检查分类和标签是否正确关联
   - 检查评论是否正确显示
4. **调整设置**：
   - 设置网站固定链接格式
   - 调整主题设置
   - 检查插件配置
5. **处理附件**：WordPress 的媒体文件需要单独迁移到 Typecho 的 uploads 目录

## 数据库配置

### Typecho 数据库
- 主机: test-db.wujie.me
- 数据库: test_typecho
- 表前缀: typecho_

### WordPress 数据库
- 主机: jsdd.net
- 数据库: www.lwbj.cn
- 表前缀: wp_

## 故障排除

### 连接失败
检查数据库配置信息是否正确，防火墙是否开放端口。

### 编码问题
确保两个数据库都使用 utf8mb4 字符集。

### 数据不完整
检查 WordPress 数据库中的数据状态，确认要迁移的内容存在。

## 统计数据（迁移前）

根据分析脚本的结果：
- WordPress 文章：617 篇（已发布：628 条记录）
- WordPress 页面：5 个
- WordPress 评论：4 条
- WordPress 分类标签：111 个

## 联系支持

如果在迁移过程中遇到问题，请检查：
1. 脚本输出的错误信息
2. 数据库连接是否正常
3. 表结构是否完整

## 版本信息

- 创建日期：2026-02-10
- Python 版本：3.x
- 依赖：pymysql

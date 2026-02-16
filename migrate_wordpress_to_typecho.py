#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress 到 Typecho 数据迁移脚本
将WordPress网站的内容完整迁移到Typecho系统
"""

import pymysql
import time
import hashlib
from datetime import datetime
import re

# 数据库配置
WORDPRESS_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'wordpress_db',
    'charset': 'utf8mb4'
}

TYPECHO_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'your_username',
    'password': 'your_password',
    'database': 'typecho_db',
    'charset': 'utf8mb4'
}

# 迁移配置
MIGRATION_CONFIG = {
    'migrate_users': False,       # 是否迁移用户
    'migrate_categories': True,   # 是否迁移分类
    'migrate_tags': True,         # 是否迁移标签
    'migrate_posts': True,        # 是否迁移文章
    'migrate_pages': True,        # 是否迁移页面
    'migrate_comments': False,     # 是否迁移评论
    'only_published': True,       # 只迁移已发布的内容
    'default_password': 'typecho123',  # 默认用户密码
}

class WordPressToTypechoMigrator:
    def __init__(self):
        self.wp_conn = None
        self.typecho_conn = None
        self.user_map = {}      # WordPress用户ID -> Typecho用户ID
        self.post_map = {}      # WordPress文章ID -> Typecho文章ID
        self.term_map = {}      # WordPress分类/标签ID -> Typecho分类/标签ID
        self.stats = {
            'users': 0,
            'categories': 0,
            'tags': 0,
            'posts': 0,
            'pages': 0,
            'comments': 0,
        }
    
    def connect_databases(self):
        """连接数据库"""
        print("正在连接数据库...")
        self.wp_conn = pymysql.connect(**WORDPRESS_CONFIG)
        self.typecho_conn = pymysql.connect(**TYPECHO_CONFIG)
        print("✓ 数据库连接成功\n")
    
    def close_databases(self):
        """关闭数据库连接"""
        if self.wp_conn:
            self.wp_conn.close()
        if self.typecho_conn:
            self.typecho_conn.close()
    
    def datetime_to_timestamp(self, dt_input):
        """将datetime字符串或对象转换为Unix时间戳"""
        if not dt_input:
            return int(time.time())
        
        try:
            # 如果已经是datetime对象，直接使用
            if isinstance(dt_input, datetime):
                dt = dt_input
            # 如果是字符串，需要转换
            elif isinstance(dt_input, str):
                if dt_input == '0000-00-00 00:00:00':
                    return int(time.time())
                dt = datetime.strptime(dt_input, '%Y-%m-%d %H:%M:%S')
            else:
                return int(time.time())
            
            # 使用 time.mktime 确保将本地时间正确转换为时间戳
            import time as time_module
            return int(time_module.mktime(dt.timetuple()))
        except Exception as e:
            print(f"  警告: 时间转换失败 ({dt_input}): {e}")
            return int(time.time())
    
    def generate_typecho_password(self, password):
        """生成Typecho格式的密码哈希"""
        # Typecho使用md5加密
        return hashlib.md5(password.encode()).hexdigest()
    
    def clean_slug(self, slug):
        """清理URL别名"""
        if not slug:
            return ''
        # 移除特殊字符，只保留字母数字和连字符
        slug = re.sub(r'[^\w\-]', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')
    
    def migrate_users(self):
        """迁移用户"""
        if not MIGRATION_CONFIG['migrate_users']:
            print("跳过用户迁移")
            return
        
        print("=" * 60)
        print("开始迁移用户...")
        print("=" * 60)
        
        wp_cursor = self.wp_conn.cursor(pymysql.cursors.DictCursor)
        typecho_cursor = self.typecho_conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取WordPress用户
        wp_cursor.execute("SELECT * FROM wp_users")
        wp_users = wp_cursor.fetchall()
        
        for wp_user in wp_users:
            # 检查用户是否已存在
            typecho_cursor.execute(
                "SELECT uid FROM typecho_users WHERE name = %s OR mail = %s",
                (wp_user['user_login'], wp_user['user_email'])
            )
            existing = typecho_cursor.fetchone()
            
            if existing:
                self.user_map[wp_user['ID']] = existing['uid']
                print(f"用户已存在: {wp_user['user_login']} (跳过)")
                continue
            
            # 插入Typecho用户
            created = self.datetime_to_timestamp(wp_user['user_registered'])
            password = self.generate_typecho_password(MIGRATION_CONFIG['default_password'])
            
            insert_sql = """
                INSERT INTO typecho_users 
                (name, password, mail, url, screenName, created, activated, logged, `group`, authCode)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            typecho_cursor.execute(insert_sql, (
                wp_user['user_login'],
                password,
                wp_user['user_email'],
                wp_user['user_url'] or '',
                wp_user['display_name'] or wp_user['user_login'],
                created,
                created,
                created,
                'administrator',
                ''
            ))
            
            new_uid = typecho_cursor.lastrowid
            self.user_map[wp_user['ID']] = new_uid
            self.stats['users'] += 1
            
            print(f"✓ 迁移用户: {wp_user['user_login']} (ID: {wp_user['ID']} -> {new_uid})")
        
        self.typecho_conn.commit()
        print(f"\n用户迁移完成: {self.stats['users']} 个用户\n")
    
    def migrate_categories(self):
        """迁移分类"""
        if not MIGRATION_CONFIG['migrate_categories']:
            print("跳过分类迁移")
            return
        
        print("=" * 60)
        print("开始迁移分类...")
        print("=" * 60)
        
        wp_cursor = self.wp_conn.cursor(pymysql.cursors.DictCursor)
        typecho_cursor = self.typecho_conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取WordPress分类
        wp_cursor.execute("""
            SELECT t.term_id, t.name, t.slug, tt.description, tt.parent
            FROM wp_terms t
            INNER JOIN wp_term_taxonomy tt ON t.term_id = tt.term_id
            WHERE tt.taxonomy = 'category'
            ORDER BY tt.parent, t.term_id
        """)
        wp_categories = wp_cursor.fetchall()
        
        for wp_cat in wp_categories:
            # 检查分类是否已存在
            typecho_cursor.execute(
                "SELECT mid FROM typecho_metas WHERE type = 'category' AND slug = %s",
                (wp_cat['slug'],)
            )
            existing = typecho_cursor.fetchone()
            
            if existing:
                self.term_map[wp_cat['term_id']] = existing['mid']
                print(f"分类已存在: {wp_cat['name']} (跳过)")
                continue
            
            # 处理父分类
            parent = 0
            if wp_cat['parent'] and wp_cat['parent'] in self.term_map:
                parent = self.term_map[wp_cat['parent']]
            
            # 插入Typecho分类
            insert_sql = """
                INSERT INTO typecho_metas 
                (name, slug, type, description, count, `order`, parent)
                VALUES (%s, %s, 'category', %s, 0, 0, %s)
            """
            
            typecho_cursor.execute(insert_sql, (
                wp_cat['name'],
                self.clean_slug(wp_cat['slug']),
                wp_cat['description'] or '',
                parent
            ))
            
            new_mid = typecho_cursor.lastrowid
            self.term_map[wp_cat['term_id']] = new_mid
            self.stats['categories'] += 1
            
            print(f"✓ 迁移分类: {wp_cat['name']} (ID: {wp_cat['term_id']} -> {new_mid})")
        
        self.typecho_conn.commit()
        print(f"\n分类迁移完成: {self.stats['categories']} 个分类\n")
    
    def migrate_tags(self):
        """迁移标签"""
        if not MIGRATION_CONFIG['migrate_tags']:
            print("跳过标签迁移")
            return
        
        print("=" * 60)
        print("开始迁移标签...")
        print("=" * 60)
        
        wp_cursor = self.wp_conn.cursor(pymysql.cursors.DictCursor)
        typecho_cursor = self.typecho_conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取WordPress标签
        wp_cursor.execute("""
            SELECT t.term_id, t.name, t.slug, tt.description
            FROM wp_terms t
            INNER JOIN wp_term_taxonomy tt ON t.term_id = tt.term_id
            WHERE tt.taxonomy = 'post_tag'
        """)
        wp_tags = wp_cursor.fetchall()
        
        for wp_tag in wp_tags:
            # 检查标签是否已存在
            typecho_cursor.execute(
                "SELECT mid FROM typecho_metas WHERE type = 'tag' AND slug = %s",
                (wp_tag['slug'],)
            )
            existing = typecho_cursor.fetchone()
            
            if existing:
                self.term_map[wp_tag['term_id']] = existing['mid']
                print(f"标签已存在: {wp_tag['name']} (跳过)")
                continue
            
            # 插入Typecho标签
            insert_sql = """
                INSERT INTO typecho_metas 
                (name, slug, type, description, count, `order`, parent)
                VALUES (%s, %s, 'tag', %s, 0, 0, 0)
            """
            
            typecho_cursor.execute(insert_sql, (
                wp_tag['name'],
                self.clean_slug(wp_tag['slug']),
                wp_tag['description'] or ''
            ))
            
            new_mid = typecho_cursor.lastrowid
            self.term_map[wp_tag['term_id']] = new_mid
            self.stats['tags'] += 1
            
            print(f"✓ 迁移标签: {wp_tag['name']} (ID: {wp_tag['term_id']} -> {new_mid})")
        
        self.typecho_conn.commit()
        print(f"\n标签迁移完成: {self.stats['tags']} 个标签\n")
    
    def migrate_posts(self):
        """迁移文章"""
        if not MIGRATION_CONFIG['migrate_posts']:
            print("跳过文章迁移")
            return
        
        print("=" * 60)
        print("开始迁移文章...")
        print("=" * 60)
        
        wp_cursor = self.wp_conn.cursor(pymysql.cursors.DictCursor)
        typecho_cursor = self.typecho_conn.cursor(pymysql.cursors.DictCursor)
        
        # 构建查询条件
        status_condition = "AND post_status = 'publish'" if MIGRATION_CONFIG['only_published'] else ""
        
        # 获取WordPress文章
        wp_cursor.execute(f"""
            SELECT * FROM wp_posts 
            WHERE post_type = 'post' {status_condition}
            ORDER BY ID
        """)
        wp_posts = wp_cursor.fetchall()
        
        for wp_post in wp_posts:
            # 检查文章是否已存在
            typecho_cursor.execute(
                "SELECT cid FROM typecho_contents WHERE slug = %s AND type = 'post'",
                (wp_post['post_name'],)
            )
            existing = typecho_cursor.fetchone()
            
            if existing:
                self.post_map[wp_post['ID']] = existing['cid']
                print(f"文章已存在: {wp_post['post_title'][:30]} (跳过)")
                continue
            
            # 获取作者ID
            author_id = self.user_map.get(wp_post['post_author'], 1)
            
            # 转换时间戳
            created = self.datetime_to_timestamp(wp_post['post_date'])
            modified = self.datetime_to_timestamp(wp_post['post_modified'])
            
            # 转换状态
            status_map = {
                'publish': 'publish',
                'draft': 'draft',
                'private': 'private',
                'pending': 'waiting'
            }
            status = status_map.get(wp_post['post_status'], 'draft')
            
            # 插入Typecho文章
            insert_sql = """
                INSERT INTO typecho_contents 
                (title, slug, created, modified, text, `order`, authorId, template, 
                type, status, password, commentsNum, allowComment, allowPing, allowFeed, parent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # 合并内容
            text = wp_post['post_content']
            if wp_post['post_excerpt']:
                text = f"<!--markdown-->\n{wp_post['post_excerpt']}\n\n<!--more-->\n\n{text}"
            
            typecho_cursor.execute(insert_sql, (
                wp_post['post_title'],
                self.clean_slug(wp_post['post_name']) or f"post-{wp_post['ID']}",
                created,
                modified,
                text,
                0,
                author_id,
                '',
                'post',
                status,
                wp_post['post_password'] or '',
                wp_post['comment_count'],
                '1' if wp_post['comment_status'] == 'open' else '0',
                '1' if wp_post['ping_status'] == 'open' else '0',
                '1',
                0
            ))
            
            new_cid = typecho_cursor.lastrowid
            self.post_map[wp_post['ID']] = new_cid
            self.stats['posts'] += 1
            
            # 迁移分类和标签关联
            self.migrate_post_terms(wp_post['ID'], new_cid)
            
            print(f"✓ 迁移文章: {wp_post['post_title'][:40]} (ID: {wp_post['ID']} -> {new_cid})")
            
            # 每10篇文章提交一次
            if self.stats['posts'] % 10 == 0:
                self.typecho_conn.commit()
                print(f"  [已提交 {self.stats['posts']} 篇]")
        
        self.typecho_conn.commit()
        print(f"\n文章迁移完成: {self.stats['posts']} 篇文章\n")
    
    def migrate_pages(self):
        """迁移页面"""
        if not MIGRATION_CONFIG['migrate_pages']:
            print("跳过页面迁移")
            return
        
        print("=" * 60)
        print("开始迁移页面...")
        print("=" * 60)
        
        wp_cursor = self.wp_conn.cursor(pymysql.cursors.DictCursor)
        typecho_cursor = self.typecho_conn.cursor(pymysql.cursors.DictCursor)
        
        # 构建查询条件
        status_condition = "AND post_status = 'publish'" if MIGRATION_CONFIG['only_published'] else ""
        
        # 获取WordPress页面
        wp_cursor.execute(f"""
            SELECT * FROM wp_posts 
            WHERE post_type = 'page' {status_condition}
            ORDER BY ID
        """)
        wp_pages = wp_cursor.fetchall()
        
        for wp_page in wp_pages:
            # 检查页面是否已存在
            typecho_cursor.execute(
                "SELECT cid FROM typecho_contents WHERE slug = %s AND type = 'page'",
                (wp_page['post_name'],)
            )
            existing = typecho_cursor.fetchone()
            
            if existing:
                self.post_map[wp_page['ID']] = existing['cid']
                print(f"页面已存在: {wp_page['post_title'][:30]} (跳过)")
                continue
            
            # 获取作者ID
            author_id = self.user_map.get(wp_page['post_author'], 1)
            
            # 转换时间戳
            created = self.datetime_to_timestamp(wp_page['post_date'])
            modified = self.datetime_to_timestamp(wp_page['post_modified'])
            
            # 转换状态
            status_map = {
                'publish': 'publish',
                'draft': 'draft',
                'private': 'private',
                'pending': 'waiting'
            }
            status = status_map.get(wp_page['post_status'], 'draft')
            
            # 插入Typecho页面
            insert_sql = """
                INSERT INTO typecho_contents 
                (title, slug, created, modified, text, `order`, authorId, template, 
                type, status, password, commentsNum, allowComment, allowPing, allowFeed, parent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            typecho_cursor.execute(insert_sql, (
                wp_page['post_title'],
                self.clean_slug(wp_page['post_name']) or f"page-{wp_page['ID']}",
                created,
                modified,
                wp_page['post_content'],
                wp_page['menu_order'],
                author_id,
                '',
                'page',
                status,
                wp_page['post_password'] or '',
                wp_page['comment_count'],
                '1' if wp_page['comment_status'] == 'open' else '0',
                '1' if wp_page['ping_status'] == 'open' else '0',
                '1',
                0
            ))
            
            new_cid = typecho_cursor.lastrowid
            self.post_map[wp_page['ID']] = new_cid
            self.stats['pages'] += 1
            
            print(f"✓ 迁移页面: {wp_page['post_title'][:40]} (ID: {wp_page['ID']} -> {new_cid})")
            
            # 每处理5个页面提交一次
            if self.stats['pages'] % 5 == 0:
                self.typecho_conn.commit()
                print(f"  [已提交 {self.stats['pages']} 个页面]")
        
        self.typecho_conn.commit()
        print(f"\n页面迁移完成: {self.stats['pages']} 个页面\n")
    
    def migrate_post_terms(self, wp_post_id, typecho_cid):
        """迁移文章的分类和标签关联"""
        wp_cursor = self.wp_conn.cursor(pymysql.cursors.DictCursor)
        typecho_cursor = self.typecho_conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取WordPress文章的分类和标签
        wp_cursor.execute("""
            SELECT tt.term_id
            FROM wp_term_relationships tr
            INNER JOIN wp_term_taxonomy tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
            WHERE tr.object_id = %s AND tt.taxonomy IN ('category', 'post_tag')
        """, (wp_post_id,))
        
        terms = wp_cursor.fetchall()
        
        for term in terms:
            if term['term_id'] in self.term_map:
                typecho_mid = self.term_map[term['term_id']]
                
                # 检查关联是否已存在
                typecho_cursor.execute(
                    "SELECT * FROM typecho_relationships WHERE cid = %s AND mid = %s",
                    (typecho_cid, typecho_mid)
                )
                
                if not typecho_cursor.fetchone():
                    # 插入关联
                    typecho_cursor.execute(
                        "INSERT INTO typecho_relationships (cid, mid) VALUES (%s, %s)",
                        (typecho_cid, typecho_mid)
                    )
                    
                    # 更新分类/标签的文章计数
                    typecho_cursor.execute(
                        "UPDATE typecho_metas SET count = count + 1 WHERE mid = %s",
                        (typecho_mid,)
                    )
    
    def migrate_comments(self):
        """迁移评论"""
        if not MIGRATION_CONFIG['migrate_comments']:
            print("跳过评论迁移")
            return
        
        print("=" * 60)
        print("开始迁移评论...")
        print("=" * 60)
        
        wp_cursor = self.wp_conn.cursor(pymysql.cursors.DictCursor)
        typecho_cursor = self.typecho_conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取WordPress评论
        wp_cursor.execute("""
            SELECT * FROM wp_comments 
            WHERE comment_approved = '1'
            ORDER BY comment_ID
        """)
        wp_comments = wp_cursor.fetchall()
        
        for wp_comment in wp_comments:
            # 获取对应的文章ID
            if wp_comment['comment_post_ID'] not in self.post_map:
                continue
            
            typecho_cid = self.post_map[wp_comment['comment_post_ID']]
            
            # 转换时间戳
            created = self.datetime_to_timestamp(wp_comment['comment_date'])
            
            # 获取作者ID
            author_id = self.user_map.get(wp_comment['user_id'], 0) if wp_comment['user_id'] else 0
            
            # 处理父评论
            parent = 0
            if wp_comment['comment_parent']:
                # 需要查找对应的Typecho评论ID
                typecho_cursor.execute(
                    "SELECT coid FROM typecho_comments WHERE text LIKE %s LIMIT 1",
                    (f"%{wp_comment['comment_content'][:50]}%",)
                )
                parent_result = typecho_cursor.fetchone()
                if parent_result:
                    parent = parent_result['coid']
            
            # 插入Typecho评论
            insert_sql = """
                INSERT INTO typecho_comments 
                (cid, created, author, authorId, ownerId, mail, url, ip, agent, 
                text, type, status, parent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            typecho_cursor.execute(insert_sql, (
                typecho_cid,
                created,
                wp_comment['comment_author'],
                author_id,
                author_id,
                wp_comment['comment_author_email'],
                wp_comment['comment_author_url'],
                wp_comment['comment_author_IP'],
                wp_comment['comment_agent'],
                wp_comment['comment_content'],
                'comment',
                'approved',
                parent
            ))
            
            self.stats['comments'] += 1
            
            # 更新文章评论数
            typecho_cursor.execute(
                "UPDATE typecho_contents SET commentsNum = commentsNum + 1 WHERE cid = %s",
                (typecho_cid,)
            )
            
            print(f"✓ 迁移评论: {wp_comment['comment_author']} 的评论 (ID: {wp_comment['comment_ID']})")
            
            # 每处理5条评论提交一次
            if self.stats['comments'] % 5 == 0:
                self.typecho_conn.commit()
                print(f"  [已提交 {self.stats['comments']} 条评论]")
        
        self.typecho_conn.commit()
        print(f"\n评论迁移完成: {self.stats['comments']} 条评论\n")
    
    def print_summary(self):
        """打印迁移摘要"""
        print("\n" + "=" * 60)
        print("迁移完成！统计信息：")
        print("=" * 60)
        print(f"用户:   {self.stats['users']} 个")
        print(f"分类:   {self.stats['categories']} 个")
        print(f"标签:   {self.stats['tags']} 个")
        print(f"文章:   {self.stats['posts']} 篇")
        print(f"页面:   {self.stats['pages']} 个")
        print(f"评论:   {self.stats['comments']} 条")
        print("=" * 60)
        print(f"\n提示: 默认用户密码为: {MIGRATION_CONFIG['default_password']}")
        print("请登录后台修改密码！\n")
    
    def run(self):
        """执行迁移"""
        try:
            start_time = time.time()
            print("\n" + "=" * 60)
            print("WordPress 到 Typecho 数据迁移")
            print("=" * 60)
            print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            self.connect_databases()
            
            # 按顺序执行迁移
            self.migrate_users()
            self.migrate_categories()
            self.migrate_tags()
            self.migrate_posts()
            self.migrate_pages()
            self.migrate_comments()
            
            # 打印摘要
            elapsed_time = time.time() - start_time
            self.print_summary()
            print(f"总耗时: {elapsed_time:.2f} 秒\n")
            
        except Exception as e:
            print(f"\n错误: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.close_databases()

if __name__ == "__main__":
    migrator = WordPressToTypechoMigrator()
    migrator.run()

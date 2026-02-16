#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移预览脚本 - 在实际迁移前查看将要导入的数据
"""

import pymysql
from datetime import datetime

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

def preview_migration():
    """预览将要迁移的数据"""
    print("=" * 70)
    print("WordPress 到 Typecho 迁移预览")
    print("=" * 70)
    print()
    
    # 连接WordPress数据库
    wp_conn = pymysql.connect(**WORDPRESS_CONFIG)
    wp_cursor = wp_conn.cursor(pymysql.cursors.DictCursor)
    
    # 连接Typecho数据库
    typecho_conn = pymysql.connect(**TYPECHO_CONFIG)
    typecho_cursor = typecho_conn.cursor(pymysql.cursors.DictCursor)
    
    print("【WordPress 数据统计】")
    print("-" * 70)
    
    # 用户统计
    wp_cursor.execute("SELECT COUNT(*) as count FROM wp_users")
    user_count = wp_cursor.fetchone()['count']
    print(f"✓ 用户: {user_count} 个")
    
    # 分类统计
    wp_cursor.execute("""
        SELECT COUNT(*) as count FROM wp_term_taxonomy 
        WHERE taxonomy = 'category'
    """)
    cat_count = wp_cursor.fetchone()['count']
    print(f"✓ 分类: {cat_count} 个")
    
    # 标签统计
    wp_cursor.execute("""
        SELECT COUNT(*) as count FROM wp_term_taxonomy 
        WHERE taxonomy = 'post_tag'
    """)
    tag_count = wp_cursor.fetchone()['count']
    print(f"✓ 标签: {tag_count} 个")
    
    # 已发布文章统计
    wp_cursor.execute("""
        SELECT COUNT(*) as count FROM wp_posts 
        WHERE post_type = 'post' AND post_status = 'publish'
    """)
    post_count = wp_cursor.fetchone()['count']
    print(f"✓ 已发布文章: {post_count} 篇")
    
    # 草稿文章统计
    wp_cursor.execute("""
        SELECT COUNT(*) as count FROM wp_posts 
        WHERE post_type = 'post' AND post_status = 'draft'
    """)
    draft_count = wp_cursor.fetchone()['count']
    print(f"  草稿文章: {draft_count} 篇 (不会迁移)")
    
    # 已发布页面统计
    wp_cursor.execute("""
        SELECT COUNT(*) as count FROM wp_posts 
        WHERE post_type = 'page' AND post_status = 'publish'
    """)
    page_count = wp_cursor.fetchone()['count']
    print(f"✓ 已发布页面: {page_count} 个")
    
    # 评论统计
    wp_cursor.execute("""
        SELECT COUNT(*) as count FROM wp_comments 
        WHERE comment_approved = '1'
    """)
    comment_count = wp_cursor.fetchone()['count']
    print(f"✓ 已审核评论: {comment_count} 条")
    
    print()
    print("【Typecho 当前数据】")
    print("-" * 70)
    
    # Typecho现有数据
    typecho_cursor.execute("SELECT COUNT(*) as count FROM typecho_users")
    te_user_count = typecho_cursor.fetchone()['count']
    print(f"现有用户: {te_user_count} 个")
    
    typecho_cursor.execute("""
        SELECT COUNT(*) as count FROM typecho_metas WHERE type = 'category'
    """)
    te_cat_count = typecho_cursor.fetchone()['count']
    print(f"现有分类: {te_cat_count} 个")
    
    typecho_cursor.execute("""
        SELECT COUNT(*) as count FROM typecho_metas WHERE type = 'tag'
    """)
    te_tag_count = typecho_cursor.fetchone()['count']
    print(f"现有标签: {te_tag_count} 个")
    
    typecho_cursor.execute("""
        SELECT COUNT(*) as count FROM typecho_contents WHERE type = 'post'
    """)
    te_post_count = typecho_cursor.fetchone()['count']
    print(f"现有文章: {te_post_count} 篇")
    
    typecho_cursor.execute("""
        SELECT COUNT(*) as count FROM typecho_contents WHERE type = 'page'
    """)
    te_page_count = typecho_cursor.fetchone()['count']
    print(f"现有页面: {te_page_count} 个")
    
    typecho_cursor.execute("SELECT COUNT(*) as count FROM typecho_comments")
    te_comment_count = typecho_cursor.fetchone()['count']
    print(f"现有评论: {te_comment_count} 条")
    
    print()
    print("【预计迁移数据】")
    print("-" * 70)
    print(f"将迁移 {user_count} 个用户")
    print(f"将迁移 {cat_count} 个分类")
    print(f"将迁移 {tag_count} 个标签")
    print(f"将迁移 {post_count} 篇文章")
    print(f"将迁移 {page_count} 个页面")
    print(f"将迁移 {comment_count} 条评论")
    
    print()
    print("【迁移后预计数据】")
    print("-" * 70)
    print(f"用户总数: {te_user_count + user_count} 个（现有 + 新增）")
    print(f"分类总数: {te_cat_count + cat_count} 个（现有 + 新增）")
    print(f"标签总数: {te_tag_count + tag_count} 个（现有 + 新增）")
    print(f"文章总数: {te_post_count + post_count} 篇（现有 + 新增）")
    print(f"页面总数: {te_page_count + page_count} 个（现有 + 新增）")
    print(f"评论总数: {te_comment_count + comment_count} 条（现有 + 新增）")
    
    print()
    print("【最近的文章预览】")
    print("-" * 70)
    wp_cursor.execute("""
        SELECT post_title, post_date, post_status, comment_count 
        FROM wp_posts 
        WHERE post_type = 'post' AND post_status = 'publish'
        ORDER BY post_date DESC 
        LIMIT 10
    """)
    recent_posts = wp_cursor.fetchall()
    
    for i, post in enumerate(recent_posts, 1):
        print(f"{i}. {post['post_title'][:50]}")
        print(f"   发布: {post['post_date']} | 评论: {post['comment_count']}")
    
    print()
    print("【注意事项】")
    print("-" * 70)
    print("⚠️  已存在的数据不会重复导入（基于 slug 判断）")
    print("⚠️  用户密码将被重置为默认密码: typecho123")
    print("⚠️  只会迁移已发布(publish)的文章和页面")
    print("⚠️  WordPress 的媒体文件需要单独迁移")
    print("✓  迁移不会删除 Typecho 现有数据")
    print("✓  可以安全地重复运行迁移脚本")
    
    print()
    print("=" * 70)
    print("预览完成！如果确认无误，请运行迁移脚本：")
    print("python3 migrate_wordpress_to_typecho.py")
    print("=" * 70)
    print()
    
    wp_conn.close()
    typecho_conn.close()

if __name__ == "__main__":
    try:
        preview_migration()
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()

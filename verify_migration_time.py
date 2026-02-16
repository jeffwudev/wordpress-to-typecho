#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证文章发布时间是否正确迁移
"""

import pymysql
from datetime import datetime

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

def verify_time():
    """验证时间迁移"""
    wp_conn = pymysql.connect(**WORDPRESS_CONFIG)
    typecho_conn = pymysql.connect(**TYPECHO_CONFIG)
    
    wp_cursor = wp_conn.cursor(pymysql.cursors.DictCursor)
    typecho_cursor = typecho_conn.cursor(pymysql.cursors.DictCursor)
    
    print("=" * 80)
    print("文章发布时间对比验证")
    print("=" * 80)
    print()
    
    # 获取最近5篇WordPress文章
    wp_cursor.execute("""
        SELECT ID, post_title, post_date, post_modified
        FROM wp_posts 
        WHERE post_type = 'post' AND post_status = 'publish'
        ORDER BY post_date DESC 
        LIMIT 5
    """)
    wp_posts = wp_cursor.fetchall()
    
    print(f"{'WordPress标题':<40} {'发布时间':<20} {'Typecho时间':<20} {'状态':<10}")
    print("-" * 80)
    
    for wp_post in wp_posts:
        # 查找对应的Typecho文章
        typecho_cursor.execute("""
            SELECT title, created, modified 
            FROM typecho_contents 
            WHERE title = %s AND type = 'post'
            LIMIT 1
        """, (wp_post['post_title'],))
        
        typecho_post = typecho_cursor.fetchone()
        
        if typecho_post:
            # 将WordPress时间转换为时间戳进行比较
            wp_timestamp = int(datetime.strptime(
                str(wp_post['post_date']), 
                '%Y-%m-%d %H:%M:%S'
            ).timestamp())
            
            typecho_timestamp = typecho_post['created']
            
            # 比较时间差（允许1秒误差）
            time_diff = abs(wp_timestamp - typecho_timestamp)
            status = "✓ 正确" if time_diff <= 1 else f"✗ 偏差{time_diff}秒"
            
            # 转换Typecho时间戳为可读格式
            typecho_dt = datetime.fromtimestamp(typecho_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"{wp_post['post_title'][:38]:<40} {str(wp_post['post_date']):<20} {typecho_dt:<20} {status:<10}")
        else:
            print(f"{wp_post['post_title'][:38]:<40} {str(wp_post['post_date']):<20} {'未找到':<20} {'✗ 缺失':<10}")
    
    print()
    print("=" * 80)
    
    wp_conn.close()
    typecho_conn.close()

if __name__ == "__main__":
    try:
        verify_time()
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

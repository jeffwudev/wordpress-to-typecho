#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress 到 Typecho 数据库结构分析脚本
分析两个数据库的表结构，为数据迁移做准备
"""

import pymysql
import json
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

def get_db_connection(config):
    """创建数据库连接"""
    return pymysql.connect(**config)

def get_table_structure(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(f"DESCRIBE {table_name}")
    return cursor.fetchall()

def get_table_count(conn, table_name):
    """获取表记录数"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cursor.fetchone()[0]

def analyze_wordpress():
    """分析WordPress数据库"""
    print("=" * 60)
    print("分析 WordPress 数据库结构")
    print("=" * 60)
    
    conn = get_db_connection(WORDPRESS_CONFIG)
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    
    print(f"\n找到 {len(tables)} 个表:\n")
    
    # 重点关注的表
    key_tables = ['wp_posts', 'wp_comments', 'wp_users', 'wp_terms', 
                  'wp_term_taxonomy', 'wp_term_relationships']
    
    for table in tables:
        if any(key_word in table for key_word in ['post', 'comment', 'user', 'term', 'meta']):
            count = get_table_count(conn, table)
            print(f"{table}: {count} 条记录")
            
            if table in key_tables:
                print(f"  结构:")
                structure = get_table_structure(conn, table)
                for field in structure[:10]:  # 只显示前10个字段
                    print(f"    - {field['Field']}: {field['Type']}")
                if len(structure) > 10:
                    print(f"    ... 还有 {len(structure) - 10} 个字段")
                print()
    
    # 分析文章状态
    cursor.execute("SELECT post_status, COUNT(*) as count FROM wp_posts GROUP BY post_status")
    print("\n文章状态统计:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # 分析文章类型
    cursor.execute("SELECT post_type, COUNT(*) as count FROM wp_posts GROUP BY post_type")
    print("\n文章类型统计:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    conn.close()

def analyze_typecho():
    """分析Typecho数据库"""
    print("\n" + "=" * 60)
    print("分析 Typecho 数据库结构")
    print("=" * 60)
    
    conn = get_db_connection(TYPECHO_CONFIG)
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    
    print(f"\n找到 {len(tables)} 个表:\n")
    
    # 重点关注的表
    key_tables = ['typecho_contents', 'typecho_comments', 'typecho_users', 
                  'typecho_metas', 'typecho_relationships']
    
    for table in tables:
        count = get_table_count(conn, table)
        print(f"{table}: {count} 条记录")
        
        if table in key_tables:
            print(f"  结构:")
            structure = get_table_structure(conn, table)
            for field in structure:
                print(f"    - {field['Field']}: {field['Type']}")
            print()
    
    conn.close()

def analyze_mapping():
    """分析字段映射关系"""
    print("\n" + "=" * 60)
    print("数据库映射分析")
    print("=" * 60)
    
    mapping = {
        "文章数据": {
            "WordPress": "wp_posts",
            "Typecho": "typecho_contents",
            "说明": "文章、页面等内容"
        },
        "评论数据": {
            "WordPress": "wp_comments",
            "Typecho": "typecho_comments",
            "说明": "用户评论"
        },
        "用户数据": {
            "WordPress": "wp_users",
            "Typecho": "typecho_users",
            "说明": "用户信息"
        },
        "分类标签": {
            "WordPress": "wp_terms + wp_term_taxonomy",
            "Typecho": "typecho_metas",
            "说明": "分类和标签统一存储"
        },
        "关联关系": {
            "WordPress": "wp_term_relationships",
            "Typecho": "typecho_relationships",
            "说明": "内容与分类/标签的关联"
        }
    }
    
    print("\n主要数据表映射关系:\n")
    for key, value in mapping.items():
        print(f"{key}:")
        print(f"  WordPress: {value['WordPress']}")
        print(f"  Typecho: {value['Typecho']}")
        print(f"  说明: {value['说明']}\n")

if __name__ == "__main__":
    try:
        print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        analyze_wordpress()
        analyze_typecho()
        analyze_mapping()
        
        print("\n" + "=" * 60)
        print("分析完成！")
        print("=" * 60)
        print("\n提示: 请根据以上分析结果检查数据迁移方案")
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()

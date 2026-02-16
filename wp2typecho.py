#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress to Typecho Migration Script
Converts WordPress WXR export file to Typecho SQL import format
"""

import xml.etree.ElementTree as ET
import argparse
import sys
import html
import re
from datetime import datetime


class WP2Typecho:
    """Main converter class for WordPress to Typecho migration"""
    
    def __init__(self, wxr_file, output_file='typecho_import.sql', table_prefix='typecho_'):
        self.wxr_file = wxr_file
        self.output_file = output_file
        self.table_prefix = table_prefix
        self.posts = []
        self.categories = []
        self.tags = []
        self.comments = []
        
        # WordPress namespaces
        self.namespaces = {
            'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'wfw': 'http://wellformedweb.org/CommentAPI/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'wp': 'http://wordpress.org/export/1.2/'
        }
    
    def parse_wxr(self):
        """Parse WordPress WXR export file"""
        print(f"Parsing WordPress export file: {self.wxr_file}")
        
        try:
            tree = ET.parse(self.wxr_file)
            root = tree.getroot()
            
            # Parse categories
            for category in root.findall('.//wp:category', self.namespaces):
                cat_data = {
                    'slug': category.find('wp:category_nicename', self.namespaces).text,
                    'name': category.find('wp:cat_name', self.namespaces).text,
                    'parent': category.find('wp:category_parent', self.namespaces).text or ''
                }
                self.categories.append(cat_data)
            
            # Parse tags
            for tag in root.findall('.//wp:tag', self.namespaces):
                tag_data = {
                    'slug': tag.find('wp:tag_slug', self.namespaces).text,
                    'name': tag.find('wp:tag_name', self.namespaces).text
                }
                self.tags.append(tag_data)
            
            # Parse posts and pages
            for item in root.findall('.//item'):
                post_type = item.find('wp:post_type', self.namespaces)
                if post_type is not None and post_type.text in ['post', 'page']:
                    post_data = self._parse_post(item)
                    if post_data:
                        self.posts.append(post_data)
            
            print(f"Parsed {len(self.posts)} posts, {len(self.categories)} categories, {len(self.tags)} tags")
            
        except Exception as e:
            print(f"Error parsing WXR file: {e}")
            sys.exit(1)
    
    def _parse_post(self, item):
        """Parse individual post/page from WXR"""
        title = item.find('title')
        content = item.find('content:encoded', self.namespaces)
        post_type = item.find('wp:post_type', self.namespaces)
        post_status = item.find('wp:status', self.namespaces)
        post_date = item.find('wp:post_date', self.namespaces)
        post_name = item.find('wp:post_name', self.namespaces)
        
        # Skip if status is not published or draft
        if post_status is not None and post_status.text not in ['publish', 'draft']:
            return None
        
        post_data = {
            'title': title.text if title is not None and title.text else 'Untitled',
            'content': content.text if content is not None and content.text else '',
            'slug': post_name.text if post_name is not None and post_name.text else '',
            'type': post_type.text if post_type is not None else 'post',
            'status': 'publish' if post_status is not None and post_status.text == 'publish' else 'draft',
            'date': post_date.text if post_date is not None and post_date.text else '',
            'categories': [],
            'tags': [],
            'comments': []
        }
        
        # Parse categories and tags
        for category in item.findall('category'):
            domain = category.get('domain')
            nicename = category.get('nicename')
            if domain == 'category':
                post_data['categories'].append(nicename)
            elif domain == 'post_tag':
                post_data['tags'].append(nicename)
        
        # Parse comments
        for comment in item.findall('wp:comment', self.namespaces):
            comment_data = self._parse_comment(comment)
            if comment_data:
                post_data['comments'].append(comment_data)
        
        return post_data
    
    def _parse_comment(self, comment):
        """Parse comment from WXR"""
        comment_approved = comment.find('wp:comment_approved', self.namespaces)
        if comment_approved is not None and comment_approved.text == 'spam':
            return None
        
        return {
            'author': self._get_text(comment.find('wp:comment_author', self.namespaces)),
            'email': self._get_text(comment.find('wp:comment_author_email', self.namespaces)),
            'url': self._get_text(comment.find('wp:comment_author_url', self.namespaces)),
            'ip': self._get_text(comment.find('wp:comment_author_IP', self.namespaces)),
            'date': self._get_text(comment.find('wp:comment_date', self.namespaces)),
            'content': self._get_text(comment.find('wp:comment_content', self.namespaces)),
            'approved': 'approved' if comment_approved is not None and comment_approved.text == '1' else 'waiting',
            'parent': self._get_text(comment.find('wp:comment_parent', self.namespaces), '0')
        }
    
    def _get_text(self, element, default=''):
        """Safely get text from XML element"""
        if element is not None and element.text:
            return element.text
        return default
    
    def generate_sql(self):
        """Generate Typecho SQL import statements"""
        print(f"Generating SQL file: {self.output_file}")
        
        sql_statements = []
        
        # Add SQL header
        sql_statements.append("-- Typecho Import SQL")
        sql_statements.append("-- Generated by WordPress to Typecho Migration Script")
        sql_statements.append(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sql_statements.append("")
        sql_statements.append("SET NAMES utf8mb4;")
        sql_statements.append("SET FOREIGN_KEY_CHECKS = 0;")
        sql_statements.append("")
        
        # Generate meta table data for categories and tags
        meta_id = 1
        meta_map = {}
        
        for category in self.categories:
            sql = self._generate_meta_insert(meta_id, category['name'], category['slug'], 'category')
            sql_statements.append(sql)
            meta_map[f"category:{category['slug']}"] = meta_id
            meta_id += 1
        
        for tag in self.tags:
            sql = self._generate_meta_insert(meta_id, tag['name'], tag['slug'], 'tag')
            sql_statements.append(sql)
            meta_map[f"tag:{tag['slug']}"] = meta_id
            meta_id += 1
        
        sql_statements.append("")
        
        # Generate contents table data for posts
        cid = 1
        comment_id = 1
        
        for post in self.posts:
            # Insert post
            sql = self._generate_content_insert(cid, post)
            sql_statements.append(sql)
            
            # Insert relationships
            for cat_slug in post['categories']:
                meta_id = meta_map.get(f"category:{cat_slug}")
                if meta_id:
                    sql = self._generate_relationship_insert(cid, meta_id)
                    sql_statements.append(sql)
            
            for tag_slug in post['tags']:
                meta_id = meta_map.get(f"tag:{tag_slug}")
                if meta_id:
                    sql = self._generate_relationship_insert(cid, meta_id)
                    sql_statements.append(sql)
            
            # Insert comments
            for comment in post['comments']:
                sql = self._generate_comment_insert(comment_id, cid, comment)
                sql_statements.append(sql)
                comment_id += 1
            
            cid += 1
        
        sql_statements.append("")
        sql_statements.append("SET FOREIGN_KEY_CHECKS = 1;")
        
        # Write to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_statements))
        
        print(f"SQL file generated successfully: {self.output_file}")
        print(f"Total posts: {len(self.posts)}")
        print(f"Total categories: {len(self.categories)}")
        print(f"Total tags: {len(self.tags)}")
    
    def _generate_meta_insert(self, mid, name, slug, type_name):
        """Generate INSERT statement for metas table"""
        name = self._escape_sql(name)
        slug = self._escape_sql(slug)
        description = ''
        count = 0
        order = 0
        parent = 0
        
        return (f"INSERT INTO `{self.table_prefix}metas` "
                f"(`mid`, `name`, `slug`, `type`, `description`, `count`, `order`, `parent`) "
                f"VALUES ({mid}, '{name}', '{slug}', '{type_name}', '{description}', {count}, {order}, {parent});")
    
    def _generate_content_insert(self, cid, post):
        """Generate INSERT statement for contents table"""
        title = self._escape_sql(post['title'])
        slug = self._escape_sql(post['slug'])
        created = self._convert_date(post['date'])
        modified = created
        text = self._escape_sql(post['content'])
        order = 0
        author_uid = 1
        template = ''
        type_name = 'post' if post['type'] == 'post' else 'page'
        status = 'publish' if post['status'] == 'publish' else 'draft'
        password = ''
        comments_num = len(post['comments'])
        allow_comment = 1
        allow_ping = 1
        allow_feed = 1
        parent = 0
        
        return (f"INSERT INTO `{self.table_prefix}contents` "
                f"(`cid`, `title`, `slug`, `created`, `modified`, `text`, `order`, `authorId`, "
                f"`template`, `type`, `status`, `password`, `commentsNum`, `allowComment`, "
                f"`allowPing`, `allowFeed`, `parent`) "
                f"VALUES ({cid}, '{title}', '{slug}', {created}, {modified}, '{text}', {order}, "
                f"{author_uid}, '{template}', '{type_name}', '{status}', '{password}', "
                f"{comments_num}, {allow_comment}, {allow_ping}, {allow_feed}, {parent});")
    
    def _generate_relationship_insert(self, cid, mid):
        """Generate INSERT statement for relationships table"""
        return (f"INSERT INTO `{self.table_prefix}relationships` (`cid`, `mid`) "
                f"VALUES ({cid}, {mid});")
    
    def _generate_comment_insert(self, coid, cid, comment):
        """Generate INSERT statement for comments table"""
        author = self._escape_sql(comment['author'])
        email = self._escape_sql(comment['email'])
        url = self._escape_sql(comment['url'])
        ip = self._escape_sql(comment['ip'])
        created = self._convert_date(comment['date'])
        text = self._escape_sql(comment['content'])
        approved = comment['approved']
        parent_coid = comment['parent']
        
        return (f"INSERT INTO `{self.table_prefix}comments` "
                f"(`coid`, `cid`, `created`, `author`, `authorId`, `ownerId`, `mail`, `url`, "
                f"`ip`, `agent`, `text`, `type`, `status`, `parent`) "
                f"VALUES ({coid}, {cid}, {created}, '{author}', 0, 1, '{email}', '{url}', "
                f"'{ip}', '', '{text}', 'comment', '{approved}', {parent_coid});")
    
    def _escape_sql(self, text):
        """Escape text for SQL"""
        if not text:
            return ''
        text = str(text)
        text = text.replace("\\", "\\\\")
        text = text.replace("'", "\\'")
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        return text
    
    def _convert_date(self, date_str):
        """Convert WordPress date to Unix timestamp"""
        if not date_str:
            return int(datetime.now().timestamp())
        
        try:
            # WordPress format: 2024-01-01 12:00:00
            dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            return int(dt.timestamp())
        except:
            return int(datetime.now().timestamp())
    
    def convert(self):
        """Main conversion process"""
        print("=" * 50)
        print("WordPress to Typecho Migration Script")
        print("=" * 50)
        self.parse_wxr()
        self.generate_sql()
        print("=" * 50)
        print("Conversion completed successfully!")
        print(f"Import SQL file: {self.output_file}")
        print("=" * 50)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Convert WordPress WXR export to Typecho SQL import'
    )
    parser.add_argument(
        'wxr_file',
        help='WordPress WXR export file path'
    )
    parser.add_argument(
        '-o', '--output',
        default='typecho_import.sql',
        help='Output SQL file path (default: typecho_import.sql)'
    )
    parser.add_argument(
        '-p', '--prefix',
        default='typecho_',
        help='Typecho database table prefix (default: typecho_)'
    )
    
    args = parser.parse_args()
    
    converter = WP2Typecho(args.wxr_file, args.output, args.prefix)
    converter.convert()


if __name__ == '__main__':
    main()

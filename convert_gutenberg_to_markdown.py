#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将WordPress古腾堡编辑器内容转换为Markdown格式
"""

import pymysql
import re
import json
import os
import time
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime
from html import unescape

TYPECHO_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'your_username',
    'password': 'your_password',
    'database': 'typecho_db',
    'charset': 'utf8mb4'
}

class GutenbergToMarkdown:
    def __init__(self):
        self.conn = None
        self.converted_count = 0
        self.skipped_count = 0
        self.downloaded_images = {}  # 缓存已下载的图片 {原始URL: 新URL}
        self.typecho_root = '/var/www/typecho'  # Typecho根目录
        
    def connect_db(self):
        """连接数据库"""
        self.conn = pymysql.connect(**TYPECHO_CONFIG)
        print("✓ 数据库连接成功\n")
    
    def close_db(self):
        """关闭数据库"""
        if self.conn:
            self.conn.close()
    
    def extract_language_from_comment(self, comment):
        """从WordPress注释中提取代码语言"""
        # 匹配 "language":"bash" 或 "className":"language-bash"
        lang_match = re.search(r'"language"\s*:\s*"([^"]+)"', comment)
        if lang_match:
            return lang_match.group(1)
        
        # 匹配 className 中的语言
        class_match = re.search(r'"className"\s*:\s*"[^"]*language-([^"\s]+)', comment)
        if class_match:
            return class_match.group(1)
        
        return ''
    
    def extract_language_from_code(self, code_content):
        """从代码内容第一行提取语言标记"""
        # 匹配第一行的语言标记，如：// language: php, # language: python 等
        first_line_match = re.match(r'^(?://|#|--|\*)\s*language:\s*(\w+)', code_content.strip(), re.IGNORECASE)
        if first_line_match:
            language = first_line_match.group(1).lower()
            # 移除第一行语言标记
            code_content = re.sub(r'^(?://|#|--|\*)\s*language:\s*\w+\s*\n?', '', code_content.strip(), count=1, flags=re.IGNORECASE)
            return language, code_content.strip()
        
        return '', code_content
    
    def convert_code_block(self, content):
        """转换代码块"""
        # 匹配 <!-- wp:code --> ... <!-- /wp:code -->
        pattern = r'<!--\s*wp:code\s*({[^}]*})?\s*-->\s*<pre[^>]*><code[^>]*>(.*?)</code></pre>\s*<!--\s*/wp:code\s*-->'
        
        def replace_code(match):
            metadata = match.group(1) or '{}'
            code_content = match.group(2)
            
            # 提取语言
            language = ''
            try:
                if metadata:
                    meta_dict = json.loads(metadata)
                    language = meta_dict.get('language', '')
                    if not language and 'className' in meta_dict:
                        # 从className提取
                        class_name = meta_dict['className']
                        lang_match = re.search(r'language-(\w+)', class_name)
                        if lang_match:
                            language = lang_match.group(1)
            except:
                # 如果JSON解析失败，尝试正则提取
                language = self.extract_language_from_comment(metadata)
            
            # 解码HTML实体
            code_content = unescape(code_content)
            
            # 如果没有从元数据中获取到语言，尝试从代码内容第一行提取
            if not language:
                extracted_lang, cleaned_code = self.extract_language_from_code(code_content)
                if extracted_lang:
                    language = extracted_lang
                    code_content = cleaned_code
            else:
                # 即使有元数据语言，也检查代码中是否有语言标记，如果有则移除
                _, cleaned_code = self.extract_language_from_code(code_content)
                # 如果代码被清理了（移除了语言标记），使用清理后的代码
                if cleaned_code != code_content:
                    code_content = cleaned_code
            
            # 构建markdown代码块
            return f'```{language}\n{code_content}\n```'
        
        content = re.sub(pattern, replace_code, content, flags=re.DOTALL)
        return content
    
    def convert_paragraph(self, content):
        """转换段落"""
        # 移除 <!-- wp:paragraph --> 注释
        content = re.sub(r'<!--\s*wp:paragraph\s*-->\s*', '', content)
        content = re.sub(r'\s*<!--\s*/wp:paragraph\s*-->', '', content)
        return content
    
    def convert_heading(self, content):
        """转换标题"""
        # 1. 转换带有 wp:heading 注释的标题
        # <!-- wp:heading {"level":2} --> <h2>...</h2> <!-- /wp:heading -->
        pattern = r'<!--\s*wp:heading\s*({[^}]*})?\s*-->\s*<h(\d)[^>]*>(.*?)</h\2>\s*<!--\s*/wp:heading\s*-->'
        
        def replace_heading(match):
            level = int(match.group(2))
            title = match.group(3)
            title = re.sub(r'<[^>]+>', '', title)  # 移除HTML标签
            return '#' * level + ' ' + title + '\n'
        
        content = re.sub(pattern, replace_heading, content, flags=re.DOTALL)
        
        # 2. 转换没有注释包裹但带有 wp-block-heading 类的标题
        # <h3 class="wp-block-heading">...</h3>
        pattern2 = r'<h(\d)[^>]*class="[^"]*wp-block-heading[^"]*"[^>]*>(.*?)</h\1>'
        
        def replace_standalone_heading(match):
            level = int(match.group(1))
            title = match.group(2)
            title = re.sub(r'<[^>]+>', '', title)  # 移除HTML标签
            return '\n' + '#' * level + ' ' + title + '\n'
        
        content = re.sub(pattern2, replace_standalone_heading, content, flags=re.DOTALL)
        
        return content
    
    def convert_list(self, content):
        """转换列表"""
        # 有序列表
        # <!-- wp:list {"ordered":true} --> <ol>...</ol> <!-- /wp:list -->
        pattern = r'<!--\s*wp:list\s*({[^}]*})?\s*-->\s*<ol[^>]*>(.*?)</ol>\s*<!--\s*/wp:list\s*-->'
        
        def replace_ordered_list(match):
            list_content = match.group(2)
            # 提取li项
            items = re.findall(r'<li[^>]*>(.*?)</li>', list_content, re.DOTALL)
            result = []
            for i, item in enumerate(items, 1):
                item = re.sub(r'<[^>]+>', '', item).strip()
                result.append(f'{i}. {item}')
            return '\n'.join(result) + '\n'
        
        content = re.sub(pattern, replace_ordered_list, content, flags=re.DOTALL)
        
        # 无序列表
        pattern = r'<!--\s*wp:list\s*-->\s*<ul[^>]*>(.*?)</ul>\s*<!--\s*/wp:list\s*-->'
        
        def replace_unordered_list(match):
            list_content = match.group(1)
            items = re.findall(r'<li[^>]*>(.*?)</li>', list_content, re.DOTALL)
            result = []
            for item in items:
                item = re.sub(r'<[^>]+>', '', item).strip()
                result.append(f'- {item}')
            return '\n'.join(result) + '\n'
        
        content = re.sub(pattern, replace_unordered_list, content, flags=re.DOTALL)
        return content
    
    def convert_quote(self, content):
        """转换引用块"""
        # <!-- wp:quote --> <blockquote>...</blockquote> <!-- /wp:quote -->
        pattern = r'<!--\s*wp:quote\s*-->\s*<blockquote[^>]*>(.*?)</blockquote>\s*<!--\s*/wp:quote\s*-->'
        
        def replace_quote(match):
            quote_content = match.group(1)
            # 移除p标签
            quote_content = re.sub(r'</?p[^>]*>', '', quote_content)
            quote_content = re.sub(r'<[^>]+>', '', quote_content).strip()
            lines = quote_content.split('\n')
            return '\n'.join(f'> {line}' for line in lines if line.strip()) + '\n'
        
        content = re.sub(pattern, replace_quote, content, flags=re.DOTALL)
        return content
    
    def convert_image(self, content):
        """转换图片"""
        # <!-- wp:image --> <figure><img src="..." alt="..." /></figure> <!-- /wp:image -->
        pattern = r'<!--\s*wp:image[^>]*-->\s*<figure[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"[^>]*>.*?</figure>\s*<!--\s*/wp:image\s*-->'
        
        def replace_image(match):
            src = match.group(1)
            alt = match.group(2) or ''
            return f'![{alt}]({src})\n'
        
        content = re.sub(pattern, replace_image, content, flags=re.DOTALL)
        return content
    
    def convert_separator(self, content):
        """转换分隔线"""
        # <!-- wp:separator --> <hr /> <!-- /wp:separator -->
        # 或者 <hr class="wp-block-separator" />
        # 匹配多种分隔线格式
        patterns = [
            r'<!--\s*wp:separator[^>]*-->\s*<hr[^>]*/?>\s*<!--\s*/wp:separator\s*-->',
            r'<hr\s+class="wp-block-separator[^"]*"[^>]*/>',
            r'<hr\s+class="wp-block-separator[^"]*"[^>]*>',
        ]
        
        for pattern in patterns:
            content = re.sub(pattern, '\n---\n', content, flags=re.DOTALL)
        
        return content
    
    def download_image(self, image_url):
        """下载图片并保存到本地"""
        # 如果已经下载过，直接返回本地URL
        if image_url in self.downloaded_images:
            return self.downloaded_images[image_url]
        
        try:
            # 解析URL
            parsed_url = urllib.parse.urlparse(image_url)
            url_path = parsed_url.path
            
            # 从URL中提取年月，例如：/wp-content/uploads/2025/02/image.jpg
            # 匹配模式：uploads/YYYY/MM/
            year_month_match = re.search(r'/uploads/(\d{4})/(\d{2})/', url_path)
            
            if year_month_match:
                # 使用原路径中的年月
                year = year_month_match.group(1)
                month = year_month_match.group(2)
                year_month = f"{year}/{month}"
            else:
                # 如果没有找到年月，使用当前日期
                now = datetime.now()
                year_month = now.strftime('%Y/%m')
            
            upload_dir = os.path.join(self.typecho_root, 'usr/uploads', year_month)
            
            # 创建目录
            os.makedirs(upload_dir, exist_ok=True)
            
            # 获取原文件名
            file_name = os.path.basename(url_path)
            name_without_ext, ext = os.path.splitext(file_name)
            
            # 检查文件是否已存在，如果存在则添加数字后缀
            local_path = os.path.join(upload_dir, file_name)
            counter = 1
            while os.path.exists(local_path):
                new_name = f"{name_without_ext}_{counter}{ext}"
                local_path = os.path.join(upload_dir, new_name)
                file_name = new_name
                counter += 1
            
            # 下载图片
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(image_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                image_data = response.read()
            
            # 保存图片
            with open(local_path, 'wb') as f:
                f.write(image_data)
            
            # 获取文件信息
            file_size = len(image_data)
            
            # 确定MIME类型
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg', 
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.svg': 'image/svg+xml',
            }
            mime_type = mime_types.get(ext.lower(), 'image/jpeg')
            
            # 相对路径（用于数据库）
            relative_path = f"/usr/uploads/{year_month}/{file_name}"
            
            # 返回本地URL（用于文章内容）
            local_url = f"/usr/uploads/{year_month}/{file_name}"
            
            # 缓存
            self.downloaded_images[image_url] = {
                'url': local_url,
                'path': relative_path,
                'name': file_name,
                'size': file_size,
                'type': ext.lstrip('.'),
                'mime': mime_type
            }
            
            print(f"    ✓ 下载图片: {file_name} -> {year_month}/{file_name}")
            return self.downloaded_images[image_url]
            
        except Exception as e:
            print(f"    ✗ 下载失败 ({image_url}): {e}")
            return None
    
    def create_attachment_record(self, image_info, parent_cid):
        """在数据库中创建附件记录"""
        try:
            cursor = self.conn.cursor()
            
            # 检查附件是否已存在
            cursor.execute(
                "SELECT cid FROM typecho_contents WHERE type = 'attachment' AND text LIKE %s",
                (f'%{image_info["name"]}%',)
            )
            
            if cursor.fetchone():
                return  # 附件已存在
            
            # 准备附件元数据
            attachment_data = {
                "name": image_info['name'],
                "path": image_info['path'],
                "size": image_info['size'],
                "type": image_info['type'],
                "mime": image_info['mime']
            }
            
            # 生成slug
            slug = re.sub(r'[^\w\-]', '-', image_info['name'])
            slug = re.sub(r'-+', '-', slug).strip('-').lower()
            
            # 插入附件记录
            now = int(time.time())
            insert_sql = """
                INSERT INTO typecho_contents 
                (title, slug, created, modified, text, `order`, authorId, template,
                type, status, password, commentsNum, allowComment, allowPing, allowFeed, parent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_sql, (
                image_info['name'],
                slug,
                now,
                now,
                json.dumps(attachment_data, ensure_ascii=False),
                0,
                1,  # 默认管理员ID
                None,
                'attachment',
                'publish',
                None,
                0,
                '1',
                '0',
                '1',
                parent_cid
            ))
            
            print(f"    ✓ 创建附件记录: {image_info['name']}")
            
        except Exception as e:
            print(f"    ✗ 创建附件记录失败: {e}")
    
    def process_images_in_content(self, content, cid):
        """处理内容中的所有图片"""
        # 查找所有图片URL（支持多种格式）
        patterns = [
            r'!\[([^\]]*)\]\(([^)]+)\)',  # Markdown格式: ![alt](url)
            r'<img[^>]+src="([^"]+)"[^>]*>',  # HTML格式: <img src="url">
        ]
        
        modified = False
        
        for pattern in patterns:
            if pattern.startswith('!'):
                # Markdown格式
                def replace_md_image(match):
                    nonlocal modified
                    alt = match.group(1)
                    url = match.group(2)
                    
                    # 只处理远程图片
                    if url.startswith('http://') or url.startswith('https://'):
                        # 只下载指定域名的图片（WordPress图片）
                        if 'wp-content/uploads' in url or 'jsdd.net' in url:
                            image_info = self.download_image(url)
                            if image_info:
                                self.create_attachment_record(image_info, cid)
                                modified = True
                                return f"![{alt}]({image_info['url']})"
                    
                    return match.group(0)
                
                content = re.sub(pattern, replace_md_image, content)
            else:
                # HTML格式
                def replace_html_image(match):
                    nonlocal modified
                    url = match.group(1)
                    
                    if url.startswith('http://') or url.startswith('https://'):
                        if 'wp-content/uploads' in url or 'jsdd.net' in url:
                            image_info = self.download_image(url)
                            if image_info:
                                self.create_attachment_record(image_info, cid)
                                modified = True
                                return match.group(0).replace(url, image_info['url'])
                    
                    return match.group(0)
                
                content = re.sub(pattern, replace_html_image, content)
        
        return content, modified
    
    def clean_html_tags(self, content):
        """清理剩余的HTML标签"""
        # 保留一些基本的HTML标签转换
        content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', content)
        content = re.sub(r'<b>(.*?)</b>', r'**\1**', content)
        content = re.sub(r'<em>(.*?)</em>', r'*\1*', content)
        content = re.sub(r'<i>(.*?)</i>', r'*\1*', content)
        content = re.sub(r'<code>(.*?)</code>', r'`\1`', content)
        
        # 转换mark标签（高亮标记）- 转为粗体
        content = re.sub(r'<mark[^>]*>(.*?)</mark>', r'**\1**', content, flags=re.DOTALL)
        
        # 转换链接
        content = re.sub(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', content)
        
        # 移除段落标签但保留内容
        content = re.sub(r'<p[^>]*>', '\n', content)
        content = re.sub(r'</p>', '\n', content)
        
        # 移除其他古腾堡注释
        content = re.sub(r'<!--\s*/?wp:[^>]*-->', '', content)
        
        return content
    
    def convert_to_markdown(self, content):
        """将古腾堡内容转换为Markdown"""
        if not content:
            return content
        
        # 如果已经是Markdown格式（已转换过），跳过
        if content.startswith('<!--markdown-->'):
            return content
        
        # 检查是否包含古腾堡块（注释或类名）
        has_gutenberg_comment = '<!-- wp:' in content
        has_gutenberg_class = 'wp-block-' in content
        
        if not has_gutenberg_comment and not has_gutenberg_class:
            return content
        
        original_content = content
        
        try:
            # 按顺序转换各种块
            content = self.convert_code_block(content)
            content = self.convert_heading(content)
            content = self.convert_list(content)
            content = self.convert_quote(content)
            content = self.convert_image(content)
            content = self.convert_separator(content)
            content = self.convert_paragraph(content)
            content = self.clean_html_tags(content)
            
            # 清理多余的空行
            content = re.sub(r'\n{3,}', '\n\n', content)
            content = content.strip()
            
            # 如果内容已经有 <!--markdown--> 标记，就不再添加
            if not content.startswith('<!--markdown-->'):
                content = '<!--markdown-->' + content
            
            return content
        except Exception as e:
            print(f"  转换出错: {e}")
            return original_content
    
    def process_all_posts(self, dry_run=False):
        """处理所有文章"""
        cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取所有包含古腾堡块的文章（注释或类名）
        cursor.execute("""
            SELECT cid, title, text 
            FROM typecho_contents 
            WHERE type = 'post' AND (text LIKE '%<!-- wp:%' OR text LIKE '%wp-block-%')
            ORDER BY cid
        """)
        
        posts = cursor.fetchall()
        total = len(posts)
        
        print(f"找到 {total} 篇包含古腾堡块的文章\n")
        
        if total == 0:
            return
        
        if dry_run:
            print("=== 预览模式（不会修改数据库）===\n")
        
        for i, post in enumerate(posts, 1):
            print(f"[{i}/{total}] 处理: {post['title'][:50]}")
            
            original_content = post['text']
            converted_content = self.convert_to_markdown(original_content)
            
            if original_content != converted_content:
                if dry_run:
                    print(f"  预览转换")
                    print(f"  原始长度: {len(original_content)} 字符")
                    print(f"  转换后长度: {len(converted_content)} 字符")
                else:
                    # 处理图片：下载并创建附件
                    final_content, images_modified = self.process_images_in_content(
                        converted_content, 
                        post['cid']
                    )
                    
                    # 更新数据库
                    update_cursor = self.conn.cursor()
                    update_cursor.execute(
                        "UPDATE typecho_contents SET text = %s WHERE cid = %s",
                        (final_content, post['cid'])
                    )
                    print(f"  ✓ 已转换并保存")
                    self.converted_count += 1
                    
                    # 每10篇提交一次
                    if self.converted_count % 10 == 0:
                        self.conn.commit()
                        print(f"  [已提交 {self.converted_count} 篇]")
            else:
                print(f"  - 无需转换")
                self.skipped_count += 1
        
        if not dry_run:
            self.conn.commit()
        
        print(f"\n{'=' * 60}")
        print(f"处理完成！")
        print(f"转换: {self.converted_count} 篇")
        print(f"跳过: {self.skipped_count} 篇")
        print(f"{'=' * 60}\n")
    
    def preview_single_post(self, cid):
        """预览单篇文章的转换结果"""
        cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT cid, title, text FROM typecho_contents WHERE cid = %s", (cid,))
        post = cursor.fetchone()
        
        if not post:
            print(f"未找到文章 ID: {cid}")
            return
        
        print(f"{'=' * 80}")
        print(f"文章: {post['title']}")
        print(f"{'=' * 80}\n")
        
        original = post['text']
        converted = self.convert_to_markdown(original)
        
        print("【原始内容】")
        print("-" * 80)
        print(original[:500] + ('...' if len(original) > 500 else ''))
        print()
        
        print("【转换后内容】")
        print("-" * 80)
        print(converted[:500] + ('...' if len(converted) > 500 else ''))
        print()
        
        print(f"原始长度: {len(original)} 字符")
        print(f"转换后长度: {len(converted)} 字符")
    
    def run(self, mode='convert', cid=None):
        """运行转换"""
        try:
            self.connect_db()
            
            if mode == 'preview' and cid:
                # 预览单篇文章
                self.preview_single_post(cid)
            elif mode == 'dry-run':
                # 预览所有文章
                self.process_all_posts(dry_run=True)
            else:
                # 执行转换
                self.process_all_posts(dry_run=False)
        
        except Exception as e:
            print(f"\n错误: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.close_db()

if __name__ == "__main__":
    import sys
    
    converter = GutenbergToMarkdown()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'preview' and len(sys.argv) > 2:
            # python3 convert_gutenberg_to_markdown.py preview 123
            converter.run(mode='preview', cid=int(sys.argv[2]))
        elif sys.argv[1] == 'dry-run':
            # python3 convert_gutenberg_to_markdown.py dry-run
            converter.run(mode='dry-run')
        else:
            print("用法:")
            print("  python3 convert_gutenberg_to_markdown.py              # 执行转换")
            print("  python3 convert_gutenberg_to_markdown.py dry-run      # 预览所有文章")
            print("  python3 convert_gutenberg_to_markdown.py preview 123  # 预览单篇文章")
    else:
        # 直接执行转换
        converter.run(mode='convert')

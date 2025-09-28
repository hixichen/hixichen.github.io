#!/usr/bin/env python3
"""
Hexo to Hugo Blog Post Converter

This script converts Hexo-generated blog posts to Hugo markdown format.
It extracts metadata (title, date, tags) and content from HTML files,
converts HTML to markdown, and generates Hugo-compatible markdown files.
"""

import os
import re
import glob
from datetime import datetime
from pathlib import Path
import html
import argparse

try:
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md
except ImportError:
    print("Required packages not found. Please install them:")
    print("pip install beautifulsoup4 markdownify lxml")
    exit(1)


class HexoToHugoConverter:
    def __init__(self, input_dir='.', output_dir='hugo_posts'):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.posts_processed = 0
        self.posts_failed = 0

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)

    def find_blog_posts(self):
        """Find all blog post HTML files matching the pattern YYYY/MM/DD/*/index.html"""
        pattern = str(self.input_dir / "[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]/*/index.html")
        files = glob.glob(pattern)

        # All files matching this pattern should be blog posts
        return sorted(files)

    def extract_date_from_path(self, file_path):
        """Extract date from file path"""
        date_pattern = re.compile(r'.*/(\d{4})/(\d{2})/(\d{2})/')
        match = date_pattern.search(file_path)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"
        return None

    def extract_slug_from_path(self, file_path):
        """Extract slug from file path"""
        path_pattern = re.compile(r'.*\d{4}/\d{2}/\d{2}/([^/]+)/index\.html$')
        match = path_pattern.search(file_path)
        if match:
            return match.group(1)
        return "untitled"

    def parse_html_file(self, file_path):
        """Parse HTML file and extract metadata and content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None

        soup = BeautifulSoup(content, 'html.parser')

        # Extract title
        title_elem = soup.find('h1', class_='post-title')
        title = title_elem.get_text().strip() if title_elem else "Untitled"

        # Extract date from meta or fallback to path
        date_from_path = self.extract_date_from_path(file_path)

        # Try to extract date from post-meta div
        meta_elem = soup.find('div', class_='post-meta')
        date = date_from_path  # Default fallback

        if meta_elem:
            meta_text = meta_elem.get_text().strip()
            # Try to parse date from meta text (e.g., "Sep 1, 2018")
            date_patterns = [
                r'(\w{3} \d{1,2}, \d{4})',  # Sep 1, 2018
                r'(\d{4}-\d{2}-\d{2})',    # 2018-09-01
            ]

            for pattern in date_patterns:
                match = re.search(pattern, meta_text)
                if match:
                    try:
                        parsed_date = datetime.strptime(match.group(1), '%b %d, %Y')
                        date = parsed_date.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue

        # Extract content
        content_elem = soup.find('div', class_='post-content')
        if not content_elem:
            print(f"Warning: No post content found in {file_path}")
            return None

        # Convert HTML content to markdown
        html_content = str(content_elem)
        markdown_content = self.html_to_markdown(html_content)

        # Extract tags
        tags = []
        tags_elem = soup.find('div', class_='tags')
        if tags_elem:
            tag_links = tags_elem.find_all('a')
            for tag_link in tag_links:
                tag_text = tag_link.get_text().strip()
                if tag_text:
                    tags.append(tag_text)

        # Extract slug from path
        slug = self.extract_slug_from_path(file_path)

        return {
            'title': title,
            'date': date,
            'tags': tags,
            'content': markdown_content,
            'slug': slug,
            'original_path': file_path
        }

    def html_to_markdown(self, html_content):
        """Convert HTML content to markdown"""
        # Clean up the HTML first
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove unwanted elements
        for elem in soup.find_all(['script', 'style']):
            elem.decompose()

        # Convert highlight code blocks to proper markdown
        for figure in soup.find_all('figure', class_='highlight'):
            lang = ''
            # Try to extract language from class
            if figure.get('class'):
                for cls in figure.get('class'):
                    if cls.startswith('highlight'):
                        continue
                    lang = cls
                    break

            # Extract code content - preserve line breaks from the table structure
            code_elem = figure.find('td', class_='code')
            if code_elem:
                # Get all the span elements which contain the code lines
                lines = []
                for line_elem in code_elem.find_all('span', class_='line'):
                    line_text = line_elem.get_text()
                    lines.append(line_text)

                # If no spans found, fall back to getting all text
                if not lines:
                    code_text = code_elem.get_text()
                    # Try to preserve line breaks by splitting on <br> tags
                    lines = code_text.split('\n')

                code_text = '\n'.join(lines)
                # Create markdown code block
                markdown_code = f"\n```{lang}\n{code_text}\n```\n"
                figure.replace_with(BeautifulSoup(markdown_code, 'html.parser'))

        # Convert to markdown
        markdown = md(str(soup), heading_style="ATX")

        # Clean up the markdown
        markdown = self.clean_markdown(markdown)

        return markdown

    def clean_markdown(self, markdown):
        """Clean up converted markdown"""
        # Remove extra whitespace
        markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)

        # Fix code block formatting
        markdown = re.sub(r'```(\w+)\s*\n\s*\n', r'```\1\n', markdown)

        # Remove leading/trailing whitespace
        markdown = markdown.strip()

        # Ensure there's a newline at the end
        if not markdown.endswith('\n'):
            markdown += '\n'

        return markdown

    def generate_hugo_frontmatter(self, post_data):
        """Generate Hugo frontmatter"""
        frontmatter = []
        frontmatter.append("---")
        frontmatter.append(f'title: "{post_data["title"]}"')
        frontmatter.append(f'date: {post_data["date"]}')
        frontmatter.append('draft: false')

        if post_data['tags']:
            tags_str = ', '.join(f'"{tag}"' for tag in post_data['tags'])
            frontmatter.append(f'tags: [{tags_str}]')
        else:
            frontmatter.append('tags: []')

        frontmatter.append("---")
        frontmatter.append("")

        return '\n'.join(frontmatter)

    def generate_output_filename(self, post_data):
        """Generate output filename for Hugo post"""
        date = post_data['date']
        slug = post_data['slug']

        # Sanitize slug
        slug = re.sub(r'[^\w\-_]', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')

        return f"{date}-{slug}.md"

    def convert_post(self, file_path):
        """Convert a single blog post"""
        print(f"Processing: {file_path}")

        post_data = self.parse_html_file(file_path)
        if not post_data:
            print(f"Failed to parse: {file_path}")
            self.posts_failed += 1
            return False

        # Generate frontmatter
        frontmatter = self.generate_hugo_frontmatter(post_data)

        # Combine frontmatter and content
        full_content = frontmatter + "\n" + post_data['content']

        # Generate output filename
        output_filename = self.generate_output_filename(post_data)
        output_path = self.output_dir / output_filename

        # Write the file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_content)

            print(f"  → Created: {output_path}")
            self.posts_processed += 1
            return True

        except Exception as e:
            print(f"  ✗ Error writing {output_path}: {e}")
            self.posts_failed += 1
            return False

    def convert_all_posts(self):
        """Convert all blog posts"""
        blog_posts = self.find_blog_posts()

        if not blog_posts:
            print("No blog posts found matching the pattern YYYY/MM/DD/*/index.html")
            return

        print(f"Found {len(blog_posts)} blog posts to convert:")
        print()

        for file_path in blog_posts:
            self.convert_post(file_path)
            print()

        print("=" * 60)
        print(f"Conversion complete!")
        print(f"  Posts processed: {self.posts_processed}")
        print(f"  Posts failed: {self.posts_failed}")
        print(f"  Output directory: {self.output_dir}")

        if self.posts_processed > 0:
            print(f"\nHugo markdown files have been created in: {self.output_dir}")
            print("You can now copy these files to your Hugo content/posts/ directory.")


def main():
    parser = argparse.ArgumentParser(description='Convert Hexo blog posts to Hugo markdown format')
    parser.add_argument('--input', '-i', default='.',
                       help='Input directory containing Hexo blog (default: current directory)')
    parser.add_argument('--output', '-o', default='hugo_posts',
                       help='Output directory for Hugo markdown files (default: hugo_posts)')
    parser.add_argument('--single', '-s',
                       help='Convert a single HTML file instead of scanning for all posts')

    args = parser.parse_args()

    converter = HexoToHugoConverter(args.input, args.output)

    if args.single:
        if os.path.exists(args.single):
            converter.convert_post(args.single)
        else:
            print(f"File not found: {args.single}")
    else:
        converter.convert_all_posts()


if __name__ == "__main__":
    main()
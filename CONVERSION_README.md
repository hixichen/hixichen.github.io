# Hexo to Hugo Blog Conversion

This directory contains a Python script that converts Hexo-generated blog posts to Hugo markdown format.

## Files

- `hexo_to_hugo_converter.py` - Main conversion script
- `requirements.txt` - Python dependencies
- `hugo_posts/` - Directory containing converted Hugo markdown files

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Convert all blog posts:
```bash
python3 hexo_to_hugo_converter.py
```

### Convert a single blog post:
```bash
python3 hexo_to_hugo_converter.py --single "2018/09/01/Get-k8s-events-with-minikube/index.html"
```

### Custom input/output directories:
```bash
python3 hexo_to_hugo_converter.py --input /path/to/hexo/blog --output /path/to/hugo/posts
```

## Conversion Results

The script successfully converted **29 blog posts** from your Hexo blog. Each converted file includes:

- Hugo frontmatter with title, date, and tags
- Clean markdown content with proper formatting
- Preserved code blocks with syntax highlighting
- Converted HTML links and formatting

## Next Steps

1. Copy the files from `hugo_posts/` to your Hugo site's `content/posts/` directory
2. Review and adjust any formatting if needed
3. Update your Hugo configuration as necessary

## Features

- Extracts metadata (title, date, tags) from HTML files
- Converts HTML content to clean markdown
- Handles code blocks with proper formatting
- Preserves links and basic formatting
- Generates Hugo-compatible frontmatter
- Processes all posts matching the pattern `YYYY/MM/DD/*/index.html`

## File Naming Convention

Output files follow the pattern: `YYYY-MM-DD-post-slug.md`

For example:
- `2018/09/01/Get-k8s-events-with-minikube/index.html` → `2018-09-01-Get-k8s-events-with-minikube.md`
- `2017/09/06/Golang_reading/index.html` → `2017-09-06-Golang_reading.md`
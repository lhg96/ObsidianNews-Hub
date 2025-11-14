#!/usr/bin/env python3
"""
Setup script for AI-RSSCrawler
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="ai-rss-crawler",
    version="1.0.0",
    author="lhg96",
    author_email="",
    description="AI-powered RSS crawler with markdown generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lhg96/-AI-RSSCrawler",
    project_urls={
        "Bug Tracker": "https://github.com/lhg96/-AI-RSSCrawler/issues",
        "Documentation": "https://github.com/lhg96/-AI-RSSCrawler/blob/main/README.md",
    },
    packages=find_packages(include=['src', 'src.*']),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: News/Diary",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: Markdown",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "pylint>=2.17.0",
            "mypy>=1.3.0",
            "isort>=5.12.0",
        ],
        "monitoring": [
            "prometheus-client>=0.16.0",
            "grafana-api>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "rss-crawl=scripts.crawl_news:main",
            "rss-generate=scripts.generate_markdown:main", 
            "rss-query=scripts.query_database:main",
            "rss-web-gui=scripts.simple_web_gui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.yaml", "config/*.csv", "config/.env.example"],
    },
    zip_safe=False,
    keywords="rss crawler news markdown obsidian chromadb",
    platforms=["any"],
)
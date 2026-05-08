"""
墨麟OS (Molin OS) — Python包安装配置
6层架构 · 290技能 · 25家Worker · 22营收子公司 · 5VP管理层
每月营收目标 ¥52,000 · 零空转 · 完整可部署
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="molin-os",
    version="5.0.0",
    author="moye-tech",
    author_email="fengye940708@gmail.com",
    description="墨麟OS — AI一人公司操作系统 (6层·492技能·22Worker·¥52K/月)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/moye-tech/Molin-OS",
    packages=find_packages(include=["molib", "molib.*", "molin", "molin.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "molin=molib.cli:main",
            "moyu=molib.cli:main",
        ],
    },
)

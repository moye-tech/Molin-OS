"""
墨麟OS (Molin OS) — Python包安装配置
AI操作系统 · 20家子公司 · 362技能 · 5VP管理层
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="molin-os",
    version="5.0.0",
    author="Moye Tech",
    author_email="fengye940708@gmail.com",
    description="墨麟OS — AI一人公司操作系统 (362技能·20子公司·¥52K/月)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/moye-tech/Molin-OS",
    packages=find_packages(
        include=["molib", "molib.*", "sop", "sop.*", "strategy", "strategy.*"]
    ),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "requests>=2.31.0",
        "toml>=0.10.2",
    ],
    extras_require={
        "full": [
            "openai>=1.30.0",
            "anthropic>=0.28.0",
            "dashscope>=1.20.0",
            "qdrant-client>=1.9.0",
            "httpx>=0.27.0",
            "pandas>=2.2.0",
            "Pillow>=10.3.0",
            "SQLAlchemy>=2.0.30",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=24.0.0",
            "ruff>=0.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "molin=molib.cli:main",
            "moyu=molib.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

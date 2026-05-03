"""
墨麟 Hermes OS — Python包安装配置
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="molin-hermes-os",
    version="2.0.0",
    author="moye-tech",
    author_email="fengye940708@gmail.com",
    description="墨麟 Hermes OS — AI一人公司操作系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/moye-tech/-Hermes-OS",
    packages=find_packages(),
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
            "molin=molin.cli:main",
        ],
    },
)

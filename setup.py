"""
厨房安全检测系统安装配置
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="kitchen-safety-system",
    version="1.0.0",
    author="Kitchen Safety Team",
    author_email="team@kitchensafety.com",
    description="基于计算机视觉和深度学习的厨房安全检测系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kitchen-safety/detection-system",
    packages=find_packages(),
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
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-django>=4.5.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "deploy": [
            "gunicorn>=20.1.0",
            "docker>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kitchen-safety=kitchen_safety_system.main:main",
            "kitchen-safety-web=kitchen_safety_system.web.manage:main",
        ],
    },
    include_package_data=True,
    package_data={
        "kitchen_safety_system": [
            "config/*.yaml",
            "config/*.json",
            "models/*.pt",
            "web/static/*",
            "web/templates/*",
        ],
    },
)
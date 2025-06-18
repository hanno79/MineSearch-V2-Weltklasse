from setuptools import setup, find_packages

setup(
    name="mine-search",
    version="1.0.0",
    author="rahn",
    description="Multi-Agent Mining Research System",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        line.strip()
        for line in open("requirements.txt").readlines()
        if not line.startswith("#") and line.strip()
    ],
    entry_points={
        "console_scripts": [
            "mine-search=ui.main:main",
        ],
    },
)
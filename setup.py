from setuptools import setup, find_packages

setup(
    name="hr_analysis_system",
    version="0.1",
    packages=find_packages(),
    package_dir={"": "src"},
    install_requires=[
        "openai",
        "numpy",
        "pandas",
        "streamlit",
        "pytest",
        "pytest-asyncio",
        "pytest-cov"
    ],
)
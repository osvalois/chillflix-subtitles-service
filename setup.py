from setuptools import setup, find_packages

setup(
    name="subtitles-api",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn",
        "aiohttp",
        "pydantic",
        "python-dotenv",
        "pydantic-settings",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
            "isort",
        ],
    },
)
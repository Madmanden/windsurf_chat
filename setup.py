from setuptools import setup, find_packages

setup(
    name="cli-llm-chat",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.5.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        'console_scripts': [
            'llmchat=cli_llm_chat.main:app.run',
        ],
    },
    python_requires=">=3.9",
    author="User",
    author_email="user@example.com",
    description="CLI app for chatting with LLMs via OpenRouter API",
    keywords="cli, llm, chat, openrouter",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
)

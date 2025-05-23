from setuptools import setup

setup(
    name="ai_databricks_package",
    version="{PACKAGE.VERSION}",
    author="Airton Lira Junior",
    author_email="airtonlirajr@gmail.com",
    install_requires=[
        "requests>=2.32.3",
        "boto3>=1.38.10",
        "botocore>=1.38.10"
    ],
    extras_require={
        "aws": [
            "boto3>=1.38.10",
            "botocore>=1.38.10"
        ],
        "text-processing": [
            "beautifulsoup4>=4.13.4",
            "lxml>=5.4.0",
            "langchain_core>=0.3.58",
            "langchain_text_splitters>=0.3.8",
            "strip_markdown>=1.3"
        ],
        "embedding": [
            "langchain_huggingface>=0.2.0",
            "python_certifi_win32>=1.6.1",
        ],
        "pdf": [
            "pdfminer.six>=20250506"
        ],
        "confluence": [
            "atlassian_python_api>=4.0.3",
            "docling>=2.31.0",
            "beautifulsoup4>=4.13.4",
            "lxml>=5.4.0"
        ],
        "databricks": [
            "databricks_sdk>=0.52.0",
            "databricks_vectorsearch>=0.56",
            "pyspark>=3.5.5",
            "pandas>=2.2.3"
        ],
        "ml": [
            "mlflow_skinny>=2.22.0",
            "pandas>=2.2.3"
        ],
        "all": [
            "beautifulsoup4>=4.13.4",
            "lxml>=5.4.0",
            "requests>=2.32.3",
            "langchain_core>=0.3.58",
            "langchain_text_splitters>=0.3.8",
            "langchain_huggingface>=0.2.0",
            "python_certifi_win32>=1.6.1",
            "strip_markdown>=1.3",
            "atlassian_python_api>=4.0.3",
            "docling>=2.31.0",
            "mlflow_skinny>=2.22.0",
            "pandas>=2.2.3",
            "pdfminer.six>=20250506",
            "boto3>=1.38.10",
            "botocore>=1.38.10",
            "databricks_sdk>=0.52.0",
            "databricks_vectorsearch>=0.56",
            "pyspark>=3.5.5"
        ]
    }
)

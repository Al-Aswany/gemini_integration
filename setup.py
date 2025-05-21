from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# Get version from __version__ variable in erpnext_gemini_integration/__init__.py
from erpnext_gemini_integration import __version__ as version

setup(
    name="erpnext_gemini_integration",
    version=version,
    description="Integration of Google's Gemini AI capabilities into ERPNext",
    author="Al-Aswany",
    author_email="user@example.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Framework :: Frappe",
    ],
)

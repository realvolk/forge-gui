from setuptools import setup, find_packages

setup(
    name="forge-gui",
    version="0.3.0",
    description="GTK3 GUI frontend for ArtixForge and VFF",
    author="Volk",
    license="Volk Open License 1.0",
    packages=find_packages(),
    install_requires=[
        "jsonschema>=4.0.0",
        "pygobject>=3.42.0",
    ],
    entry_points={
        "console_scripts": [
            "forge-gui = forge_ui.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
    ],
)
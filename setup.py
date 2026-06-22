from setuptools import setup, find_packages

setup(
    name="forge-gui",
    version="0.4.1",
    description="GTK4 GUI frontend for ArtixForge and VFF",
    author="Volk",
    license="Forge Attribution License 1.0",
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
#imports
import sys
import pip

# update the pip package installer
pip.main(["install", "--upgrade", "pip"])
# install required packages
pip.main(["install", "uproot"])
pip.main(["install", "awkward"])
pip.main(["install", "vector"])
pip.main(["install", "numpy"])
pip.main(["install", "matplotlib"])


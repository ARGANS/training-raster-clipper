#### RUN ME #### 
# 
# From the project's root, run:
#
# scripts/clean.sh
# 
# or 
# bash scripts/clean.sh
# 
# This will prune and sort imports, then format the code.


echo 'Prune unused imports with `pautoflake`'
poetry run pautoflake      src tests


echo 'Sort imports with `isort`'
poetry run isort           src tests


echo 'Format the code with `black`'
poetry run black --preview src tests
# The preview flag enables the breaking of long strings over multiple lines
# See https://github.com/psf/black/issues/1802

echo 'Format docstrings with `docformatter`'
poetry run docformatter --in-place --black --wrap-summaries 88 --wrap-descriptions 88 --pre-summary-newline --recursive src

# Note: enable pylint only for a specific rule
# poetry run pylint --disable=all --enable=missing-module-docstring src

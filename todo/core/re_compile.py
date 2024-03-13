import re

DATE_PATTERN = re.compile(r'(\d+)[\.](\d+)[\.]?')
COMMAND_PATTERN = re.compile(r'(.*?)(?=\@)')
WORD_PATTERN = re.compile(r'\b\w+\b')

# encoding: utf8

from pathlib import Path

# encodings.
CORPUS_ENCODING = "gb18030"
QUERY_ENCODING = "utf8"
OUTPUT_ENCODING = "utf8"

# files.
QUERY_FILE = Path(__file__).parent / "words_set_small.txt" # 查询词集文件路径，请勿改动
CORPUS_PATH = Path(__file__).parents[1] / "整理后语料V3/整理后语料V3/xiandai" # 现代汉语部分语料库路径，请勿改动
ANCIENT_CORPUS_PATH = Path(__file__).parents[1] / "整理后语料V3/整理后语料V3/gudai" # 古代汉语部分语料库路径，请勿改动

# output.
OUTPUT_DIR = Path(__file__).parent / "query_result" # 输出文件夹路径，请勿改动

# 查找范围，与CCL在线查找的时间范围一致
SUB_PATHS = [
    "1900s",
    "1910s", 
    "1920s",
    "1930s",
    "1940s",
    "1950s",
    "1960s",
    "1970s",
    "1980s",
    "1990s",
    "2000s",
    "2010s",
    "2020s", 
    "CWAC", 
]

# 显示范围
DISPLAY_WINDOW = 50

# batch size.
BATCH_SIZE = 100
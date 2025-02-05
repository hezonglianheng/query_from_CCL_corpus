# encoding: utf8

import config
import aiofiles
import asyncio
from collections.abc import Iterator
from pathlib import Path
import re
from itertools import product

def read_query_file() -> Iterator[str]:
    """读取查询词集文件

    Yields:
        Iterator[str]: 查询词
    """
    with open(config.QUERY_FILE, "r", encoding=config.QUERY_ENCODING) as f:
        for line in f:
            yield line.strip()

async def word_match(word: str, file_path: Path, ancestor_path: Path):
    """查找语料库中的匹配词，并将匹配的文本片段写入文件

    Args:
        word (str): 待匹配的词
        file_path (Path): 语料文件路径
        ancestor_path (Path): 语料库根目录路径
    """
    # 去除file_path中的前缀路径
    output_path = file_path.relative_to(ancestor_path)
    # 获得一系列匹配的文本片段
    matched: list[str] = []
    try:
        async with aiofiles.open(file_path, "r", encoding=config.CORPUS_ENCODING, errors="ignore") as f:
            content = await f.read()
            for match in re.finditer(word, content):
                # 查找距离匹配词最近的上一个换行符位置，没有则置为0
                last_newline = content.rfind("\n", 0, match.start())
                if last_newline == -1:
                    last_newline = 0
                # 查找距离匹配词最近的下一个换行符位置，没有则置为文本末尾
                next_newline = content.find("\n", match.end())
                if next_newline == -1:
                    next_newline = len(content)
                start_position = max(0, match.start() - config.DISPLAY_WINDOW, last_newline + 1)
                end_position = min(len(content), match.end() + config.DISPLAY_WINDOW, next_newline)
                matched_slice = content[start_position:match.start()] + "【" + content[match.start():match.end()] + "】" + content[match.end():end_position]
                matched.append(matched_slice)
    except Exception as e:
        print(f"读取{file_path}失败: {e}")
    # 将匹配的文本片段写入文件
    if len(matched) > 0:
        with open(config.OUTPUT_DIR / (word + ".txt"), "a", encoding=config.OUTPUT_ENCODING) as f:
            for line in matched:
                f.write(f"【来源: {output_path}】" + line + "\n")
                print(f"在{output_path}中找到匹配词“{word}”")

def sub_corpus_match(word: str, sub_path: str):
    """查找语料库中的匹配词，并将匹配的文本片段写入文件

    Args:
        word (str): 待匹配的词
        sub_path (str): 语料库的子路径
    """
    async def process_files():
        tasks = []
        files = list(Path(config.CORPUS_PATH / sub_path).rglob("*.txt"))

        for batch in [files[i:i + config.BATCH_SIZE] for i in range(0, len(files), config.BATCH_SIZE)]:
            batch_tasks = [word_match(word, file_path, config.CORPUS_PATH) for file_path in batch]
            tasks.extend(batch_tasks)

        await asyncio.gather(*tasks)

    asyncio.run(process_files())

def ancient_corpus_match(word: str):
    """查找古代语料库中的匹配词，并将匹配的文本片段写入文件

    Args:
        word (str): 待匹配的词
    """
    async def process_files():
        tasks = []
        files = list(config.ANCIENT_CORPUS_PATH.rglob("*.txt"))

        for batch in [files[i:i + config.BATCH_SIZE] for i in range(0, len(files), config.BATCH_SIZE)]:
            batch_tasks = [word_match(word, file_path, config.ANCIENT_CORPUS_PATH) for file_path in batch]
            tasks.extend(batch_tasks)

        await asyncio.gather(*tasks)

    asyncio.run(process_files())

def main():
    """程序主函数
    """
    # 清空输出文件夹
    for file in Path(config.OUTPUT_DIR).rglob("*.txt"):
        file.unlink()
    # 读取查询词集文件
    for word, subpath in product(read_query_file(), config.SUB_PATHS):
        ancient_corpus_match(word) # 先查找古代语料库
        sub_corpus_match(word, subpath) # 再查找现代语料库

if __name__ == "__main__":
    main()
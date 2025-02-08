# encoding: utf8

import config
from pathlib import Path
import re
from concurrent.futures import ThreadPoolExecutor
import time
from threading import Lock
from typing import TextIO

class FilePool:
    """文件句柄池
    """
    def __init__(self, max_files=1000, timeout=300):
        self.max_files = max_files
        self.timeout = timeout  # 文件句柄超时时间(秒)
        self.files: dict[Path, tuple[int, TextIO, list[str]]] = {}  # {路径: (最后访问时间, 文件对象)}
        self.lock = Lock()
    
    def get_file(self, file_path: Path) -> list[str]:
        """获取文件句柄

        Args:
            file_path (Path): 文件路径

        Returns:
            list[str]: 文件内容
        """
        with self.lock:
            current_time = int(time.time())
            
            # 清理超时的文件句柄
            self._cleanup(current_time)
            
            # 如果文件已在池中且未超时，更新访问时间并返回
            if file_path in self.files:
                _, file_obj, lines = self.files[file_path]
                self.files[file_path] = (current_time, file_obj, lines)
                # return file_obj
                return lines
            
            # 如果池已满，清理最旧的文件
            if len(self.files) >= self.max_files:
                oldest_path = min(self.files.items(), key=lambda x: x[1][0])[0]
                self._close_file(oldest_path)
            
            # 打开新文件
            file_obj = open(file_path, 'r', encoding=config.CORPUS_ENCODING, errors="ignore")
            lines = file_obj.readlines()
            self.files[file_path] = (current_time, file_obj, lines)
            # return file_obj
            return lines
    
    def _cleanup(self, current_time: int):
        """清理超时的文件句柄"""
        expired = [
            path for path, (last_access, _, lines) in self.files.items()
            if current_time - last_access > self.timeout
        ]
        for path in expired:
            self._close_file(path)
    
    def _close_file(self, file_path: Path):
        """关闭并移除文件句柄"""
        if file_path in self.files:
            _, file_obj, lines = self.files[file_path]
            file_obj.close()
            del self.files[file_path]
    
    def close_all(self):
        """关闭所有文件句柄"""
        with self.lock:
            for path in list(self.files.keys()):
                self._close_file(path)


def read_query_file(curr_query: str) -> list[str]:
    """读取查询词集文件

    Args:
        curr_query (str): 查询词集文件路径

    Returns:
        list[str]: 查询词集列表
    """
    with open(curr_query, "r", encoding=config.QUERY_ENCODING) as f:
        return [line.strip() for line in f]

def word_match(word: str, file_path: Path, ancestor_path: Path, file_pool: FilePool):
    """查找语料库中的匹配词，并将匹配的文本片段写入文件

    Args:
        word (str): 待匹配的词
        file_path (Path): 语料文件路径
        ancestor_path (Path): 语料库根目录路径
        file_pool (FilePool): 文件句柄池
    """
    # 去除file_path中的前缀路径
    output_path = file_path.relative_to(ancestor_path)
    # 获得一系列匹配的文本片段
    matched: list[str] = []
    try:
        lines = file_pool.get_file(file_path)
        for line in lines:
            for match in re.finditer(word, line):
                start_position = max(0, match.start() - config.DISPLAY_WINDOW)
                end_position = min(len(line), match.end() + config.DISPLAY_WINDOW)
                matched_slice = line[start_position:match.start()] + "【" + line[match.start():match.end()] + "】" + line[match.end():end_position]
                matched.append(matched_slice)
    except Exception as e:
        print(f"读取{file_path}失败: {e}")
    
    # 将匹配的文本片段写入文件
    if len(matched) > 0:
        with open(config.OUTPUT_DIR / (word + ".txt"), "a", encoding=config.OUTPUT_ENCODING) as f:
            for line in matched:
                if line[-1] != "\n":
                    line += "\n"
                f.write(f"【来源: {output_path}】" + line)
                print(f"在{output_path}中找到匹配词“{word}”")

def sub_corpus_match(word_batch: list[str], sub_path: str):
    """查找语料库中的匹配词，并将匹配的文本片段写入文件

    Args:
        sub_path (str): 语料库的子路径
    """
    file_pool = FilePool()
    try:
        files = list(Path(config.CORPUS_PATH / sub_path).rglob("*.txt"))
        batches = [files[i:i + config.BATCH_SIZE] for i in range(0, len(files), config.BATCH_SIZE)]

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            for batch in batches:
                for file_path in batch:
                    for word in word_batch:
                        executor.submit(word_match, word, file_path, config.CORPUS_PATH, file_pool)
    finally:
        file_pool.close_all()

def ancient_corpus_match(word_batch: list[str]):
    """查找古代语料库中的匹配词，并将匹配的文本片段写入文件
    """
    file_pool = FilePool()
    try:
        files = list(config.ANCIENT_CORPUS_PATH.rglob("*.txt"))
        batches = [files[i:i + config.BATCH_SIZE] for i in range(0, len(files), config.BATCH_SIZE)]

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            for batch in batches:
                for file_path in batch:
                    for word in word_batch:
                        executor.submit(word_match, word, file_path, config.CORPUS_PATH, file_pool)
    finally:
        file_pool.close_all()

def process(curr_query: str):
    """
    处理查询词集文件主函数

    Args:
        curr_query (str): 查询词集文件路径
    """
    words = read_query_file(curr_query)
    word_batches: list[list[str]] = [words[i:i + config.WORD_BATCH_SIZE] for i in range(0, len(words), config.WORD_BATCH_SIZE)]
    print(f"共{len(words)}个查询词，分为{len(word_batches)}个批次")
    for i, word_batch in enumerate(word_batches, start=1):
        start_time = time.time()
        print(f"正在处理第{i}批次...")
        ancient_corpus_match(word_batch)
        for sub_path in config.SUB_PATHS:
            sub_corpus_match(word_batch, sub_path)
        end_time = time.time()
        print(f"第{i}批次处理完毕，耗时{end_time - start_time:.2f}秒")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="查找语料库中词表词的匹配")
    parser.add_argument("query_file", type=str, help="查询词集文件路径")
    args = parser.parse_args()
    process(args.query_file)
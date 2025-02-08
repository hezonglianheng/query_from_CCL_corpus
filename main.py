# encoding: utf8

import config
from pathlib import Path
import subprocess

# 子进程数量
sub_process_num = 8

def main():
    # 清空输出文件夹
    for file in Path(config.OUTPUT_DIR).rglob("*.txt"):
        file.unlink()
    print("输出文件夹已清空，开始查找匹配词")
    # 读取words_set.txt中的词表
    with open(config.QUERY_FILE, "r", encoding=config.QUERY_ENCODING) as f:
        words = f.readlines()
    # 按照子进程数量分批
    word_batches: list[list[str]] = [words[i:i + len(words) // sub_process_num] for i in range(0, len(words), len(words) // sub_process_num)]
    # 创建临时批处理文件夹
    Path("temp_batch").mkdir(exist_ok=True)
    # 将每个批次的词表写入临时文件
    for i, word_batch in enumerate(word_batches):
        with open(f"temp_batch/batch_{i}.txt", "w", encoding=config.QUERY_ENCODING) as f:
            f.writelines(word_batch)
    # 创建子进程
    processes = []
    for i in range(sub_process_num):
        processes.append(subprocess.Popen(["python", "process.py", f"temp_batch/batch_{i}.txt"]))
    # 等待子进程结束
    for process in processes:
        process.wait()
    # 删除临时文件夹
    for file in Path("temp_batch").rglob("*"):
        file.unlink()
    Path("temp_batch").rmdir()

if __name__ == "__main__":
    main()
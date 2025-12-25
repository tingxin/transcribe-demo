#!/usr/bin/env python3
"""
缓存管理脚本
用于查看和清理音频文件缓存
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from transcribe_audio import AudioTranscriber
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 manage_cache.py info          # 查看缓存信息")
        print("  python3 manage_cache.py clean [days]  # 清理缓存 (默认7天)")
        print("  python3 manage_cache.py clear         # 清空所有缓存")
        return
    
    command = sys.argv[1].lower()
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    transcriber = AudioTranscriber(aws_region=aws_region)
    
    if command == 'info':
        # 显示缓存信息
        cache_info = transcriber.get_cache_info()
        if cache_info:
            print(f"缓存目录: {cache_info['cache_dir']}")
            print(f"文件数量: {cache_info['file_count']}")
            print(f"总大小: {cache_info['total_size_mb']:.2f} MB")
        else:
            print("无法获取缓存信息")
    
    elif command == 'clean':
        # 清理过期缓存
        days = 7
        if len(sys.argv) > 2:
            try:
                days = int(sys.argv[2])
            except ValueError:
                print("错误: 天数必须是整数")
                return
        
        print(f"清理超过 {days} 天的缓存文件...")
        transcriber.clean_cache(max_age_days=days)
    
    elif command == 'clear':
        # 清空所有缓存
        confirm = input("确定要删除所有缓存文件吗? (y/N): ")
        if confirm.lower() == 'y':
            transcriber.clean_cache(max_age_days=0)
            print("所有缓存文件已删除")
        else:
            print("操作已取消")
    
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main()
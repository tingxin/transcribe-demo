#!/usr/bin/env python3
"""
分析转录JSON文件的数据结构
"""

import json
import os
from pathlib import Path

def analyze_transcript_structure():
    """分析转录文件的数据结构"""
    
    # 查找test_transcript.json文件
    json_file = Path('test_results/test_transcript.json')
    
    if not json_file.exists():
        print("未找到test_transcript.json文件")
        return
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("=== 转录文件数据结构分析 ===\n")
        
        # 分析顶层结构
        print("顶层键:", list(data.keys()))
        
        if 'full_result' in data:
            full_result = data['full_result']
            print("\nfull_result结构:")
            print("  类型:", type(full_result))
            print("  键:", list(full_result.keys()) if isinstance(full_result, dict) else "不是字典")
            
            if 'results' in full_result:
                results = full_result['results']
                print(f"\nresults结构:")
                print(f"  类型: {type(results)}")
                
                if isinstance(results, dict):
                    print(f"  键: {list(results.keys())}")
                    
                    # 检查说话人标签
                    if 'speaker_labels' in results:
                        speaker_labels = results['speaker_labels']
                        print(f"\nspeaker_labels结构:")
                        print(f"  类型: {type(speaker_labels)}")
                        print(f"  键: {list(speaker_labels.keys()) if isinstance(speaker_labels, dict) else '不是字典'}")
                        
                        if isinstance(speaker_labels, dict) and 'segments' in speaker_labels:
                            segments = speaker_labels['segments']
                            print(f"  segments数量: {len(segments)}")
                            if len(segments) > 0:
                                print(f"  第一个segment结构: {list(segments[0].keys())}")
                                print(f"  第一个segment内容: {segments[0]}")
                    
                    # 检查声道标签
                    if 'channel_labels' in results:
                        channel_labels = results['channel_labels']
                        print(f"\nchannel_labels结构:")
                        print(f"  类型: {type(channel_labels)}")
                        print(f"  键: {list(channel_labels.keys()) if isinstance(channel_labels, dict) else '不是字典'}")
                        
                        if isinstance(channel_labels, dict) and 'channels' in channel_labels:
                            channels = channel_labels['channels']
                            print(f"  channels数量: {len(channels)}")
                            if len(channels) > 0:
                                print(f"  第一个channel结构: {list(channels[0].keys())}")
                                # 只显示前几个items
                                if 'items' in channels[0]:
                                    items = channels[0]['items']
                                    print(f"  第一个channel的items数量: {len(items)}")
                                    if len(items) > 0:
                                        print(f"  第一个item结构: {list(items[0].keys())}")
                                        print(f"  第一个item内容: {items[0]}")
                
                elif isinstance(results, list):
                    print(f"  长度: {len(results)}")
                    if len(results) > 0:
                        print(f"  第一个元素类型: {type(results[0])}")
                        print(f"  第一个元素键: {list(results[0].keys()) if isinstance(results[0], dict) else '不是字典'}")
        
        # 检查现有的labeled_transcript
        if 'labeled_transcript' in data:
            labeled = data['labeled_transcript']
            print(f"\n现有labeled_transcript:")
            print(f"  长度: {len(labeled)}")
            print(f"  内容: '{labeled}'")
        
    except Exception as e:
        print(f"分析失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_transcript_structure()
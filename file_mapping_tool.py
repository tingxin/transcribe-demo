#!/usr/bin/env python3
"""
文件映射查询工具
用于查询转录文件与call.csv记录的对应关系
"""

import json
import pandas as pd
from pathlib import Path
import argparse
import sys

class FileMappingTool:
    def __init__(self, transcripts_dir='transcripts', csv_file='call.csv'):
        """
        初始化映射工具
        
        Args:
            transcripts_dir: 转录文件目录
            csv_file: CSV文件路径
        """
        self.transcripts_dir = Path(transcripts_dir)
        self.csv_file = csv_file
        self.mapping_file = self.transcripts_dir / 'file_mapping.json'
        
        # 加载映射数据
        self.load_mapping()
        self.load_csv()
    
    def load_mapping(self):
        """加载文件映射数据"""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    self.mapping_data = json.load(f)
                print(f"✓ 已加载映射文件: {self.mapping_file}")
                print(f"  包含 {len(self.mapping_data)} 个文件映射记录")
            except Exception as e:
                print(f"✗ 加载映射文件失败: {e}")
                self.mapping_data = {}
        else:
            print(f"✗ 映射文件不存在: {self.mapping_file}")
            self.mapping_data = {}
    
    def load_csv(self):
        """加载CSV数据"""
        try:
            self.csv_data = pd.read_csv(self.csv_file)
            print(f"✓ 已加载CSV文件: {self.csv_file}")
            print(f"  包含 {len(self.csv_data)} 行记录")
        except Exception as e:
            print(f"✗ 加载CSV文件失败: {e}")
            self.csv_data = None
    
    def find_by_csv_row(self, row_index):
        """
        根据CSV行号查找对应的转录文件
        
        Args:
            row_index: CSV行号
            
        Returns:
            dict: 映射信息，如果未找到返回None
        """
        for json_file, mapping in self.mapping_data.items():
            if mapping['csv_row_index'] == row_index:
                return mapping
        return None
    
    def find_by_call_id(self, call_id):
        """
        根据催收外呼ID查找对应的转录文件
        
        Args:
            call_id: 催收外呼ID
            
        Returns:
            dict: 映射信息，如果未找到返回None
        """
        call_id_str = str(call_id)
        for json_file, mapping in self.mapping_data.items():
            if mapping.get('call_id') == call_id_str:
                return mapping
        return None
    
    def find_by_customer_id(self, customer_id):
        """
        根据客户号查找对应的转录文件
        
        Args:
            customer_id: 客户号
            
        Returns:
            list: 映射信息列表（一个客户可能有多个通话记录）
        """
        customer_id_str = str(customer_id)
        results = []
        for json_file, mapping in self.mapping_data.items():
            if mapping.get('customer_id') == customer_id_str:
                results.append(mapping)
        return results
    
    def find_by_filename(self, filename):
        """
        根据文件名查找对应的CSV记录
        
        Args:
            filename: JSON或TXT文件名
            
        Returns:
            dict: 映射信息，如果未找到返回None
        """
        # 移除扩展名，支持查找JSON或TXT文件
        base_name = filename.replace('.json', '').replace('.txt', '')
        
        for json_file, mapping in self.mapping_data.items():
            json_base = mapping['json_file'].replace('.json', '')
            txt_base = mapping['txt_file'].replace('.txt', '')
            
            if base_name == json_base or base_name == txt_base or filename == mapping['json_file'] or filename == mapping['txt_file']:
                return mapping
        return None
    
    def list_all_mappings(self):
        """列出所有映射关系"""
        if not self.mapping_data:
            print("没有找到映射数据")
            return
        
        print(f"\n=== 所有文件映射关系 (共 {len(self.mapping_data)} 个) ===")
        
        # 按CSV行号排序
        sorted_mappings = sorted(self.mapping_data.items(), 
                               key=lambda x: x[1]['csv_row_index'])
        
        for json_file, mapping in sorted_mappings:
            print(f"\nCSV行号: {mapping['csv_row_index']}")
            if mapping.get('call_id'):
                print(f"催收外呼ID: {mapping['call_id']}")
            if mapping.get('customer_id'):
                print(f"客户号: {mapping['customer_id']}")
            print(f"JSON文件: {mapping['json_file']}")
            print(f"TXT文件: {mapping['txt_file']}")
            print(f"处理时间: {mapping['processed_time']}")
            print("-" * 50)
    
    def verify_files_exist(self):
        """验证映射的文件是否实际存在"""
        print("\n=== 验证文件存在性 ===")
        
        missing_files = []
        existing_files = []
        
        for json_file, mapping in self.mapping_data.items():
            json_path = self.transcripts_dir / mapping['json_file']
            txt_path = self.transcripts_dir / mapping['txt_file']
            
            json_exists = json_path.exists()
            txt_exists = txt_path.exists()
            
            if json_exists and txt_exists:
                existing_files.append(mapping)
            else:
                missing_files.append({
                    'mapping': mapping,
                    'json_exists': json_exists,
                    'txt_exists': txt_exists
                })
        
        print(f"✓ 存在的文件对: {len(existing_files)}")
        print(f"✗ 缺失的文件对: {len(missing_files)}")
        
        if missing_files:
            print("\n缺失的文件:")
            for item in missing_files:
                mapping = item['mapping']
                print(f"  CSV行号 {mapping['csv_row_index']}:")
                if not item['json_exists']:
                    print(f"    ✗ {mapping['json_file']}")
                if not item['txt_exists']:
                    print(f"    ✗ {mapping['txt_file']}")
    
    def get_csv_record(self, row_index):
        """
        获取CSV中指定行的完整记录
        
        Args:
            row_index: CSV行号
            
        Returns:
            dict: CSV记录，如果未找到返回None
        """
        if self.csv_data is None:
            return None
        
        try:
            if row_index < len(self.csv_data):
                return self.csv_data.iloc[row_index].to_dict()
            else:
                return None
        except Exception as e:
            print(f"获取CSV记录失败: {e}")
            return None
    
    def search_interactive(self):
        """交互式搜索"""
        print("\n=== 交互式文件映射查询 ===")
        print("输入 'quit' 或 'exit' 退出")
        print("支持的查询类型:")
        print("  1. CSV行号: 输入数字，如 '5'")
        print("  2. 催收外呼ID: 输入 'call:ID'，如 'call:1234567890'")
        print("  3. 客户号: 输入 'customer:ID'，如 'customer:8000000000'")
        print("  4. 文件名: 输入文件名，如 'transcript_call_1234_row_5.json'")
        print("  5. 列出所有: 输入 'list'")
        print("  6. 验证文件: 输入 'verify'")
        
        while True:
            try:
                query = input("\n请输入查询条件: ").strip()
                
                if query.lower() in ['quit', 'exit']:
                    break
                
                if query.lower() == 'list':
                    self.list_all_mappings()
                    continue
                
                if query.lower() == 'verify':
                    self.verify_files_exist()
                    continue
                
                if query.startswith('call:'):
                    call_id = query[5:]
                    result = self.find_by_call_id(call_id)
                    if result:
                        self.print_mapping_result(result)
                    else:
                        print(f"未找到催收外呼ID为 '{call_id}' 的记录")
                
                elif query.startswith('customer:'):
                    customer_id = query[9:]
                    results = self.find_by_customer_id(customer_id)
                    if results:
                        print(f"找到客户号 '{customer_id}' 的 {len(results)} 条记录:")
                        for i, result in enumerate(results, 1):
                            print(f"\n--- 记录 {i} ---")
                            self.print_mapping_result(result)
                    else:
                        print(f"未找到客户号为 '{customer_id}' 的记录")
                
                elif query.isdigit():
                    row_index = int(query)
                    result = self.find_by_csv_row(row_index)
                    if result:
                        self.print_mapping_result(result)
                        # 同时显示CSV中的原始记录
                        csv_record = self.get_csv_record(row_index)
                        if csv_record:
                            print("\nCSV原始记录:")
                            for key, value in csv_record.items():
                                if pd.notna(value) and str(value).strip():
                                    print(f"  {key}: {value}")
                    else:
                        print(f"未找到CSV行号为 {row_index} 的记录")
                
                else:
                    # 尝试作为文件名查找
                    result = self.find_by_filename(query)
                    if result:
                        self.print_mapping_result(result)
                    else:
                        print(f"未找到文件名为 '{query}' 的记录")
                        print("提示: 请检查文件名是否正确，或使用其他查询方式")
            
            except KeyboardInterrupt:
                print("\n\n再见!")
                break
            except Exception as e:
                print(f"查询出错: {e}")
    
    def print_mapping_result(self, mapping):
        """打印映射结果"""
        print(f"\n=== 找到匹配记录 ===")
        print(f"CSV行号: {mapping['csv_row_index']}")
        if mapping.get('call_id'):
            print(f"催收外呼ID: {mapping['call_id']}")
        if mapping.get('customer_id'):
            print(f"客户号: {mapping['customer_id']}")
        print(f"JSON文件: {mapping['json_file']}")
        print(f"TXT文件: {mapping['txt_file']}")
        print(f"处理时间: {mapping['processed_time']}")
        
        # 检查文件是否存在
        json_path = self.transcripts_dir / mapping['json_file']
        txt_path = self.transcripts_dir / mapping['txt_file']
        
        print(f"JSON文件存在: {'✓' if json_path.exists() else '✗'}")
        print(f"TXT文件存在: {'✓' if txt_path.exists() else '✗'}")
        
        if mapping.get('other_fields'):
            print("\n其他字段:")
            for key, value in mapping['other_fields'].items():
                if value:
                    print(f"  {key}: {value}")


def main():
    parser = argparse.ArgumentParser(description='文件映射查询工具')
    parser.add_argument('--transcripts-dir', default='transcripts', 
                       help='转录文件目录 (默认: transcripts)')
    parser.add_argument('--csv-file', default='call.csv', 
                       help='CSV文件路径 (默认: call.csv)')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='启动交互式查询模式')
    parser.add_argument('--list', '-l', action='store_true',
                       help='列出所有映射关系')
    parser.add_argument('--verify', '-v', action='store_true',
                       help='验证文件存在性')
    parser.add_argument('--csv-row', type=int,
                       help='根据CSV行号查询')
    parser.add_argument('--call-id',
                       help='根据催收外呼ID查询')
    parser.add_argument('--customer-id',
                       help='根据客户号查询')
    parser.add_argument('--filename',
                       help='根据文件名查询')
    
    args = parser.parse_args()
    
    # 创建映射工具实例
    tool = FileMappingTool(args.transcripts_dir, args.csv_file)
    
    if not tool.mapping_data:
        print("没有找到映射数据，请先运行转录脚本生成映射文件")
        sys.exit(1)
    
    # 根据参数执行相应操作
    if args.interactive:
        tool.search_interactive()
    elif args.list:
        tool.list_all_mappings()
    elif args.verify:
        tool.verify_files_exist()
    elif args.csv_row is not None:
        result = tool.find_by_csv_row(args.csv_row)
        if result:
            tool.print_mapping_result(result)
        else:
            print(f"未找到CSV行号为 {args.csv_row} 的记录")
    elif args.call_id:
        result = tool.find_by_call_id(args.call_id)
        if result:
            tool.print_mapping_result(result)
        else:
            print(f"未找到催收外呼ID为 '{args.call_id}' 的记录")
    elif args.customer_id:
        results = tool.find_by_customer_id(args.customer_id)
        if results:
            print(f"找到客户号 '{args.customer_id}' 的 {len(results)} 条记录:")
            for i, result in enumerate(results, 1):
                print(f"\n--- 记录 {i} ---")
                tool.print_mapping_result(result)
        else:
            print(f"未找到客户号为 '{args.customer_id}' 的记录")
    elif args.filename:
        result = tool.find_by_filename(args.filename)
        if result:
            tool.print_mapping_result(result)
        else:
            print(f"未找到文件名为 '{args.filename}' 的记录")
    else:
        # 默认启动交互式模式
        tool.search_interactive()


if __name__ == "__main__":
    main()
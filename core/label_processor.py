#!/usr/bin/env python3
"""
标签处理模块

功能：
- 标签删除：删除指定标签，若JSON文件无其他标签则删除文件
- 标签导出：导出包含指定标签的JSON文件和对应图片
- 标签替换：将指定标签名称替换为新名称

作者：数据集处理工具
版本：1.0
"""

import os
import json
import shutil
from typing import Optional, Callable, List, Dict
from pathlib import Path
import time

class LabelProcessor:
    """标签处理主类"""
    
    # 支持的图片格式
    IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'}
    
    def __init__(self, source_dir: str,
                 recursive: bool = True,
                 backup_enabled: bool = False,
                 backup_dir: str = "",
                 progress_callback: Optional[Callable] = None,
                 log_callback: Optional[Callable] = None):
        """
        初始化标签处理器
        
        Args:
            source_dir: 源目录路径
            recursive: 是否递归遍历子文件夹
            backup_enabled: 是否启用备份
            backup_dir: 备份目录路径
            progress_callback: 进度回调函数
            log_callback: 日志回调函数
        """
        self.source_dir = source_dir
        self.recursive = recursive
        self.backup_enabled = backup_enabled
        self.backup_dir = backup_dir
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        
        # 统计信息
        self.total_files = 0
        self.processed_files = 0
        self.error_files = []
        self.modified_files = []
        self.deleted_files = []
        self.exported_files = []
        
        # 处理状态标志
        self.is_running = True
    
    def log(self, message: str):
        """记录日志"""
        if self.log_callback:
            self.log_callback(message)
        print(message)
    
    def update_progress(self, progress: float):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(progress)
    
    def get_json_files(self) -> List[str]:
        """
        获取所有JSON标注文件
        
        Returns:
            JSON文件路径列表
        """
        json_files = []
        
        try:
            if self.recursive:
                # 递归遍历
                for root, dirs, files in os.walk(self.source_dir):
                    for file in files:
                        if file.lower().endswith('.json'):
                            json_files.append(os.path.join(root, file))
            else:
                # 只遍历当前目录
                for file in os.listdir(self.source_dir):
                    if file.lower().endswith('.json'):
                        file_path = os.path.join(self.source_dir, file)
                        if os.path.isfile(file_path):
                            json_files.append(file_path)
        except Exception as e:
            self.log(f"遍历目录时出错: {e}")
        
        return json_files
    
    def find_image_file(self, json_path: str) -> Optional[str]:
        """
        根据JSON文件路径查找对应的图片文件
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            对应的图片文件路径，找不到返回None
        """
        # 获取JSON文件的目录和基础文件名
        json_dir = os.path.dirname(json_path)
        json_name = os.path.splitext(os.path.basename(json_path))[0]
        
        # 在同一目录下查找同名的图片文件
        for ext in self.IMAGE_FORMATS:
            image_path = os.path.join(json_dir, json_name + ext)
            if os.path.exists(image_path):
                return image_path
        
        return None
    
    def backup_file(self, file_path: str) -> bool:
        """
        备份文件
        
        Args:
            file_path: 要备份的文件路径
            
        Returns:
            备份是否成功
        """
        if not self.backup_enabled or not self.backup_dir:
            return True
        
        try:
            # 创建备份目录
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # 计算相对路径，保持目录结构
            rel_path = os.path.relpath(file_path, self.source_dir)
            backup_path = os.path.join(self.backup_dir, rel_path)
            
            # 创建备份文件的目录
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # 复制文件
            shutil.copy2(file_path, backup_path)
            return True
            
        except Exception as e:
            self.log(f"备份文件失败 {file_path}: {e}")
            return False
    
    def load_json_file(self, json_path: str) -> Optional[Dict]:
        """
        加载JSON文件
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            JSON数据字典，失败返回None
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.log(f"读取JSON文件失败 {json_path}: {e}")
            self.error_files.append((json_path, f"读取失败: {e}"))
            return None
    
    def save_json_file(self, json_path: str, data: Dict) -> bool:
        """
        保存JSON文件
        
        Args:
            json_path: JSON文件路径
            data: JSON数据
            
        Returns:
            保存是否成功
        """
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.log(f"保存JSON文件失败 {json_path}: {e}")
            self.error_files.append((json_path, f"保存失败: {e}"))
            return False
    
    def delete_labels(self, target_labels: List[str]) -> bool:
        """
        删除指定标签
        
        Args:
            target_labels: 要删除的标签名称列表
            
        Returns:
            处理是否成功
        """
        try:
            self.log("开始标签删除处理...")
            start_time = time.time()
            
            # 获取所有JSON文件
            json_files = self.get_json_files()
            self.total_files = len(json_files)
            
            if self.total_files == 0:
                self.log("未找到任何JSON文件")
                return False
            
            self.log(f"找到 {self.total_files} 个JSON文件")
            
            for i, json_path in enumerate(json_files):
                # 加载JSON文件
                data = self.load_json_file(json_path)
                if data is None:
                    continue
                
                # 检查是否有shapes字段
                if 'shapes' not in data:
                    continue
                
                # 备份原文件（如果需要）
                if self.backup_enabled:
                    self.backup_file(json_path)
                
                # 过滤掉要删除的标签
                original_count = len(data['shapes'])
                data['shapes'] = [shape for shape in data['shapes'] 
                                if shape.get('label', '') not in target_labels]
                new_count = len(data['shapes'])
                
                deleted_count = original_count - new_count
                
                if deleted_count > 0:
                    if new_count == 0:
                        # 如果没有剩余标签，删除整个JSON文件
                        try:
                            os.remove(json_path)
                            self.deleted_files.append(json_path)
                            self.log(f"删除空标注文件: {os.path.basename(json_path)}")
                        except Exception as e:
                            self.log(f"删除文件失败 {json_path}: {e}")
                            self.error_files.append((json_path, f"删除失败: {e}"))
                    else:
                        # 保存修改后的JSON文件
                        if self.save_json_file(json_path, data):
                            self.modified_files.append(json_path)
                            self.log(f"修改文件: {os.path.basename(json_path)} (删除 {deleted_count} 个标签)")
                
                # 更新进度
                self.processed_files += 1
                progress = self.processed_files / self.total_files
                self.update_progress(progress)
            
            elapsed_time = time.time() - start_time
            self.log(f"标签删除处理完成！耗时: {elapsed_time:.2f}秒")
            self.log(f"修改文件: {len(self.modified_files)} 个")
            self.log(f"删除文件: {len(self.deleted_files)} 个")
            self.log(f"错误文件: {len(self.error_files)} 个")
            
            return True
            
        except Exception as e:
            self.log(f"标签删除处理过程中出现错误: {e}")
            return False
    
    def export_labels(self, target_labels: List[str], output_dir: str) -> bool:
        """
        导出包含指定标签的文件
        
        Args:
            target_labels: 要导出的标签名称列表
            output_dir: 输出目录
            
        Returns:
            处理是否成功
        """
        try:
            self.log("开始标签导出处理...")
            start_time = time.time()
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 获取所有JSON文件
            json_files = self.get_json_files()
            self.total_files = len(json_files)
            
            if self.total_files == 0:
                self.log("未找到任何JSON文件")
                return False
            
            self.log(f"找到 {self.total_files} 个JSON文件")
            
            for i, json_path in enumerate(json_files):
                # 加载JSON文件
                data = self.load_json_file(json_path)
                if data is None:
                    continue
                
                # 检查是否包含目标标签
                if 'shapes' in data:
                    has_target_label = any(shape.get('label', '') in target_labels 
                                         for shape in data['shapes'])
                    
                    if has_target_label:
                        try:
                            # 复制JSON文件
                            json_filename = os.path.basename(json_path)
                            output_json_path = os.path.join(output_dir, json_filename)
                            shutil.copy2(json_path, output_json_path)
                            
                            # 查找并复制对应的图片文件
                            image_path = self.find_image_file(json_path)
                            if image_path:
                                image_filename = os.path.basename(image_path)
                                output_image_path = os.path.join(output_dir, image_filename)
                                shutil.copy2(image_path, output_image_path)
                                self.exported_files.append((json_path, image_path))
                                self.log(f"导出: {json_filename} + {image_filename}")
                            else:
                                self.exported_files.append((json_path, None))
                                self.log(f"导出: {json_filename} (未找到对应图片)")
                            
                        except Exception as e:
                            self.log(f"导出文件失败 {json_path}: {e}")
                            self.error_files.append((json_path, f"导出失败: {e}"))
                
                # 更新进度
                self.processed_files += 1
                progress = self.processed_files / self.total_files
                self.update_progress(progress)
            
            elapsed_time = time.time() - start_time
            self.log(f"标签导出处理完成！耗时: {elapsed_time:.2f}秒")
            self.log(f"导出文件组: {len(self.exported_files)} 个")
            self.log(f"错误文件: {len(self.error_files)} 个")
            
            return True
            
        except Exception as e:
            self.log(f"标签导出处理过程中出现错误: {e}")
            return False
    
    def replace_labels(self, old_label: str, new_label: str) -> bool:
        """
        替换标签名称
        
        Args:
            old_label: 原标签名称
            new_label: 新标签名称
            
        Returns:
            处理是否成功
        """
        try:
            self.log("开始标签替换处理...")
            start_time = time.time()
            
            # 获取所有JSON文件
            json_files = self.get_json_files()
            self.total_files = len(json_files)
            
            if self.total_files == 0:
                self.log("未找到任何JSON文件")
                return False
            
            self.log(f"找到 {self.total_files} 个JSON文件")
            self.log(f"将标签 '{old_label}' 替换为 '{new_label}'")
            
            for i, json_path in enumerate(json_files):
                # 加载JSON文件
                data = self.load_json_file(json_path)
                if data is None:
                    continue
                
                # 检查是否有shapes字段
                if 'shapes' not in data:
                    continue
                
                # 查找并替换标签
                replaced_count = 0
                for shape in data['shapes']:
                    if shape.get('label', '') == old_label:
                        # 备份原文件（如果需要且是第一次修改）
                        if replaced_count == 0 and self.backup_enabled:
                            self.backup_file(json_path)
                        
                        shape['label'] = new_label
                        replaced_count += 1
                
                if replaced_count > 0:
                    # 保存修改后的JSON文件
                    if self.save_json_file(json_path, data):
                        self.modified_files.append(json_path)
                        self.log(f"修改文件: {os.path.basename(json_path)} (替换 {replaced_count} 个标签)")
                
                # 更新进度
                self.processed_files += 1
                progress = self.processed_files / self.total_files
                self.update_progress(progress)
            
            elapsed_time = time.time() - start_time
            self.log(f"标签替换处理完成！耗时: {elapsed_time:.2f}秒")
            self.log(f"修改文件: {len(self.modified_files)} 个")
            self.log(f"错误文件: {len(self.error_files)} 个")
            
            return True
            
        except Exception as e:
            self.log(f"标签替换处理过程中出现错误: {e}")
            return False
    
    def export_blank_images(self, output_dir: str) -> bool:
        """
        导出未标注或标注为空的图片
        
        Args:
            output_dir: 输出目录
            
        Returns:
            bool: 是否成功完成
        """
        try:
            self.log("开始导出空白图片...")
            start_time = time.time()
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 获取所有图片文件
            image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
            image_files = []
            
            if self.recursive:
                for root, _, files in os.walk(self.source_dir):
                    for file in files:
                        if file.lower().endswith(image_extensions):
                            image_files.append(os.path.join(root, file))
            else:
                for file in os.listdir(self.source_dir):
                    if file.lower().endswith(image_extensions):
                        image_files.append(os.path.join(self.source_dir, file))
            
            if not image_files:
                self.log("未找到任何图片文件")
                return False
            
            self.total_files = len(image_files)
            self.log(f"找到 {self.total_files} 个图片文件，开始检查...")
            
            # 初始化统计信息
            if not hasattr(self, 'stats'):
                self.stats = {}
            
            blank_images = []
            no_json_images = []
            empty_label_images = []
            
            processed_files = 0
            
            for image_path in image_files:
                # 检查是否有对应的JSON文件
                json_path = image_path.rsplit('.', 1)[0] + '.json'
                
                if not os.path.exists(json_path):
                    # 没有对应的JSON文件
                    no_json_images.append(image_path)
                    blank_images.append(image_path)
                else:
                    try:
                        # 读取JSON文件检查标签
                        json_data = self.load_json_file(json_path)
                        if not json_data or 'shapes' not in json_data or not json_data['shapes']:
                            # JSON文件存在但没有标签
                            empty_label_images.append(image_path)
                            blank_images.append(image_path)
                    except Exception as e:
                        self.log(f"读取JSON文件失败 {json_path}: {e}")
                        no_json_images.append(image_path)
                        blank_images.append(image_path)
                
                processed_files += 1
                progress = processed_files / self.total_files * 0.5  # 前50%用于检查
                self.update_progress(progress)
                
                # 检查是否需要停止
                if not self.is_running:
                    self.log("处理被用户中断")
                    return False
            
            # 复制空白图片到输出目录
            if blank_images:
                self.log(f"找到 {len(blank_images)} 个空白图片（无JSON: {len(no_json_images)}, 空标签: {len(empty_label_images)}）")
                self.log(f"开始复制到输出目录: {output_dir}")
                
                copied_count = 0
                for i, image_path in enumerate(blank_images):
                    try:
                        # 获取文件名
                        filename = os.path.basename(image_path)
                        output_path = os.path.join(output_dir, filename)
                        
                        # 复制文件
                        shutil.copy2(image_path, output_path)
                        copied_count += 1
                        self.exported_files.append(image_path)
                        
                        self.log(f"已复制: {filename}")
                    except Exception as e:
                        self.log(f"复制文件失败 {image_path}: {e}")
                        self.error_files.append((image_path, f"复制失败: {e}"))
                    
                    # 更新进度
                    progress = 0.5 + (i / len(blank_images)) * 0.5  # 后50%用于复制
                    self.update_progress(progress)
                    
                    # 检查是否需要停止
                    if not self.is_running:
                        self.log("复制过程被用户中断")
                        return False
                
                self.log(f"成功复制 {copied_count} 个空白图片")
            else:
                self.log("未找到空白图片")
            
            # 保存统计信息
            self.stats['blank_images_found'] = len(blank_images)
            self.stats['no_json_images'] = len(no_json_images)
            self.stats['empty_label_images'] = len(empty_label_images)
            self.stats['blank_images_exported'] = len(blank_images)
            
            elapsed_time = time.time() - start_time
            self.log(f"空白图片导出完成！耗时: {elapsed_time:.2f}秒")
            self.log(f"导出图片数量: {len(self.exported_files)} 个")
            self.log(f"错误文件: {len(self.error_files)} 个")
            
            return True
            
        except Exception as e:
            self.log(f"空白图片导出过程中出现错误: {e}")
            return False
    
    def generate_report(self) -> str:
        """
        生成处理报告
        
        Returns:
            格式化的报告字符串
        """
        report = []
        report.append("="*60)
        report.append("标签处理报告")
        report.append("="*60)
        report.append(f"源目录: {self.source_dir}")
        report.append(f"递归遍历: {'是' if self.recursive else '否'}")
        report.append(f"备份功能: {'启用' if self.backup_enabled else '关闭'}")
        if self.backup_enabled:
            report.append(f"备份目录: {self.backup_dir}")
        report.append("")
        
        report.append("处理统计:")
        report.append(f"  总文件数量: {self.total_files}")
        report.append(f"  处理文件数量: {self.processed_files}")
        report.append(f"  修改文件数量: {len(self.modified_files)}")
        report.append(f"  删除文件数量: {len(self.deleted_files)}")
        report.append(f"  导出文件数量: {len(self.exported_files)}")
        report.append(f"  错误文件数量: {len(self.error_files)}")
        
        # 添加空白图片导出统计信息
        if hasattr(self, 'stats') and 'blank_images_found' in self.stats:
            report.append("")
            report.append("空白图片导出统计:")
            report.append(f"  找到的空白图片数量: {self.stats['blank_images_found']}")
            report.append(f"    - 无JSON文件的图片: {self.stats['no_json_images']}")
            report.append(f"    - 空标签的图片: {self.stats['empty_label_images']}")
            report.append(f"  导出的空白图片数量: {self.stats['blank_images_exported']}")
        
        report.append("")
        
        if self.error_files:
            report.append("错误文件:")
            for file_path, error in self.error_files[:10]:  # 只显示前10个错误
                report.append(f"  {os.path.basename(file_path)}: {error}")
            if len(self.error_files) > 10:
                report.append(f"  ... 还有 {len(self.error_files) - 10} 个错误文件")
            report.append("")
        
        report.append("="*60)
        return "\n".join(report)

def test_label_processor():
    """测试标签处理功能"""
    print("标签处理模块测试")
    print("注意：这是一个演示测试，实际使用请通过UI界面操作")
    return True

def main():
    """主函数 - 用于单独测试模块功能"""
    print("=" * 50)
    print("标签处理模块测试")
    print("=" * 50)
    
    try:
        # 执行测试
        result = test_label_processor()
        
        if result:
            print("标签处理模块测试成功！")
            return True
        else:
            print("标签处理模块测试失败！")
            return False
            
    except Exception as e:
        print(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("测试成功！")
    else:
        print("测试失败！")
        exit(1)

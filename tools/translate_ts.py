import xml.etree.ElementTree as ET
import os
import sys
import subprocess

TRANSLATIONS = {
    "未安装TensorRT": "TensorRT not installed",
    "TensorRT版本：": "TensorRT Version:",
    "输入设置": "Input Settings",
    "ONNX路径：": "ONNX Path:",
    "选择文件": "Select File",
    "构建参数": "Build Parameters",
    "输出目录：": "Output Directory:",
    "选择目录": "Select Directory",
    "文件名称：": "Filename:",
    "例如: best.engine (不能包含中文)": "E.g., best.engine (No Chinese)",
    "图像大小：": "Image Size:",
    "最大内存(GB)：": "Max Memory (GB):",
    "最小内存(GB)：": "Min Memory (GB):",
    "开始构建": "Start Build",
    "构建日志": "Build Log",
    "选择ONNX模型": "Select ONNX Model",
    "选择输出目录": "Select Output Directory",
    "错误": "Error",
    "请选择有效的ONNX文件！": "Please select a valid ONNX file!",
    "请选择输出目录！": "Please select an output directory!",
    "请输入文件名称！": "Please enter a filename!",
    "文件名称不能包含中文！": "Filename cannot contain Chinese!",
    "构建中...": "Building...",
    "完成": "Done",
    "模型构建成功！": "Model build successful!",
    "构建成功！": "Build Successful!",
    "执行命令：": "Execute Command:",
    "失败": "Failed",
    "模型构建失败，请查看日志。": "Model build failed, check logs.",
    "标注数据文件夹：": "Label Data Folder:",
    "分类文本文件：": "Class Text File:",
    "划分数据集比例(训练集:验证集:测试集):": "Split Ratio (Train:Val:Test):",
    "数据集格式：": "Dataset Format:",
    "开始构建": "Start Build",
    "处理日志": "Process Log",
    "温馨提示：比例总和需要为10，否则无法开启一键训练,当前总和为": "Tip: Sum of ratios must be 10. Current sum:",
    "选择标注文件夹": "Select Label Folder",
    "选择 classes.txt": "Select classes.txt",
    "选择输出数据集路径": "Select Output Path",
    "警告！": "Warning!",
    "标注数据集文件夹路径不可为空！请检查后再执行操作。": "Label folder cannot be empty!",
    "类别文件路径不可为空！请检查后再执行操作。": "Class file cannot be empty!",
    "结果输出路径不可为空！请检查后再执行操作。": "Output path cannot be empty!",
    "构建中": "Building",
    "构建数据集": "Build Dataset",
    "选择": "Select",
    "加载配置": "Load Config",
    "保存配置": "Save Config",
    "导出配置": "Export Config",
    "选择配置": "Select Config",
    "字段": "Field",
    "无法解析为有效结构": "Invalid structure",
    "成功": "Success",
    "配置已保存": "Config Saved",
    "配置已导出": "Config Exported",
    "数据源设置": "Data Source Settings",
    "处理目录：": "Process Directory:",
    "递归处理子目录": "Recursive",
    "功能选择": "Functions",
    "删除标签": "Delete Labels",
    "导出标签": "Export Labels",
    "替换标签": "Replace Labels",
    "导出空白图": "Export Empty Imgs",
    "参数配置": "Parameters",
    "目标标签：": "Target Labels:",
    "多个标签请用逗号分隔": "Comma separated",
    "原标签名：": "Old Label:",
    "新标签名：": "New Label:",
    "备份原文件": "Backup Original",
    "备份目录：": "Backup Directory:",
    "开始处理": "Start Processing",
    "选择处理目录": "Select Process Dir",
    "选择备份目录": "Select Backup Dir",
    "请选择有效的处理目录！": "Invalid process directory!",
    "开启备份时必须选择备份目录！": "Backup directory required!",
    "请输入要删除的标签！": "Enter labels to delete!",
    "语言": "Language",
    "系统设置": "System Settings",
    "打开设置": "Open Settings",
    "切换用户": "Switch User",
    "管理员验证": "Admin Verification",
    "请输入管理员密码：": "Enter Admin Password:",
    "验证失败": "Verification Failed",
    "密码错误，请重试！": "Wrong password!",
    "清空日志": "Clear Log",
    "保存日志": "Save Log",
    "数据集文件夹：": "Dataset Folder:",
    "结果输出路径：": "Output Path:",
    "开始训练": "Start Training",
    "停止训练": "Stop Training",
    "训练中": "Training...",
    "正在停止训练...": "Stopping...",
    "持久化": "Persist",
    "构建失败，错误码：": "Build Failed, Error Code:",
    "数据集文件夹与模型导出路径均不可为空！请检查后再执行操作。": "Paths cannot be empty!",
    "请输入要导出的标签！": "Enter labels to export!",
    "请输入原标签名和新标签名！": "Enter old and new labels!",
    "操作已完成！": "Operation completed!",
    "操作失败：": "Operation failed: ",
    "提示": "Info",
    "选择文件夹": "Select Folder",
    "处理完成": "Process Completed",
    "处理失败或被中断": "Process Failed or Interrupted",
    "警告": "Warning",
    "一键训练": "One-Click Train",
    "训练配置": "Train Config",
    "标签处理": "Label Process",
    "模型转换": "Model Convert",
    "正在发送停止信号...": "Sending stop signal...",
    "当前没有正在运行的训练任务。": "No training task is currently running.",
    "数据集构建完成": "Dataset build completed",
    "警告": "Warning",
    "Conda 环境路径不能为空。请检查配置文件是否正确或联系管理员。": "Conda env path cannot be empty. Check config or contact admin.",
    "获取 Conda 环境路径失败。请检查配置文件是否正确或联系管理员。": "Failed to get Conda env path. Check config or contact admin.",
    "启动训练": "Starting training",
    "命令: ": "Command: ",
    "功能区": "Functions",
    "工具区": "Tools",
    "请输入要导出的标签！": "Enter labels to export!",
    "• 删除JSON文件中指定名称的标签\n• 如果删除后JSON文件没有其他标签，则删除整个JSON文件\n• 支持同时删除多个标签 (用逗号分隔)\n• 可选择是否备份原文件": "• Delete specified labels in JSON\n• Delete JSON if empty after deletion\n• Support multiple labels (comma separated)\n• Optional backup",
    "• 导出包含指定标签的JSON文件和对应图片\n• 将匹配的文件复制到指定的输出目录\n• 支持同时匹配多个标签 (用逗号分隔)\n• 自动查找同名的图片文件": "• Export JSON & images with specified labels\n• Copy matched files to output dir\n• Support multiple labels\n• Auto-find corresponding images",
    "• 将JSON文件中的指定标签名称替换为新名称\n• 精确匹配标签名称进行替换\n• 可选择是否备份原文件\n• 批量处理所有匹配的文件": "• Replace label names in JSON\n• Exact match replacement\n• Optional backup\n• Batch process all matched files",
    "• 导出没有JSON文件或JSON文件为空的图片\n• 将符合条件的图片复制到指定的输出目录\n• 支持常见图片格式 (jpg, png, bmp等)\n• 自动保持目录结构": "• Export images without JSON or empty JSON\n• Copy matched images to output dir\n• Support common image formats\n• Preserve directory structure",
    "训练结束": "Training Finished",
    "利用率": "UTE",
    "温度": "TEMP",
    "显存使用率": "VRAM USR",
    "平均温度": "Avg TEMP",
    "最大温度": "Max TEMP",
    "CPU负载": "CPU Load",
    "通用内存": "System Memory",
    "虚拟负载": "Vir Load",
    "使用量": "USED",
    "可用量": "AVAIL",
    "物理": "PM",
    "虚拟": "VM",
    "占用率": "USR",
    "处理中...": "Processing...",
    "oneST": "oneST",
    "构建数据": "Build Data",
    "是否持久化数据集": "Persist Dataset?",
    "已选择持久化数据集，输出数据集路径不可为空！请检查后再执行操作。": "Persist enabled, output path cannot be empty!",
    "选择数据集文件夹": "Select Dataset Folder",
    "选择模型导出路径": "Select Model Export Path",
    "GPU": "GPU"
}

def main():
    # Ensure we are in the project root
    if not os.path.exists("resources"):
        # Try to find the root
        if os.path.exists("../resources"):
            os.chdir("..")
            
    ts_file = "resources/translations/en.ts"
    qm_file = "resources/translations/en.qm"
    
    if not os.path.exists(ts_file):
        print(f"Error: {ts_file} not found.")
        return

    tree = ET.parse(ts_file)
    root = tree.getroot()
    
    count = 0
    for context in root.findall('context'):
        for message in context.findall('message'):
            source = message.find('source').text
            translation = message.find('translation')
            
            if source in TRANSLATIONS:
                translation.text = TRANSLATIONS[source]
                # Remove 'type="unfinished"' if it exists
                if 'type' in translation.attrib:
                    del translation.attrib['type']
                count += 1
            else:
                print(f"Missing translation for: {source}")

    tree.write(ts_file, encoding="utf-8", xml_declaration=True)
    print(f"Updated {count} translations in {ts_file}")
    
    # Run lrelease
    # Find lrelease
    python_dir = os.path.dirname(sys.executable)
    possible_paths = [
        os.path.join(python_dir, "Lib", "site-packages", "PySide6", "lrelease.exe"),
        os.path.join(python_dir, "Scripts", "pyside6-lrelease.exe"),
        os.path.join(python_dir, "bin", "pyside6-lrelease"),
        os.path.join(python_dir, "pyside6-lrelease")
    ]
    
    lrelease_cmd = "pyside6-lrelease"
    for p in possible_paths:
        if os.path.exists(p):
            lrelease_cmd = p
            break
            
    cmd = [lrelease_cmd, ts_file, "-qm", qm_file]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"Generated {qm_file}")

if __name__ == "__main__":
    main()

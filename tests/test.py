import time
import os
 
ts = time.strftime("%y-%m-%d_%H:%M", time.localtime())
print(ts)

import sys
if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS  # type: ignore[attr-defined] 打包后：临时解压目录
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 开发时：脚本所在目录
print(os.path.join(base_path, "test"))
"""
厨房安全检测系统 (Kitchen Safety Detection System)

基于计算机视觉和深度学习技术的智能安全监控系统，专门针对厨房环境设计。
系统通过实时视频分析，识别厨房中的安全风险，包括人员跌倒和灶台无人看管等危险情况。

主要功能:
- 实时视频采集和处理
- YOLO目标检测 (人员、灶台、火焰)
- MediaPipe姿态识别和跌倒检测
- 风险评估和报警管理
- Django Web后台管理
- 日志记录和查询系统
"""

__version__ = "1.0.0"
__author__ = "Kitchen Safety Team"
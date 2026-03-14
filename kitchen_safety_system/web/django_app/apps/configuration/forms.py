from django import forms
from .models import SystemConfiguration, DetectionThreshold, CameraConfiguration
import json


class SystemConfigurationForm(forms.ModelForm):
    """系统配置表单"""
    
    change_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': '修改原因（可选）...'
        }),
        label='修改原因'
    )
    
    class Meta:
        model = SystemConfiguration
        fields = ['value']
        widgets = {
            'value': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }
        labels = {
            'value': '配置值',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            # 根据配置类型调整输入控件
            if self.instance.config_type == 'boolean':
                self.fields['value'].widget = forms.Select(
                    choices=[('true', '是'), ('false', '否')],
                    attrs={'class': 'form-select'}
                )
            elif self.instance.config_type == 'integer':
                self.fields['value'].widget = forms.NumberInput(attrs={
                    'class': 'form-control',
                    'step': '1'
                })
            elif self.instance.config_type == 'float':
                self.fields['value'].widget = forms.NumberInput(attrs={
                    'class': 'form-control',
                    'step': '0.01'
                })
            elif self.instance.config_type == 'string':
                self.fields['value'].widget = forms.TextInput(attrs={
                    'class': 'form-control'
                })
            
            # 设置验证规则提示
            if self.instance.validation_rules:
                rules = self.instance.validation_rules
                help_text = []
                if 'min' in rules:
                    help_text.append(f"最小值: {rules['min']}")
                if 'max' in rules:
                    help_text.append(f"最大值: {rules['max']}")
                if help_text:
                    self.fields['value'].help_text = ', '.join(help_text)
    
    def clean_value(self):
        """验证配置值"""
        value = self.cleaned_data['value']
        
        if self.instance and self.instance.pk:
            is_valid, error_message = self.instance.validate_value(value)
            if not is_valid:
                raise forms.ValidationError(error_message)
        
        return value


class DetectionThresholdForm(forms.ModelForm):
    """检测阈值表单"""
    
    class Meta:
        model = DetectionThreshold
        fields = ['name', 'detection_type', 'confidence_threshold', 
                 'time_threshold_seconds', 'distance_threshold_meters',
                 'additional_params', 'is_enabled', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'detection_type': forms.TextInput(attrs={'class': 'form-control'}),
            'confidence_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '1'
            }),
            'time_threshold_seconds': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'distance_threshold_meters': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1'
            }),
            'additional_params': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '{"param1": "value1", "param2": "value2"}'
            }),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }
        labels = {
            'name': '阈值名称',
            'detection_type': '检测类型',
            'confidence_threshold': '置信度阈值',
            'time_threshold_seconds': '时间阈值(秒)',
            'distance_threshold_meters': '距离阈值(米)',
            'additional_params': '附加参数 (JSON)',
            'is_enabled': '启用状态',
            'description': '描述',
        }
    
    def clean_additional_params(self):
        """验证附加参数JSON格式"""
        params = self.cleaned_data['additional_params']
        if params:
            try:
                json.loads(params)
            except json.JSONDecodeError:
                raise forms.ValidationError('附加参数必须是有效的JSON格式')
        return params


class CameraConfigurationForm(forms.ModelForm):
    """摄像头配置表单"""
    
    class Meta:
        model = CameraConfiguration
        fields = ['camera_id', 'name', 'location', 'rtsp_url',
                 'resolution_width', 'resolution_height', 'fps',
                 'detection_zones', 'is_enabled', 'calibration_data']
        widgets = {
            'camera_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'rtsp_url': forms.URLInput(attrs={'class': 'form-control'}),
            'resolution_width': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '320'
            }),
            'resolution_height': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '240'
            }),
            'fps': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '60'
            }),
            'detection_zones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '[{"name": "zone1", "points": [[x1,y1], [x2,y2], ...]}]'
            }),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'calibration_data': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '{"scale_factor": 1.0, "offset_x": 0, "offset_y": 0}'
            }),
        }
        labels = {
            'camera_id': '摄像头ID',
            'name': '摄像头名称',
            'location': '安装位置',
            'rtsp_url': 'RTSP地址',
            'resolution_width': '分辨率宽度',
            'resolution_height': '分辨率高度',
            'fps': '帧率',
            'detection_zones': '检测区域 (JSON)',
            'is_enabled': '启用状态',
            'calibration_data': '标定数据 (JSON)',
        }
    
    def clean_detection_zones(self):
        """验证检测区域JSON格式"""
        zones = self.cleaned_data['detection_zones']
        if zones:
            try:
                json.loads(zones)
            except json.JSONDecodeError:
                raise forms.ValidationError('检测区域必须是有效的JSON格式')
        return zones
    
    def clean_calibration_data(self):
        """验证标定数据JSON格式"""
        data = self.cleaned_data['calibration_data']
        if data:
            try:
                json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError('标定数据必须是有效的JSON格式')
        return data


class ConfigurationImportForm(forms.Form):
    """配置导入表单"""
    
    config_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.json,.yaml,.yml'
        }),
        label='配置文件'
    )
    
    overwrite_existing = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='覆盖现有配置'
    )
    
    def clean_config_file(self):
        """验证配置文件"""
        file = self.cleaned_data['config_file']
        
        if file:
            # 检查文件大小
            if file.size > 1024 * 1024:  # 1MB
                raise forms.ValidationError('配置文件大小不能超过1MB')
            
            # 检查文件格式
            if not file.name.lower().endswith(('.json', '.yaml', '.yml')):
                raise forms.ValidationError('只支持JSON和YAML格式的配置文件')
        
        return file
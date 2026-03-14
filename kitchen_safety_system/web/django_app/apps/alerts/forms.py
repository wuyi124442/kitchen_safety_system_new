from django import forms
from .models import Alert, AlertRule


class AlertFilterForm(forms.Form):
    """报警筛选表单"""
    
    alert_type = forms.ChoiceField(
        choices=[('', '全部')] + Alert.ALERT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='报警类型'
    )
    
    severity = forms.ChoiceField(
        choices=[('', '全部')] + Alert.SEVERITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='严重程度'
    )
    
    status = forms.ChoiceField(
        choices=[('', '全部')] + Alert.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='状态'
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='开始日期'
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='结束日期'
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '搜索标题、描述或位置...'
        }),
        label='搜索'
    )


class AlertActionForm(forms.Form):
    """报警操作表单"""
    
    ACTION_CHOICES = [
        ('acknowledge', '确认'),
        ('resolve', '解决'),
        ('false_positive', '标记为误报'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='操作'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '备注信息（可选）...'
        }),
        label='备注'
    )


class AlertRuleForm(forms.ModelForm):
    """报警规则表单"""
    
    class Meta:
        model = AlertRule
        fields = ['name', 'alert_type', 'is_enabled', 'threshold_config', 
                 'notification_config', 'cooldown_seconds', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'alert_type': forms.Select(attrs={'class': 'form-select'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'threshold_config': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '{"confidence_threshold": 0.8, "duration_seconds": 30}'
            }),
            'notification_config': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '{"email": true, "sms": false, "webhook": false}'
            }),
            'cooldown_seconds': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }
        labels = {
            'name': '规则名称',
            'alert_type': '报警类型',
            'is_enabled': '启用状态',
            'threshold_config': '阈值配置 (JSON)',
            'notification_config': '通知配置 (JSON)',
            'cooldown_seconds': '冷却时间(秒)',
            'description': '描述',
        }
    
    def clean_threshold_config(self):
        """验证阈值配置JSON格式"""
        import json
        config = self.cleaned_data['threshold_config']
        try:
            json.loads(config)
            return config
        except json.JSONDecodeError:
            raise forms.ValidationError('阈值配置必须是有效的JSON格式')
    
    def clean_notification_config(self):
        """验证通知配置JSON格式"""
        import json
        config = self.cleaned_data['notification_config']
        try:
            json.loads(config)
            return config
        except json.JSONDecodeError:
            raise forms.ValidationError('通知配置必须是有效的JSON格式')
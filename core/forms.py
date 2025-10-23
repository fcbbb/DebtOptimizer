from django import forms

class ExcelImportForm(forms.Form):
    file = forms.FileField(label='Excel文件', help_text='请上传.xlsx或.xls格式的Excel文件')

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if not (file.name.endswith('.xlsx') or file.name.endswith('.xls')):
                raise forms.ValidationError('请上传Excel格式的文件 (.xlsx 或 .xls)')
        return file
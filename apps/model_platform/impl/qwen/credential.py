
from model_platform.spi import BaseCredential


class QwenCredential(BaseCredential):
    field_schema = [
        {"key":"api_base", "label":"API Base","type":"text","required":True,"default":"https://dashscope.aliyuncs.com/compatible-mode/v1"},
        {"key":"api_key","label":"API Key","type":"password","required":True},
    ]

    def is_valid(self, credential,model_type,model_name):
        if not credential.get("api_key"): return False
        try:
            QwenCredential(model_name,credential).invoke([{"role":"user","content":"hi"}],max_tokens=1)
            return True
        except Exception as e:
            return False
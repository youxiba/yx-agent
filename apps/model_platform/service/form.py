from model_platform.infra.cipher import CredentialCipher
from model_platform.models import ModelType
from model_platform.registry import PROVIDERS


def get_credential_form(provider: str,model_type:str, model_name:str) -> list[dict]:
    p = PROVIDERS[provider]
    info = next(i for i in p.get_model_list(ModelType(model_type)) if i.name == model_name)
    return info.credential_cls.field_schema

def get_model_params_form(provider:str,model_type:str,model_name:str) -> list[dict]:
    """通用参数表单:temperature/max_tokens，后续厂商可覆写"""
    return [
        {"key":"temperature","label":"Temperature","type":"slider","min":0,"max":2,"step":0.1,"default":0.7},
        {"key":"max_tokens","label":"Max_Tokens","type":"number","min":1,"max":32768,"default":4096}
    ]

def mask_credential(cred: dict) -> dict:
    return {k: (CredentialCipher.mask(str(v)) if "key" in k.lower() or "secret" in k.lower() else v) for k, v in cred.items()}

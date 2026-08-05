import json
import urllib

from model_platform.spi import MaxKBBaseModel


class OllamaChatModel(MaxKBBaseModel):
    def __init__(self, model_name,credential, **kw):
        self.model_name = model_name
        self.base = credential.get("api_base") or "http://127.0.0.1:11434"

    def stream(self, messages, **kw):
        req = urllib.request.Request(
            f"{self.base}/api/chat",
            data=json.dumps({"model":self.model_name, "messages":messages,"stream":True}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            for line in resp:
                obj = json.loads(line)
                yield {"content":obj.get("message",{}).get("content",""),
                       "reasoning_content":""}

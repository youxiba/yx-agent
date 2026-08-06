# coding=utf-8
"""工具服务：入参校验、执行记录写入"""
import jsonschema
from common.exceptions import AppApiException
from .models import ToolRecord


def validate_inputs(input_schema: dict, inputs: dict) -> None:
    """按 input_schema 对运行时入参做 JSON Schema 校验（驱动前端表单的同一份契约）"""
    if not input_schema:
        return
    try:
        jsonschema.Draft7Validator(input_schema).validate(inputs)
    except jsonschema.ValidationError as e:
        raise AppApiException(f"入参校验失败: {e.message}", code=400)


def record_execution(tool, result: dict, *, inputs: dict, chat_id=None) -> ToolRecord:
    """把一次执行写入 ToolRecord（审计），result 来自 ToolExecutor.exec_code"""
    return ToolRecord.objects.create(
        tool=tool,
        chat_id=chat_id,
        inputs=inputs,
        output=result.get("output"),
        stdout=result.get("stdout", ""),
        stderr=result.get("stderr", ""),
        status=result.get("status", "FAILURE"),
        run_time_ms=result.get("run_time_ms", 0),
    )
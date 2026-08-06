# apps/tool/infra/static_check.py
# coding=utf-8
"""pylint 静态检查：保存/发布/调试前对工具源码做错误级检查（E/F 两档封顶）"""
import io
import json
import os
import tempfile
from pylint.lint import Run
from pylint.reporters import JSONReporter


def static_check(code: str) -> dict:
    """返回 {ok, fatal, errors, messages}；ok=False 表示存在错误/致命问题"""
    if not code.strip():
        return {"ok": True, "fatal": 0, "errors": 0, "messages": []}
    fd, path = tempfile.mkstemp(suffix=".py", prefix="maxkb_tool_")
    # 真实空 rcfile（pylint 4.x 已不认 __NONE__ 哨兵，会报"config file doesn't exist"）
    rc_fd, rc_path = tempfile.mkstemp(suffix=".pylintrc")
    os.close(rc_fd)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        buf = io.StringIO()
        # -E = 只报告 error 与 fatal；rcfile 指向空配置避免读本机用户配置
        Run([path, "-E", "--persistent=n", "--reports=n", "--score=n", f"--rcfile={rc_path}"],
            reporter=JSONReporter(buf), exit=False)
        items = json.loads(buf.getvalue() or "[]")
    finally:
        os.unlink(path)
        os.unlink(rc_path)
    fatal = [i for i in items if i["type"] == "fatal"]
    errors = [i for i in items if i["type"] == "error"]
    return {
        "ok": not fatal and not errors,
        "fatal": len(fatal), "errors": len(errors),
        "messages": [{"type": i["type"], "message": i["message"], "line": i["line"]} for i in items],
    }
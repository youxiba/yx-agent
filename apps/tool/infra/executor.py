# apps/tool/infra/executor.py
# coding=utf-8
"""ToolExecutor：静态黑名单 + 子进程隔离 + 资源限制 + 网络白名单 + 超时。

安全模型（三层）：
  1) _precheck   —— 黑名单关键字 + compile() 语法预检（可被字符串拼接绕过，仅第一道）；
  2) 子进程守卫   —— 注入 socket 白名单补丁 + RLIMIT 资源限制 + psutil 内存看门狗；
  3) 生产加固    —— Linux 部署叠加 LD_PRELOAD 的 sandbox.so（见 Day 4）。
"""
import os
import subprocess
import sys
import tempfile
import threading
import time
import json
from dataclasses import asdict
from .sandbox import SandboxConfig

# 第一道静态防线：黑名单关键字（覆盖 文件/网络/进程/反射 四类敏感面）
BANNED_KEYWORDS = [
    "__import__", "eval(", "exec(", "compile(", "open(", "os.", "subprocess",
    "socket", "ctypes", "importlib", "__builtins__", "sys.modules", "globals()",
    "pickle", "marshal", "base64", "requests", "urllib", "http.client",
    "shutil", "pathlib", "tempfile", "functools.reduce.__getattr__", "getattr(",
]


class SandboxRejected(Exception):
    """黑名单/守卫拦截，携带拒绝原因"""


class ToolExecutor:
    def __init__(self, config: SandboxConfig | None = None):
        self.sandbox = config or SandboxConfig()

    def exec_code(self, code: str, inputs: dict, timeout: int | None = None) -> dict:
        """执行工具源码，恒返回 dict：{ok, status, stdout, stderr, output, run_time_ms}"""
        t0 = time.monotonic()
        timeout = timeout or self.sandbox.timeout
        try:
            self._precheck(code)
        except SandboxRejected as e:
            return self._reject(str(e), t0)
        script = self._build_script(code, inputs)
        with tempfile.TemporaryDirectory(prefix="maxkb-sandbox-") as tmp:
            env = dict(os.environ)
            env["PYTHONUSERBASE"] = ""                    # 不加载用户 site-packages
            env["PYTHONPATH"] = ""                        # 不继承宿主包路径
            env["MAXKB_SANDBOX_TMP"] = tmp
            stop = self._start_watchdog(timeout)          # 内存/时间看门狗（跨平台）
            try:
                p = subprocess.Popen(
                    [sys.executable, "-c", script],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL, env=env, cwd=tmp,
                    preexec_fn=self._posix_limits,        # Windows 上为 None（见陷阱）
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
                )
                try:
                    out, err = p.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    self._kill(p)
                    return {"ok": False, "status": "TIMEOUT", "stdout": "", "stderr": "执行超时",
                            "output": None, "run_time_ms": int((time.monotonic() - t0) * 1000)}
            finally:
                stop.set()
            stdout = out.decode("utf-8", "replace")[: self.sandbox.max_output]
            stderr = err.decode("utf-8", "replace")[: self.sandbox.max_output]
            ok = p.returncode == 0
            return {"ok": ok,
                    "status": "SUCCESS" if ok else "FAILURE",
                    "stdout": stdout, "stderr": stderr,
                    "output": self._parse_output(stdout),
                    "run_time_ms": int((time.monotonic() - t0) * 1000)}

    # ---------- 第一道：静态黑名单 + 语法预检 ----------
    def _precheck(self, code: str) -> None:
        for b in BANNED_KEYWORDS:
            if b in code:
                raise SandboxRejected(f"命中禁用关键字: {b}")
        try:
            compile(code, "<sandbox>", "exec")            # 语法预检
        except SyntaxError as e:
            raise SandboxRejected(f"语法错误: {e}")

    # ---------- 第二道：守卫代码注入 + 入参隔离 ----------
    def _build_script(self, code: str, inputs: dict) -> str:
        allow = list(self.sandbox.net_allow_hosts)
        payload = json.dumps(inputs, ensure_ascii=False)
        return f"""# coding=utf-8
import socket as _sock
_ORIG_CONNECT = _sock.socket.connect
_ALLOW = {allow!r}
def _connect(self, address):
    host = address[0] if isinstance(address, tuple) else address
    if not _ALLOW or host not in _ALLOW:
        raise OSError("net blocked: " + str(host))
    return _ORIG_CONNECT(self, address)
_sock.socket.connect = _connect
_sock.socket.connect_ex = lambda self, *a: (_connect(self, *a) or 0)
import json as _json
_inputs = _json.loads({payload!r})
__result__ = {{}}
def _maxkb_returns(**kw):
    __result__.update(kw)
{code}
print("__MAXKB_RESULT__:" + _json.dumps(__result__, ensure_ascii=False, default=str))
"""

    def _parse_output(self, stdout: str):
        for line in reversed(stdout.splitlines()):
            if line.startswith("__MAXKB_RESULT__:"):
                try:
                    return json.loads(line.split(":", 1)[1])
                except json.JSONDecodeError:
                    return None
        return None

    # ---------- POSIX 资源限制（Windows 走看门狗） ----------
    def _posix_limits(self):
        if os.name != "posix":
            return
        import resource
        mb = self.sandbox.mem_limit_mb << 20
        resource.setrlimit(resource.RLIMIT_AS, (mb, mb))                       # 内存
        resource.setrlimit(resource.RLIMIT_CPU,
                           (int(self.sandbox.cpu_limit), int(self.sandbox.cpu_limit) + 1))  # CPU
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))                   # 文件句柄
        resource.setrlimit(resource.RLIMIT_NPROC,
                           (self.sandbox.max_children, self.sandbox.max_children))          # 防 fork
        os.setsid()

    # ---------- 内存/时间看门狗（跨平台，Windows 主用） ----------
    def _start_watchdog(self, timeout: int) -> threading.Event:
        stop = threading.Event()
        pid = None
        lock = threading.Lock()
        real = {"pid": None}

        def watcher():
            import psutil
            deadline = time.monotonic() + timeout
            while not stop.wait(0.2):
                with lock:
                    pid = real["pid"]
                if pid is None:
                    continue
                if time.monotonic() > deadline:
                    self._kill_pid(pid); return
                try:
                    if psutil.Process(pid).memory_info().rss > self.sandbox.mem_limit_mb << 20:
                        self._kill_pid(pid); return
                except psutil.NoSuchProcess:
                    return

        def register(pid):
            with lock:
                real["pid"] = pid

        t = threading.Thread(target=watcher, daemon=True)
        t.start()
        stop.register = register                     # 简化注入：subprocess 前记录 pid
        return stop

    def _kill(self, p):
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
        else:
            try:
                os.killpg(p.pid, 9)
            except ProcessLookupError:
                p.kill()

    def _kill_pid(self, pid):
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
        else:
            try:
                os.killpg(pid, 9)
            except (ProcessLookupError, PermissionError):
                pass

    def _reject(self, reason: str, t0: float) -> dict:
        return {"ok": False, "status": "REJECTED", "stdout": "", "stderr": reason,
                "output": None, "run_time_ms": int((time.monotonic() - t0) * 1000)}
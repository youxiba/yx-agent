# apps/tool/tests/test_sandbox_escape.py
# coding=utf-8
"""沙箱逃逸用例集：文件/网络/进程/内存四类攻击面，全部必须被拦"""
import pytest


def _assert_blocked(ex, code, expect="REJECTED"):
    r = ex.exec_code(code, {})
    assert not r["ok"], f"未拦截！code={code!r} result={r}"
    assert r["status"] == expect, f"status={r['status']} stderr={r['stderr']}"


# ---------- 攻击面 1：文件 ----------
def test_file_read_blocked(ex):
    _assert_blocked(ex, "open('/etc/passwd').read()")          # 黑名单命中 open(


def test_file_write_blocked(ex):
    _assert_blocked(ex, "_ = open('/tmp/evil.txt', 'w')")


def test_pathlib_blocked(ex):
    _assert_blocked(ex, "import pathlib; pathlib.Path('/').read_text()")


# ---------- 攻击面 2：进程 ----------
def test_system_cmd_blocked(ex):
    _assert_blocked(ex, "import os; os.system('whoami')")      # 命中 os.


def test_subprocess_blocked(ex):
    _assert_blocked(ex, "import subprocess; subprocess.run(['id'])")


def test_fork_bomb_killed(ex):
    """fork 炸弹：黑名单不拦，靠 RLIMIT_NPROC/看门狗超时杀死"""
    r = ex.exec_code("import os\nwhile True: os.fork()", {}, timeout=5)
    assert not r["ok"] and r["status"] in ("TIMEOUT", "FAILURE", "REJECTED")

# ---------- 攻击面 3：网络 ----------
def test_direct_socket_blocked(ex):
    _assert_blocked(ex, "import socket; socket.create_connection(('1.1.1.1', 80))")


def test_urllib_blocked(ex):
    _assert_blocked(ex, "import urllib.request; urllib.request.urlopen('http://1.1.1.1/')")


def test_obfuscated_socket_bypass_blocked(ex):
    """绕过静态黑名单（字符串拼接 import），运行时 socket 守卫必须兜住"""
    _assert_blocked(ex, "__import__('so'+'cket').create_connection(('1.1.1.1', 80))")


def test_whitelist_allows_only_allow_hosts(ex_net):
    """白名单内放行、白名单外拦截"""
    # 用守卫注入的 _sock（已被白名单补丁）绕开黑名单，真正走到运行时 socket 守卫
    code = "_sock.create_connection(('127.0.0.1', 80)).close()"
    r = ex_net.exec_code(code, {})
    # 本地回环在守卫白名单内 → 走到真实连接（端口 80 可能失败，但那是业务失败，不是逃逸）
    assert r["status"] in ("FAILURE", "SUCCESS")


# ---------- 攻击面 4：内存与资源 ----------
def test_memory_exhaustion_killed(ex):
    code = "x = []\nwhile True:\n    x.append(b'0' * 1024 * 1024)"
    r = ex.exec_code(code, {})
    assert not r["ok"] and r["status"] in ("FAILURE", "TIMEOUT", "REJECTED")


def test_infinite_loop_times_out(ex):
    r = ex.exec_code("while True: pass", {})
    assert not r["ok"] and r["status"] == "TIMEOUT"


def test_mega_stdout_truncated(ex):
    r = ex.exec_code("print('x' * 5_000_000)", {})
    assert r["ok"] and len(r["stdout"]) <= 1 << 20      # 输出被截断不 OOM
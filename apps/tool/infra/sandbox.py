# apps/tool/infra/sandbox.py
# coding=utf-8
"""沙箱配置：资源上限与网络白名单"""
from dataclasses import dataclass, field


@dataclass
class SandboxConfig:
    mem_limit_mb: int = 256                # 子进程 RSS 上限（MB）
    cpu_limit: float = 5.0                 # CPU 秒数上限（RLIMIT_CPU）
    timeout: int = 30                      # 墙钟超时（秒）
    net_allow_hosts: tuple[str, ...] = field(default_factory=tuple)   # 网络白名单，空 = 禁联网
    max_output: int = 1 << 20              # stdout/stderr 各上限 1MB
    max_children: int = 8                  # 最大子进程数（RLIMIT_NPROC，防 fork 炸弹）
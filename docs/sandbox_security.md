# 沙箱安全基线（Phase 6）

## 已落地防线
1. 静态黑名单（BANNED_KEYWORDS，四类攻击面全覆盖）
2. compile() 语法预检
3. 子进程隔离（独立临时目录 cwd、PYTHONPATH/PYTHONUSERBASE 清空）
4. POSIX RLIMIT（AS/CPU/NOFILE/NPROC）+ psutil 内存看门狗（跨平台）
5. socket 运行时守卫 + 网络白名单（默认全禁）
6. 墙钟超时 + 进程树强杀（POSIX killpg / Windows taskkill /T）
7. 输出截断（1MB）防管道 OOM

## 生产加固（Linux 部署必做）
- 编译 installer/sandbox.c -> sandbox.so，子进程 preload：在 libc 层封
  connect(2)/open(2)/fork/execve 等，双保险兜住 Python 层绕过。
- 运行账号降权：子进程以无权限低 UID（nobody）运行，禁写除临时目录外路径。
- seccomp 白名单（Docker 可选）：默认拒绝 execve/open 系统调用。

## 已知残余风险
- DNS 解析泄漏（gethostbyname）；内存计数 race（RSS 瞬时超限可能晚一拍被杀）
- 白名单匹配仅 host 精确串，不支持 CIDR（后续扩展）
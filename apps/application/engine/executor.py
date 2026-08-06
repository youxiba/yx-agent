import asyncio
import threading

# 进程级共享事件循环：Django 同步线程里 async 节点的桥接器
_loop = asyncio.new_event_loop()
_loop_thread = threading.Thread(target=_loop.run_forever, daemon=True)
_loop_thread.start()


def _run_one(self, node, ctx, emitter):
    result = node.execute(ctx)                       # sync 节点直接出结果
    if asyncio.iscoroutine(result):                  # async 节点（mcp-node）桥接到事件循环
        result = asyncio.run_coroutine_threadsafe(result, _loop).result(timeout=120)
    if result is None:
        return NodeResult()
    return result
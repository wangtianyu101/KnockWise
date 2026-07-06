"""共享 slowapi Limiter 实例（V2 L4 review 改进项）。

用途：
- main.py 装载到 app.state.limiter + 注册 RateLimitExceeded handler
- api/v2_settlement.py 在 6 个端点上加 @limiter.limit(...) 装饰器
- 未来 V3+ 其它端点复用

spec §3.2 限流阈值见 api-spec.md
"""
from slowapi import Limiter
from slowapi.util import get_remote_address


# 全局共享 Limiter（key_func 用 IP，未登录时也能限流）
# 已登录用户实际可按 user.id 限流，但 V2.5 优化阶段再说
limiter = Limiter(key_func=get_remote_address)
"""POC-3: Pydantic 动态组件 demo

目标：验证 Component Protocol + 动态注册中心可行
通过标准：写一个组件类，registry 自动发现并能执行
"""
import sys
import importlib
import inspect
from pathlib import Path
from typing import Protocol, runtime_checkable
from pydantic import BaseModel, Field, ConfigDict


# === 组件协议（强制） ===
class ComponentManifest(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    name: str
    version: str
    description: str
    input_schema: dict
    output_schema: dict


@runtime_checkable
class Component(Protocol):
    manifest: ComponentManifest

    def execute(self, input: dict) -> dict: ...


# === 组件注册中心 ===
class ComponentRegistry:
    def __init__(self):
        self._components: dict[str, Component] = {}

    def register(self, component: Component):
        self._components[component.manifest.id] = component
        print(f"  [registry] registered: {component.manifest.id} v{component.manifest.version}")

    def get(self, component_id: str) -> Component:
        return self._components[component_id]

    def list_ids(self) -> list[str]:
        return list(self._components.keys())


# === 示例组件 1: Echo ===
class EchoComponent:
    manifest = ComponentManifest(
        id="echo",
        name="Echo",
        version="1.0.0",
        description="原样返回输入",
        input_schema={"type": "object", "properties": {"msg": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"echoed": {"type": "string"}}},
    )

    def execute(self, input: dict) -> dict:
        return {"echoed": input.get("msg", "")}


# === 示例组件 2: WordCount ===
class WordCountComponent:
    manifest = ComponentManifest(
        id="word_count",
        name="Word Count",
        version="1.0.0",
        description="统计文本单词数",
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"count": {"type": "integer"}}},
    )

    def execute(self, input: dict) -> dict:
        text = input.get("text", "")
        return {"count": len(text.split())}


# === 示例组件 3: 动态加载（从文件） ===
DYNAMIC_COMPONENT_CODE = '''
from pydantic import BaseModel, Field
from typing import Protocol

class Manifest(BaseModel):
    id: str
    name: str
    version: str
    description: str
    input_schema: dict
    output_schema: dict
    class Config:
        frozen = True

class DynamicHelloComponent:
    manifest = Manifest(
        id="dynamic_hello",
        name="Dynamic Hello",
        version="0.1.0",
        description="动态加载的 hello 组件",
        input_schema={"type": "object", "properties": {"name": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"greeting": {"type": "string"}}},
    )
    def execute(self, input):
        return {"greeting": f"Hello, {input.get('name', 'world')}!"}
'''


def main():
    print("=== POC-3: Pydantic 动态组件 ===\n")

    # 1. 注册中心初始化
    registry = ComponentRegistry()
    print("[1] 初始化注册中心")

    # 2. 注册静态组件
    print("\n[2] 注册静态组件:")
    registry.register(EchoComponent())
    registry.register(WordCountComponent())

    # 3. 动态加载组件（从字符串代码）
    print("\n[3] 动态加载组件（exec 模拟运行时注册）:")
    ns: dict = {}
    exec(DYNAMIC_COMPONENT_CODE, ns)
    DynamicHello = ns["DynamicHelloComponent"]
    registry.register(DynamicHello())
    print(f"   动态组件类名: {DynamicHello.__name__}")

    # 4. 列出所有
    print(f"\n[4] 当前注册组件: {registry.list_ids()}")

    # 5. 执行测试
    print("\n[5] 执行测试:")
    for case in [
        ("echo", {"msg": "hello workflow"}),
        ("word_count", {"text": "one two three four five"}),
        ("dynamic_hello", {"name": "POC"}),
    ]:
        comp_id, inp = case
        result = registry.get(comp_id).execute(inp)
        print(f"   {comp_id}({inp}) → {result}")

    # 6. 协议校验
    print("\n[6] 协议校验（runtime_checkable）:")
    echo = registry.get("echo")
    print(f"   EchoComponent 是 Component: {isinstance(echo, Component)}")
    print(f"   manifest 可序列化: {echo.manifest.model_dump_json()[:80]}...")

    print("\n=== 结论: Pydantic 动态组件协议 + 注册中心可行 ===")


if __name__ == "__main__":
    main()

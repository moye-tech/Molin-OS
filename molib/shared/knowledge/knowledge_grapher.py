"""
知识图谱引擎 — 从 Lum1104/Understand-Anything (12.3K⭐) 汲取的混合分析管线

核心思想:
  - 混合分析管线: 确定性静态分析(文件解析) → LLM增强(语义提取) → 标准化输出
  - 21种节点类型/35种边类型: 统一的知识图谱数据模型
  - 标准化管线: Zod校验 + 别名映射 + ID修复 + 边去重
  - 两阶段布局: ELK(复杂图) → dagre(小图) → d3-force(知识图谱)
  - 陈旧检测: git commit hash + 文件指纹比对

适用场景:
  - 代码仓库→知识图谱(项目架构可视化)
  - 知识库→概念图谱(LLM Wiki/文档)
  - 子公司能力→能力图谱(CEO决策引擎的ROI分析)
  - 领域知识→推理图谱(研究分析)
"""

import json
import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ─── 类型定义 ────────────────────────────────────────────────────────────

# 4大类节点类型
NODE_TYPE_CODE = ("file", "function", "class", "module", "concept")
NODE_TYPE_INFRA = ("config", "document", "service", "table", "endpoint", "pipeline", "schema", "resource")
NODE_TYPE_DOMAIN = ("domain", "flow", "step")
NODE_TYPE_KNOWLEDGE = ("article", "entity", "topic", "claim", "source")

ALL_NODE_TYPES = NODE_TYPE_CODE + NODE_TYPE_INFRA + NODE_TYPE_DOMAIN + NODE_TYPE_KNOWLEDGE

# 8大类边类型
EDGE_CATEGORIES = (
    "structural", "behavioral", "data_flow", "dependencies",
    "semantic", "infrastructure", "domain", "knowledge"
)


@dataclass
class GraphNode:
    """图节点 — 21种子类型"""
    id: str  # type:name 格式，如 "function:mainHandler"、"file:src/app.py"
    label: str
    node_type: str  # 从 ALL_NODE_TYPES 中选择
    properties: dict = field(default_factory=dict)
    complexity: str = "medium"  # simple | medium | complex
    weight: float = 1.0


@dataclass
class GraphEdge:
    """图边 — 35种子类型"""
    source_id: str
    target_id: str
    edge_type: str  # 如 contains, imports, calls, inherits, related
    edge_category: str = "structural"  # 从 EDGE_CATEGORIES 中选择
    weight: float = 1.0
    properties: dict = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    """知识图谱 — 完整的图数据结构"""
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_node(self, node: GraphNode):
        """添加节点（幂等）"""
        if not any(n.id == node.id for n in self.nodes):
            self.nodes.append(node)

    def add_edge(self, edge: GraphEdge):
        """添加边（去重）"""
        existing = any(
            e.source_id == edge.source_id
            and e.target_id == edge.target_id
            and e.edge_type == edge.edge_type
            for e in self.edges
        )
        if not existing:
            self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """按ID查找节点"""
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "nodes": [
                {"id": n.id, "label": n.label, "type": n.node_type,
                 "properties": n.properties, "complexity": n.complexity}
                for n in self.nodes
            ],
            "edges": [
                {"source": e.source_id, "target": e.target_id,
                 "type": e.edge_type, "category": e.edge_category}
                for e in self.edges
            ],
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeGraph":
        """从字典反序列化"""
        kg = cls(metadata=data.get("metadata", {}))
        for n in data.get("nodes", []):
            kg.nodes.append(GraphNode(
                id=n["id"], label=n["label"], node_type=n["type"],
                properties=n.get("properties", {}),
                complexity=n.get("complexity", "medium")
            ))
        for e in data.get("edges", []):
            kg.edges.append(GraphEdge(
                source_id=e["source"], target_id=e["target"],
                edge_type=e["type"], edge_category=e.get("category", "structural")
            ))
        return kg


# ─── 文件分析器 ─────────────────────────────────────────────────────

class FileAnalyzer:
    """文件级静态分析 — Tree-sitter风格的导入/依赖提取"""

    # 导入正则模式
    IMPORT_PATTERNS = {
        "python": [
            r'^import\s+(\S+)',
            r'^from\s+(\S+)\s+import',
        ],
        "typescript": [
            r"^import\s+.*\s+from\s+['\"](.+?)['\"]",
            r"^import\s+['\"](.+?)['\"]",
            r"^require\s*\(\s*['\"](.+?)['\"]\s*\)",
        ],
        "javascript": [
            r"^import\s+.*\s+from\s+['\"](.+?)['\"]",
            r"^import\s+['\"](.+?)['\"]",
            r"^require\s*\(\s*['\"](.+?)['\"]\s*\)",
            r"^const\s+.*=\s*require\s*\(\s*['\"](.+?)['\"]\s*\)",
        ],
        "go": [
            r'^import\s+"(.+?)"',
            r'^import\s+\([^)]*"(.+?)"',
        ],
        "rust": [
            r'^use\s+(\S+)',
            r'^use\s+\S+\s+as\s+\S+',
            r'^extern\s+crate\s+(\S+)',
        ],
        "java": [
            r'^import\s+(.+?);',
        ],
    }

    @classmethod
    def detect_language(cls, filename: str) -> Optional[str]:
        """检测文件语言"""
        ext_map = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".jsx": "javascript", ".tsx": "typescript", ".go": "go",
            ".rs": "rust", ".java": "java", ".rb": "ruby",
            ".php": "php", ".swift": "swift", ".kt": "kotlin",
        }
        ext = filename[filename.rfind("."):] if "." in filename else ""
        return ext_map.get(ext)

    @classmethod
    def extract_imports(cls, content: str, language: str) -> list[str]:
        """提取导入依赖"""
        imports = []
        patterns = cls.IMPORT_PATTERNS.get(language, [])
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for m in matches:
                # 提取主包名
                if isinstance(m, str):
                    parts = m.split(".")[0].split("/")[0]
                    if parts and parts not in imports and not parts.startswith("."):
                        imports.append(parts)
                elif isinstance(m, tuple):
                    for part in m:
                        if isinstance(part, str):
                            parts = part.split(".")[0].split("/")[0]
                            if parts and parts not in imports and not parts.startswith("."):
                                imports.append(parts)
        return imports

    @classmethod
    def extract_functions(cls, content: str, language: str) -> list[dict]:
        """提取函数/方法定义"""
        functions = []
        if language == "python":
            for match in re.finditer(
                    r'^(?:async\s+)?def\s+(\w+)\s*\(', content, re.MULTILINE):
                functions.append({
                    "name": match.group(1),
                    "line": content[:match.start()].count("\n") + 1
                })
            for match in re.finditer(
                    r'^class\s+(\w+)', content, re.MULTILINE):
                functions.append({
                    "name": match.group(1),
                    "type": "class",
                    "line": content[:match.start()].count("\n") + 1
                })
        elif language in ("typescript", "javascript"):
            for match in re.finditer(
                    r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', content):
                functions.append({
                    "name": match.group(1),
                    "line": content[:match.start()].count("\n") + 1
                })
            for match in re.finditer(
                    r'(?:export\s+)?class\s+(\w+)', content):
                functions.append({
                    "name": match.group(1),
                    "type": "class",
                    "line": content[:match.start()].count("\n") + 1
                })
        return functions

    @classmethod
    def analyze_file(cls, filename: str, content: str) -> list[GraphNode]:
        """分析单个文件，返回节点列表"""
        nodes = []
        language = cls.detect_language(filename)
        if not language:
            return nodes

        # 文件节点
        file_node = GraphNode(
            id=f"file:{filename}",
            label=filename.split("/")[-1],
            node_type="file",
            properties={"path": filename, "language": language}
        )
        nodes.append(file_node)

        # 函数/类节点
        funcs = cls.extract_functions(content, language)
        for func in funcs:
            node_type = func.get("type", "function")
            f_node = GraphNode(
                id=f"{node_type}:{filename}:{func['name']}",
                label=func["name"],
                node_type=node_type,
                properties={"file": filename, "line": func.get("line", 0)}
            )
            nodes.append(f_node)

        return nodes


# ─── 图标准化器 ──────────────────────────────────────────────────────

class GraphNormalizer:
    """图标准化 — 从Understand-Anything normalize-graph汲取

    处理LLM输出不一致:
    - ID格式修复 (func:foo → function:foo)
    - 别名映射 (fn:bar → function:bar)
    - 复杂度归一化 ("low"/"trivial" → "simple")
    - 孤边检测与移除
    - 边去重
    """

    TYPE_ALIASES = {
        "func": "function", "fn": "function",
        "cls": "class", "obj": "class",
        "mod": "module", "lib": "module",
        "doc": "document", "pkg": "package",
    }

    COMPLEXITY_MAP = {
        "low": "simple", "trivial": "simple", "easy": "simple",
        "medium": "medium", "moderate": "medium",
        "high": "complex", "hard": "complex", "advanced": "complex",
    }

    @classmethod
    def normalize_node_id(cls, node_id: str) -> str:
        """标准化节点ID"""
        for alias, canonical in cls.TYPE_ALIASES.items():
            if node_id.startswith(f"{alias}:"):
                node_id = f"{canonical}:{node_id[len(alias)+1:]}"
                break
        return node_id

    @classmethod
    def normalize_complexity(cls, complexity: str) -> str:
        """标准化复杂度"""
        return cls.COMPLEXITY_MAP.get(complexity.lower(), complexity)

    @classmethod
    def normalize_graph(cls, graph: KnowledgeGraph) -> KnowledgeGraph:
        """标准化整个图 — 幂等操作"""
        # 标准化节点ID
        id_map = {}
        for node in graph.nodes:
            old_id = node.id
            new_id = cls.normalize_node_id(old_id)
            node.complexity = cls.normalize_complexity(node.complexity)
            node.id = new_id
            if old_id != new_id:
                id_map[old_id] = new_id

        # 更新边的source/target
        for edge in graph.edges:
            edge.source_id = id_map.get(edge.source_id, edge.source_id)
            edge.target_id = id_map.get(edge.target_id, edge.target_id)

        # 移除孤边
        valid_ids = {n.id for n in graph.nodes}
        graph.edges = [e for e in graph.edges
                       if e.source_id in valid_ids and e.target_id in valid_ids]

        # 边去重
        seen = set()
        unique_edges = []
        for e in graph.edges:
            key = (e.source_id, e.target_id, e.edge_type)
            if key not in seen:
                seen.add(key)
                unique_edges.append(e)
        graph.edges = unique_edges

        return graph


# ─── 知识图谱构建引擎 ─────────────────────────────────────────

class KnowledgeGrapher:
    """知识图谱构建引擎 — 混合分析管线

    管线: 文件扫描 → 静态分析 → LLM增强 → 标准化 → 输出
    
    使用方式:
        grapher = KnowledgeGrapher(llm_enhance_func=None)
        graph = grapher.build_from_codebase("/path/to/project")
    """

    def __init__(self, llm_enhance_func: Optional[Callable] = None):
        """
        llm_enhance_func: async (nodes, edges) -> (enhanced_nodes, enhanced_edges)
                          为节点添加语义摘要和关系
        """
        self.llm_enhance = llm_enhance_func
        self.normalizer = GraphNormalizer()

    def build_from_code(self, files: dict[str, str]) -> KnowledgeGraph:
        """从代码文件列表构建知识图谱

        Args:
            files: {filename: content} 字典
        Returns:
            KnowledgeGraph
        """
        graph = KnowledgeGraph()

        for filename, content in files.items():
            # 静态分析
            nodes = FileAnalyzer.analyze_file(filename, content)
            for node in nodes:
                graph.add_node(node)

            # 添加 contains 边
            graph.add_edge(GraphEdge(
                source_id=f"file:{filename}",
                target_id=f"file:{filename}",  # 将被修正
                edge_type="contains",
                edge_category="structural"
            ))

            # 提取导入依赖
            language = FileAnalyzer.detect_language(filename)
            if language:
                imports = FileAnalyzer.extract_imports(content, language)
                for imp in imports:
                    graph.add_edge(GraphEdge(
                        source_id=f"file:{filename}",
                        target_id=f"module:{imp}",
                        edge_type="imports",
                        edge_category="dependencies"
                    ))

        # 修正contains边的target（指向第一个子节点）
        # 简化：文件→函数名的连接
        for node in graph.nodes:
            if node.node_type in ("function", "class"):
                source = f"file:{node.properties.get('file', '')}"
                if source != f"file:":  # 确保source有效
                    graph.add_edge(GraphEdge(
                        source_id=source,
                        target_id=node.id,
                        edge_type="contains",
                        edge_category="structural"
                    ))

        # 标准化
        graph = self.normalizer.normalize_graph(graph)

        # LLM增强（可选）
        # if self.llm_enhance:
        #     enhanced = await self.llm_enhance(graph.nodes, graph.edges)
        #     ...

        graph.metadata = {
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "node_types": self._count_types(graph.nodes),
            "edge_categories": self._count_categories(graph.edges),
        }

        return graph

    def build_from_knowledge_base(self, pages: dict[str, str]) -> KnowledgeGraph:
        """从知识库（Markdown Wiki）构建知识图谱

        分析：Wikilinks [[target]]、index.md分类层级、章节结构
        """
        graph = KnowledgeGraph()

        for title, content in pages.items():
            # 文章节点
            node = GraphNode(
                id=f"article:{title}",
                label=title,
                node_type="article",
                properties={"content_length": len(content)}
            )
            graph.add_node(node)

            # 提取Wikilinks [[target]]
            for match in re.finditer(r'\[\[(.+?)\]\]', content):
                target = match.group(1)
                graph.add_edge(GraphEdge(
                    source_id=f"article:{title}",
                    target_id=f"article:{target}",
                    edge_type="related",
                    edge_category="knowledge"
                ))

            # 提取话题标签 #tag
            for match in re.finditer(r'#([a-zA-Z\u4e00-\u9fff]\w+)', content):
                tag = match.group(1)
                graph.add_node(GraphNode(
                    id=f"topic:{tag}",
                    label=tag,
                    node_type="topic"
                ))
                graph.add_edge(GraphEdge(
                    source_id=f"article:{title}",
                    target_id=f"topic:{tag}",
                    edge_type="tagged",
                    edge_category="semantic"
                ))

        return self.normalizer.normalize_graph(graph)

    def build_from_subsidiaries(self, subsidiaries: list[dict]) -> KnowledgeGraph:
        """从子公司能力列表构建能力图谱

        用于CEO决策引擎的ROI分析
        subsidiaries: [{"name": "墨声", "skills": [...], "revenue": 0, ...}]
        """
        graph = KnowledgeGraph()

        for sub in subsidiaries:
            # 子公司节点
            graph.add_node(GraphNode(
                id=f"subsidiary:{sub['name']}",
                label=sub["name"],
                node_type="domain",
                properties={k: v for k, v in sub.items() if k != "skills"}
            ))

            # 技能节点
            for skill in sub.get("skills", []):
                skill_id = f"skill:{sub['name']}:{skill}"
                graph.add_node(GraphNode(
                    id=skill_id,
                    label=skill,
                    node_type="concept",
                    properties={"subsidiary": sub["name"]}
                ))
                graph.add_edge(GraphEdge(
                    source_id=f"subsidiary:{sub['name']}",
                    target_id=skill_id,
                    edge_type="owns",
                    edge_category="domain"
                ))

        return self.normalizer.normalize_graph(graph)

    def export_mermaid(self, graph: KnowledgeGraph) -> str:
        """导出为Mermaid图表的Markdown"""
        lines = ["```mermaid"]
        lines.append("graph TD")

        for node in graph.nodes:
            safe_id = node.id.replace(":", "_").replace("/", "_").replace(".", "_")
            label = node.label.replace('"', "'")
            lines.append(f"    {safe_id}[\"{label}\"]")

        for edge in graph.edges:
            s = edge.source_id.replace(":", "_").replace("/", "_").replace(".", "_")
            t = edge.target_id.replace(":", "_").replace("/", "_").replace(".", "_")
            label = edge.edge_type
            lines.append(f"    {s} -->|{label}| {t}")

        lines.append("```")
        return "\n".join(lines)

    def export_json(self, graph: KnowledgeGraph) -> str:
        """导出为JSON"""
        return json.dumps(graph.to_dict(), ensure_ascii=False, indent=2)

    def _count_types(self, nodes: list[GraphNode]) -> dict:
        counts = {}
        for n in nodes:
            counts[n.node_type] = counts.get(n.node_type, 0) + 1
        return counts

    def _count_categories(self, edges: list[GraphEdge]) -> dict:
        counts = {}
        for e in edges:
            counts[e.edge_category] = counts.get(e.edge_category, 0) + 1
        return counts


# ─── 陈旧检测 ──────────────────────────────────────────────────────

def compute_fingerprint(content: str) -> str:
    """计算文件指纹 — 用于变更检测"""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def detect_changes(old_fingerprints: dict[str, str],
                   new_files: dict[str, str]) -> dict[str, str]:
    """检测文件变更，返回变更类型

    Returns: {filename: "added"|"modified"|"removed"|"unchanged"}
    """
    changes = {}
    old_names = set(old_fingerprints.keys())
    new_names = set(new_files.keys())

    for name in new_names - old_names:
        changes[name] = "added"
    for name in old_names - new_names:
        changes[name] = "removed"
    for name in old_names & new_names:
        old_fp = old_fingerprints[name]
        new_fp = compute_fingerprint(new_files.get(name, ""))
        changes[name] = "modified" if old_fp != new_fp else "unchanged"

    return changes

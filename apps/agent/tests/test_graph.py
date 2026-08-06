import pytest
from agent.engine.graph import WorkflowGraph, WorkflowGraphError, GraphNode, GraphEdge


def build_linear() -> WorkflowGraph:
    g = WorkflowGraph()
    for i, t in enumerate(["start-node", "reply-node"]):
        g.add_node(GraphNode(node_id=f"n{i}", node_type=t, name=t))
    g.add_edge(GraphEdge(source="n0", target="n1"))
    return g


def test_linear_valid():
    g = build_linear()
    g.validate()
    assert g.get_start() == "n0"
    assert g.successors("n0") == ["n1"]
    assert g.predecessors("n1") == ["n0"]


def test_json_roundtrip():
    g = build_linear()
    g2 = WorkflowGraph.from_json(g.to_json())
    assert g2.to_json() == g.to_json()
    g2.validate()


def test_cycle_rejected():
    g = WorkflowGraph()
    g.add_node(GraphNode(node_id="a", node_type="start-node"))
    g.add_node(GraphNode(node_id="b", node_type="reply-node"))
    g.add_edge(GraphEdge(source="a", target="b"))
    g.add_edge(GraphEdge(source="b", target="a"))   # 回边
    with pytest.raises(WorkflowGraphError):
        g.validate()


def test_dup_node_rejected():
    g = WorkflowGraph()
    g.add_node(GraphNode(node_id="a", node_type="start-node"))
    with pytest.raises(WorkflowGraphError):
        g.add_node(GraphNode(node_id="a", node_type="reply-node"))


def test_missing_start_rejected():
    g = WorkflowGraph()
    g.add_node(GraphNode(node_id="a", node_type="reply-node"))
    with pytest.raises(WorkflowGraphError):
        g.get_start()
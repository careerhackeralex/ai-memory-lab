from conftest import mcp_call


def test_01_mcp(base):
    res = mcp_call(base + "/mcp/lab/", "tools/list")
    names = [t["name"] for t in res["result"]["tools"]]
    print(f"\n  /mcp/lab/ tools/list: {len(names)}개 — {', '.join(names[:4])} …")
    assert "retain" in names or "sync_retain" in names, names
    assert "recall" in names, names

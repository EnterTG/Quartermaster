import asyncio
import os
import re
import unittest

from src import mcp_server

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(ROOT_DIR, "skills", "quartermaster")

# Anything shaped like one of the server's tool names (search_owned_assets, get_vault_stats, ...);
# parameters and result fields (local_only, vault_owned, asset_ids) don't start with these verbs
TOOL_LIKE = re.compile(r"\b(?:search|get|list|audit|import|validate)_[a-z_]+\b")


def _tool_names():
    return {t.name for t in asyncio.run(mcp_server.mcp.list_tools())}


def _read_skill():
    with open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8") as f:
        text = f.read()
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise AssertionError("SKILL.md has no frontmatter")
    meta = dict(line.split(":", 1) for line in match.group(1).splitlines())
    return {k.strip(): v.strip() for k, v in meta.items()}, text[match.end():]


class TestServerInstructions(unittest.TestCase):
    """The server shipped no instructions, so agents only used the vault when the user asked them to.
    It now tells them when to search it; these keep that text naming tools that exist."""

    def test_server_sends_instructions(self):
        self.assertEqual(mcp_server.mcp.instructions, mcp_server.INSTRUCTIONS)

    def test_instructions_name_only_real_tools(self):
        named = set(TOOL_LIKE.findall(mcp_server.INSTRUCTIONS))
        self.assertTrue({"search_owned_assets", "get_stack_recommendations", "audit_project",
                         "validate_stack", "import_asset_to_project"} <= named)
        self.assertEqual(named - _tool_names(), set())


class TestSkill(unittest.TestCase):
    """skills/quartermaster/SKILL.md is the same workflow for clients that load Agent Skills."""

    def test_frontmatter_follows_the_agent_skills_format(self):
        meta, _ = _read_skill()
        self.assertEqual(meta["name"], os.path.basename(SKILL_DIR))   # must match its folder
        self.assertRegex(meta["name"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertTrue(0 < len(meta["description"]) <= 1024)

    def test_skill_covers_every_tool_and_names_no_others(self):
        _, body = _read_skill()
        self.assertEqual(set(TOOL_LIKE.findall(body)), _tool_names())


if __name__ == "__main__":
    unittest.main()

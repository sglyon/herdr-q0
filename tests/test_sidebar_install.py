import unittest
from install_sidebar import NAME, patch_sidebar, sidebar_layout


class SidebarInstallTests(unittest.TestCase):
    def test_only_builtin_agents_references_in_personal_layout_change(self):
        tree = {"id": "root", "children": [
            {"id": "agents", "content": {"mod": "agents", "props": {"custom": True}}, "size": {"weight": 2}},
            {"content": {"mod": "my-agents"}},
            {"children": [{"content": {"mod": "agents"}}]},
            {"content": {"mod": "q0-agents"}}]}
        result = sidebar_layout(tree)
        self.assertEqual(tree["children"][0]["content"]["mod"], "agents")
        self.assertEqual(result["children"][0]["content"], {"mod": NAME, "props": {"custom": True}})
        self.assertEqual(result["children"][0]["size"], {"weight": 2})
        self.assertEqual(result["children"][1]["content"]["mod"], "my-agents")
        self.assertEqual(result["children"][2]["children"][0]["content"]["mod"], NAME)
        self.assertEqual(result["children"][3]["content"]["mod"], "q0-agents")
        self.assertEqual(sidebar_layout(result), result)

    def test_unknown_upstream_structure_fails_before_installation(self):
        with self.assertRaisesRegex(ValueError, "Herdr Agents mod changed"):
            patch_sidebar('export default class ChangedAgents {}')

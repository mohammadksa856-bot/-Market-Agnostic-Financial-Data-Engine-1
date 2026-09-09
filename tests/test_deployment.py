import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeploymentContractTests(unittest.TestCase):
    def test_runtime_state_is_not_mounted_over_seed_data(self):
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn("/app/state/financial.sqlite3", compose)
        self.assertNotIn("./data:/app/data", compose)

    def test_startup_preserves_existing_database(self):
        startup = (ROOT / "deploy" / "start-production.sh").read_text(encoding="utf-8")
        self.assertIn('if [ ! -s "$database" ]', startup)
        self.assertIn('--raw-dir "$raw_dir"', startup)

    def test_supabase_projection_is_read_only_for_clients(self):
        migration = (ROOT / "supabase" / "migrations" / "0001_financial_facts.sql").read_text(encoding="utf-8")
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn("enable row level security", migration)
        self.assertIn("on public.financial_facts from anon", migration)
        self.assertIn("grant select", migration)
        self.assertIn("supabase-publisher", compose)

    def test_release_deploys_only_after_successful_main_tests(self):
        workflow = (ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_run.conclusion == 'success'", workflow)
        self.assertIn("workflow_run.head_branch == 'main'", workflow)
        self.assertIn("PRODUCTION_DEPLOY_ENABLED", workflow)
        self.assertIn("VPS_KNOWN_HOSTS", workflow)


if __name__ == "__main__":
    unittest.main()

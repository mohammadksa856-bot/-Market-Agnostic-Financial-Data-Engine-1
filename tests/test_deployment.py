import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeploymentContractTests(unittest.TestCase):
    def test_runtime_state_is_not_mounted_over_seed_data(self):
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn("/app/state/financial.sqlite3", compose)
        self.assertIn("FINENGINE_SEED_RAW_DIR", compose)
        self.assertIn("/app/data/raw:ro", compose)
        self.assertNotIn("./data:/app/data", compose)

    def test_container_installs_xauth_for_xvfb_runtime(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("xauth", dockerfile)

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
        self.assertIn("'as_of', 'daily', 'event'", migration)
        self.assertIn("supabase-publisher", compose)

    def test_release_deploys_only_after_successful_main_tests(self):
        workflow = (ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_run.conclusion == 'success'", workflow)
        self.assertIn("workflow_run.head_branch == 'main'", workflow)
        self.assertIn("PRODUCTION_DEPLOY_ENABLED", workflow)
        self.assertIn("VPS_KNOWN_HOSTS", workflow)

    def test_ci_parses_every_deployment_shell_script(self):
        workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
        self.assertIn("sh -n deploy/*.sh", workflow)

    def test_supabase_publish_rebuilds_and_audits_before_export(self):
        workflow = (ROOT / ".github" / "workflows" / "publish-supabase.yml").read_text(encoding="utf-8")
        self.assertIn("SUPABASE_PUBLISH_ENABLED", workflow)
        self.assertIn("bootstrap", workflow)
        self.assertLess(workflow.index("bootstrap"), workflow.index("audit"))
        self.assertLess(workflow.index("audit"), workflow.index("export-supabase"))
        self.assertIn("SUPABASE_SECRET_KEY", workflow)

    def test_vps_preflight_checks_resources_secrets_and_compose(self):
        preflight = (ROOT / "deploy" / "preflight.sh").read_text(encoding="utf-8")
        self.assertIn("_NPROCESSORS_ONLN", preflight)
        self.assertIn("/proc/meminfo", preflight)
        self.assertIn("150 GiB", preflight)
        self.assertIn("FINENGINE_API_KEY", preflight)
        self.assertIn("API_DOMAIN", preflight)
        self.assertIn("docker compose", preflight)
        self.assertIn("must be an absolute server path", preflight)

    def test_backup_worker_verifies_bundle_and_backs_off_on_failure(self):
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        worker = (ROOT / "deploy" / "backup-loop.sh").read_text(encoding="utf-8")
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn('/app/deploy/backup-loop.sh', compose)
        self.assertIn("verify_portable_bundle", worker)
        self.assertIn("backup-status.json", worker)
        self.assertIn("FINENGINE_BACKUP_RETRY_SECONDS", worker)
        self.assertIn('sleep "$retry_delay"', worker)
        self.assertIn('>"$result_file" 2>"$error_file"', worker)
        self.assertIn("backup-loop.sh", dockerfile)
        self.assertIn("backup-status.json", compose)
        self.assertIn("kill -0 1", compose)

    def test_onboarding_worker_is_bounded_durable_and_quality_gated(self):
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        worker = (ROOT / "deploy" / "onboarding-loop.sh").read_text(encoding="utf-8")
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("universe-onboard", worker)
        self.assertIn("FINENGINE_ONBOARDING_US_LIMIT", worker)
        self.assertIn("FINENGINE_ONBOARDING_SA_LIMIT", worker)
        self.assertIn("onboarding-status.json", worker)
        self.assertIn("onboarding-loop.sh", dockerfile)
        self.assertIn("onboarding:", compose)
        self.assertIn("FINENGINE_ONBOARDING_SCHEDULE_SECONDS", compose)
        self.assertIn("universe-refresh", compose)

    def test_background_worker_adds_bounded_parallel_capacity(self):
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn("  worker:", compose)
        self.assertIn("financial.sqlite3 worker --poll 10", compose)
        self.assertIn("xvfb-run -a", compose)
        self.assertIn("kill -0 1", compose)


if __name__ == "__main__":
    unittest.main()

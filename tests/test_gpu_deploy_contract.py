#!/usr/bin/env python3
"""Deployment contract tests for the single-user GPU container."""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GPU_COMPOSE = REPO_ROOT / "deploy" / "docker-compose.gpu.yaml"
MULTI_COMPOSE = REPO_ROOT / "deploy" / "docker-compose.yaml"
GPU_ENV_EXAMPLE = REPO_ROOT / "deploy" / ".env.gpu.example"
MULTI_ENV_EXAMPLE = REPO_ROOT / "deploy" / ".env.example"
GPU_DOCKERFILE = REPO_ROOT / "deploy" / "Dockerfile.gpu"
ENTRYPOINT = REPO_ROOT / "deploy" / "entrypoint.sh"


class GpuDeployContractTest(unittest.TestCase):
    def test_compose_mounts_host_framework_to_container_framework_path(self):
        content = GPU_COMPOSE.read_text()

        self.assertIn("FRAMEWORK_PATH", content)
        self.assertIn(":/aris/framework", content)
        self.assertIn("DEV_FRAMEWORK_PATH", content)
        self.assertIn(":/aris/aris-dev", content)
        self.assertIn("BUILD_HTTP_PROXY", content)
        self.assertIn("BUILD_HTTPS_PROXY", content)

    def test_env_example_uses_generic_host_paths(self):
        content = GPU_ENV_EXAMPLE.read_text()

        self.assertIn("USERNAME=researcher", content)
        self.assertIn("FRAMEWORK_PATH=/data/aris/aris-framework", content)
        self.assertIn("DEV_FRAMEWORK_PATH=/data/aris/aris-dev", content)
        self.assertIn("PROJECT_PATH=/data/aris/projects", content)
        self.assertIn("DATASETS_PATH=/data/datasets", content)
        self.assertNotIn("USERNAME=orangmood", content)
        self.assertNotIn("/workspace", content)

    def test_env_examples_include_runtime_proxy_git_proxy_and_feishu_vars(self):
        required = [
            "HTTP_PROXY=",
            "HTTPS_PROXY=",
            "NO_PROXY=",
            "http_proxy=",
            "https_proxy=",
            "no_proxy=",
            "GIT_HTTP_PROXY=",
            "GIT_HTTPS_PROXY=",
            "FEISHU_APP_ID=",
            "FEISHU_APP_SECRET=",
            "FEISHU_USER_ID=",
            "FEISHU_RECEIVE_ID_TYPE=open_id",
            "FEISHU_ENABLE_WS=0",
            "BRIDGE_PORT=5000",
            "ARIS_PROJECT_ROOT=",
            "ARIS_FEISHU_CONTROL_ROOT=",
        ]
        for path in [GPU_ENV_EXAMPLE, MULTI_ENV_EXAMPLE]:
            content = path.read_text()
            with self.subTest(path=path.name):
                for item in required:
                    self.assertIn(item, content)

    def test_compose_files_pass_proxy_git_proxy_and_feishu_vars(self):
        required = [
            "HTTP_PROXY=${HTTP_PROXY:-}",
            "HTTPS_PROXY=${HTTPS_PROXY:-}",
            "NO_PROXY=${NO_PROXY:-}",
            "http_proxy=${http_proxy:-}",
            "https_proxy=${https_proxy:-}",
            "no_proxy=${no_proxy:-}",
            "GIT_HTTP_PROXY=${GIT_HTTP_PROXY:-}",
            "GIT_HTTPS_PROXY=${GIT_HTTPS_PROXY:-}",
            "FEISHU_APP_ID=${FEISHU_APP_ID:-}",
            "FEISHU_APP_SECRET=${FEISHU_APP_SECRET:-}",
            "FEISHU_USER_ID=${FEISHU_USER_ID:-}",
            "FEISHU_RECEIVE_ID_TYPE=${FEISHU_RECEIVE_ID_TYPE:-open_id}",
            "FEISHU_ENABLE_WS=${FEISHU_ENABLE_WS:-0}",
            "BRIDGE_PORT=${BRIDGE_PORT:-5000}",
            "ARIS_PROJECT_ROOT=${ARIS_PROJECT_ROOT:-/aris/framework}",
            "ARIS_FEISHU_CONTROL_ROOT=${ARIS_FEISHU_CONTROL_ROOT:-}",
        ]
        for path in [GPU_COMPOSE, MULTI_COMPOSE]:
            content = path.read_text()
            with self.subTest(path=path.name):
                for item in required:
                    self.assertIn(item, content)

    def test_entrypoint_persists_upper_lower_proxy_and_optional_git_proxy(self):
        content = ENTRYPOINT.read_text()

        self.assertIn('PROXY_HTTP="${HTTP_PROXY:-${http_proxy:-}}"', content)
        self.assertIn('PROXY_HTTPS="${HTTPS_PROXY:-${https_proxy:-$PROXY_HTTP}}"', content)
        self.assertIn('PROXY_NO="${NO_PROXY:-${no_proxy:-127.0.0.1,localhost}}"', content)
        for name in ["HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy"]:
            self.assertIn(f'echo "{name}=', content)
        self.assertIn('git config --global http.proxy "$GIT_HTTP_PROXY"', content)
        self.assertIn('git config --global https.proxy "$GIT_HTTPS_PROXY"', content)

    def test_gpu_dockerfile_uses_distribution_python_without_ppa(self):
        content = GPU_DOCKERFILE.read_text()

        self.assertNotIn("deadsnakes", content)
        self.assertNotIn("add-apt-repository", content)
        self.assertIn("python3-venv", content)
        self.assertIn("python3-dev", content)
        self.assertIn("python3-distutils", content)
        self.assertIn("python3-pip", content)
        self.assertNotIn("get-pip.py", content)

    def test_gpu_dockerfile_clears_base_image_proxy_before_apt(self):
        content = GPU_DOCKERFILE.read_text()
        first_apt = content.index("apt-get update")
        early_content = content[:first_apt]

        self.assertIn("BUILD_HTTP_PROXY", early_content)
        self.assertIn("BUILD_HTTPS_PROXY", early_content)
        self.assertIn('export http_proxy="${BUILD_HTTP_PROXY}"', early_content)
        self.assertIn("/etc/apt/apt.conf.d/*proxy*", early_content)
        self.assertIn("/etc/environment", early_content)
        self.assertGreaterEqual(content.count('export http_proxy="${BUILD_HTTP_PROXY}"'), 8)


if __name__ == "__main__":
    unittest.main()

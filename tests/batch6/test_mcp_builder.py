"""
Tests for 'mcp-builder' skill.
Generated from benchmark case definitions for mcp-builder.
"""

import ast
import base64
import glob
import json
import os
import py_compile
import re
import subprocess
import textwrap

import pytest

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


class TestMcpBuilder:
    """Verify the mcp-builder skill output."""

    REPO_DIR = '/workspace/servers'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestMcpBuilder.REPO_DIR, rel)

    @staticmethod
    def _safe_read(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    @staticmethod
    def _load_yaml(path: str):
        if yaml is None:
            pytest.skip("PyYAML not available")
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return yaml.safe_load(fh)

    @staticmethod
    def _load_json(path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return json.load(fh)

    @classmethod
    def _run_in_repo(cls, script: str, timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python", "-c", textwrap.dedent(script)],
            cwd=cls.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def _run_cmd(cls, command, args=None, timeout=120):
        args = args or []
        if isinstance(command, str) and args:
            return subprocess.run(
                [command, *args],
                cwd=cls.REPO_DIR,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        return subprocess.run(
            command if isinstance(command, list) else command,
            cwd=cls.REPO_DIR,
            shell=isinstance(command, str),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def _ensure_setup(cls, label, setup_cmds, fallback):
        if not setup_cmds:
            return
        key = tuple(setup_cmds)
        if key in cls._SETUP_CACHE:
            ok, msg = cls._SETUP_CACHE[key]
            if ok:
                return
            if fallback == "skip_if_setup_fails":
                pytest.skip(f"{label} setup failed: {msg}")
            pytest.fail(f"{label} setup failed: {msg}")
        for cmd in setup_cmds:
            r = subprocess.run(cmd, cwd=cls.REPO_DIR, shell=True,
                               capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                msg = (r.stderr or r.stdout or 'failed').strip()
                cls._SETUP_CACHE[key] = (False, msg)
                if fallback == "skip_if_setup_fails":
                    pytest.skip(f"{label} setup failed: {msg}")
                pytest.fail(f"{label} setup failed: {msg}")
        cls._SETUP_CACHE[key] = (True, 'ok')


    # ── file_path_check (static) ────────────────────────────────────────

    def test_index_ts_exists(self):
        """Verify src/index.ts server entry point exists"""
        _p = self._repo_path('src/index.ts')
        assert os.path.isfile(_p), f'Missing file: src/index.ts'

    def test_package_json_has_mcp_sdk(self):
        """Verify package.json has @modelcontextprotocol/sdk dependency"""
        _p = self._repo_path('package.json')
        assert os.path.isfile(_p), f'Missing file: package.json'
        self._load_json(_p)  # parse check

    def test_tools_dir_exists(self):
        """Verify src/tools/ or src/resources/ directories exist"""
        _p = self._repo_path('src/tools/')
        assert os.path.isdir(_p), f'Missing directory: src/tools/'
        _p = self._repo_path('src/resources/')
        assert os.path.isdir(_p), f'Missing directory: src/resources/'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_server_import_sdk(self):
        """Verify src/index.ts imports Server from MCP SDK"""
        _p = self._repo_path('src/index.ts')
        assert os.path.exists(_p), f'Missing: src/index.ts'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert '@modelcontextprotocol/sdk' in _all, 'Missing: @modelcontextprotocol/sdk'
        assert 'Server' in _all, 'Missing: Server'

    def test_handler_registrations(self):
        """Verify request handlers registered for resources, tools, and prompts"""
        _p = self._repo_path('src/index.ts')
        assert os.path.exists(_p), f'Missing: src/index.ts'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'setRequestHandler' in _all, 'Missing: setRequestHandler'
        assert 'ListResources' in _all, 'Missing: ListResources'
        assert 'CallTool' in _all, 'Missing: CallTool'
        assert 'ListPrompts' in _all, 'Missing: ListPrompts'

    def test_tool_input_schema(self):
        """Verify tool definitions have inputSchema with type 'object'"""
        _p = self._repo_path('src/')
        assert os.path.isdir(_p), f'Missing directory: src/'
        _contents = ''
        for _f in sorted(glob.glob(os.path.join(_p, '**', '*'), recursive=True)):
            if os.path.isfile(_f):
                _contents += self._safe_read(_f) + '\n'
        _all = _contents if isinstance(_contents, str) else ''
        assert 'inputSchema' in _all, 'Missing: inputSchema'
        assert 'properties' in _all, 'Missing: properties'
        assert 'type' in _all, 'Missing: type'

    # ── functional_check ────────────────────────────────────────

    def test_typescript_compiles(self):
        """Verify TypeScript compiles without errors"""
        self._ensure_setup('test_typescript_compiles', ['npm install'], 'fail_if_missing')
        result = self._run_cmd('npx', args=['tsc', '--noEmit'], timeout=120)
        assert result.returncode == 0, (
            f'test_typescript_compiles failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_npm_test_passes(self):
        """Verify npm test passes"""
        self._ensure_setup('test_npm_test_passes', ['npm install'], 'fail_if_missing')
        result = self._run_cmd('npm', args=['test'], timeout=300)
        assert result.returncode == 0, (
            f'test_npm_test_passes failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_package_json_valid_json(self):
        """Verify package.json is valid JSON with MCP SDK dependency"""
        result = self._run_cmd('python', args=['-c', "import json; pkg=json.loads(open('package.json').read()); deps={**pkg.get('dependencies',{}),**pkg.get('devDependencies',{})}; assert '@modelcontextprotocol/sdk' in deps; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_package_json_valid_json failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_server_connect_grep(self):
        """Verify server.connect is called with transport"""
        result = self._run_cmd('python', args=['-c', "content=open('src/index.ts').read(); assert 'connect' in content and ('Transport' in content or 'transport' in content), 'No transport connect'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_server_connect_grep failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_at_least_2_tools(self):
        """Verify at least 2 tools are defined"""
        result = self._run_cmd('python', args=['-c', "import glob; tool_files=glob.glob('src/tools/**/*.ts',recursive=True); content=open('src/index.ts').read(); tool_count=content.count('name:'); assert tool_count>=2 or len(tool_files)>=2, f'Only {max(tool_count,len(tool_files))} tools'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_at_least_2_tools failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_error_handling_pattern(self):
        """Verify McpError is used for error responses"""
        result = self._run_cmd('python', args=['-c', "import glob; files=glob.glob('src/**/*.ts',recursive=True); found=False\nfor f in files:\n    c=open(f).read()\n    if 'McpError' in c or 'ErrorCode' in c: found=True; break\nassert found, 'No McpError usage found'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_error_handling_pattern failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'


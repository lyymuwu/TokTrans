import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import token_saver


class TokenSaverUnitTests(unittest.TestCase):
    def test_detects_chinese(self):
        det = token_saver.detect_language("请帮我检查这个仓库的测试失败原因")
        self.assertTrue(det.should_translate)
        self.assertEqual(det.language, "Chinese")

    def test_english_does_not_translate(self):
        det = token_saver.detect_language("Please inspect why the tests fail.")
        self.assertFalse(det.should_translate)

    def test_model_detection_extends_to_latin_languages(self):
        cfg = dict(token_saver.DEFAULT_CONFIG)
        with mock.patch.object(
            token_saver,
            "detect_language_with_model",
            return_value=token_saver.Detection(True, "Spanish", 0.0, 0.0, "model-detect:0.98"),
        ) as detector:
            det = token_saver.resolve_detection("Por favor revisa por que fallan las pruebas.", cfg)
        self.assertTrue(det.should_translate)
        self.assertEqual(det.language, "Spanish")
        detector.assert_called_once()

    def test_configured_source_language_forces_translation(self):
        cfg = dict(token_saver.DEFAULT_CONFIG)
        cfg["source_language"] = "French"
        det = token_saver.resolve_detection("Veuillez corriger les tests.", cfg)
        self.assertTrue(det.should_translate)
        self.assertEqual(det.language, "French")

    def test_detects_other_high_token_languages(self):
        samples = {
            "Japanese": "このリポジトリのテスト失敗の原因を調べてください",
            "Thai": "ช่วยตรวจสอบว่าทำไมการทดสอบของโปรเจกต์นี้จึงล้มเหลว",
            "Hindi": "कृपया जाँचें कि इस प्रोजेक्ट के टेस्ट क्यों असफल हो रहे हैं",
        }
        for expected, text in samples.items():
            with self.subTest(expected=expected):
                det = token_saver.detect_language(text)
                self.assertTrue(det.should_translate)
                self.assertEqual(det.language, expected)

    def test_code_heavy_does_not_translate(self):
        text = """```python
def hello():
    return "你好"
```
/tmp/project/main.py
"""
        det = token_saver.detect_language(text)
        self.assertFalse(det.should_translate)
        self.assertEqual(det.reason, "code-heavy")

    def test_strip_protected_regions(self):
        text = "翻译这个:\n```json\n{\"message\":\"你好\"}\n```\n然后解释"
        stripped = token_saver.strip_protected_regions(text)
        self.assertIn("翻译这个", stripped)
        self.assertIn("然后解释", stripped)
        self.assertNotIn("message", stripped)

    def test_find_real_codex_skips_self(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self_path = root / "codex-ts"
            self_path.write_text("#!/bin/sh\n", encoding="utf-8")
            self_path.chmod(self_path.stat().st_mode | stat.S_IXUSR)
            real = root / "codex"
            real.write_text("#!/bin/sh\n", encoding="utf-8")
            real.chmod(real.stat().st_mode | stat.S_IXUSR)
            with mock.patch.dict(os.environ, {"PATH": str(root)}, clear=False):
                found = token_saver.find_real_codex(self_path)
            self.assertEqual(Path(found), real)

    def test_split_exec_prompt_with_stdin(self):
        args, prompt, read_stdin = token_saver.split_exec_prompt(["exec", "-"], "中文输入")
        self.assertEqual(args, ["exec"])
        self.assertEqual(prompt, "中文输入")
        self.assertTrue(read_stdin)

    def test_inject_output_file_removes_user_output(self):
        args, user = token_saver.inject_output_file(["exec", "-o", "user.md"], Path("/tmp/final.md"))
        self.assertEqual(user, Path("user.md"))
        self.assertEqual(args[-2:], ["--output-last-message", "/tmp/final.md"])
        self.assertNotIn("user.md", args)

    def test_codex_cli_provider_uses_configured_cheap_model(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fake = root / "codex"
            seen = root / "args.json"
            fake.write_text(
                f"""#!/usr/bin/env python3
import json, sys
from pathlib import Path
args = sys.argv[1:]
Path({str(seen)!r}).write_text(json.dumps(args), encoding="utf-8")
out = args[args.index("--output-last-message") + 1]
Path(out).write_text("Translated text", encoding="utf-8")
""",
                encoding="utf-8",
            )
            fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
            cfg = dict(token_saver.DEFAULT_CONFIG)
            cfg["provider"] = "codex_cli"
            cfg["codex_model"] = "gpt-5.4-mini"
            with mock.patch.dict(os.environ, {"CODEX_TOKEN_SAVER_REAL_CODEX": str(fake)}, clear=False):
                result = token_saver.translation_chat([{"role": "user", "content": "翻译"}], cfg)
            args = json.loads(seen.read_text(encoding="utf-8"))
            self.assertEqual(result, "Translated text")
            self.assertIn("-m", args)
            self.assertEqual(args[args.index("-m") + 1], "gpt-5.4-mini")

    def test_codex_cli_provider_times_out(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fake = root / "codex"
            fake.write_text(
                """#!/usr/bin/env python3
import time
time.sleep(2)
""",
                encoding="utf-8",
            )
            fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
            cfg = dict(token_saver.DEFAULT_CONFIG)
            cfg["provider"] = "codex_cli"
            cfg["timeout_seconds"] = 0.1
            with mock.patch.dict(os.environ, {"CODEX_TOKEN_SAVER_REAL_CODEX": str(fake)}, clear=False):
                with self.assertRaisesRegex(RuntimeError, "timed out"):
                    token_saver.translation_chat([{"role": "user", "content": "翻译"}], cfg)


class TokenSaverIntegrationTests(unittest.TestCase):
    def test_exec_flow_with_fake_codex(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fake = root / "codex"
            seen = root / "seen.txt"
            fake.write_text(
                f"""#!/usr/bin/env python3
import sys
from pathlib import Path
args=sys.argv[1:]
out=None
for i,a in enumerate(args):
    if a in ("-o","--output-last-message"):
        out=args[i+1]
if out:
    Path(out).write_text("Final answer in English", encoding="utf-8")
Path({str(seen)!r}).write_text(args[-1], encoding="utf-8")
print("codex saw:" + args[-1])
""",
                encoding="utf-8",
            )
            fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

            cfg = dict(token_saver.DEFAULT_CONFIG)
            cfg["show_savings_report"] = False
            with mock.patch.dict(os.environ, {"CODEX_TOKEN_SAVER_REAL_CODEX": str(fake)}, clear=False):
                with mock.patch.object(token_saver, "translate_to_english", return_value="Please inspect tests"):
                    with mock.patch.object(token_saver, "translate_from_english", return_value="最终中文答案"):
                        with mock.patch("sys.stdout") as stdout:
                            code = token_saver.handle_exec(["exec", "请检查测试"], cfg, None)
            self.assertEqual(code, 0)
            self.assertEqual(seen.read_text(encoding="utf-8"), "Please inspect tests")
            self.assertNotIn("Token Saver note", seen.read_text(encoding="utf-8"))
            printed = "".join(call.args[0] for call in stdout.write.call_args_list if call.args)
            self.assertIn("最终中文答案", printed)

    def test_translation_failure_falls_back_to_raw_codex(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            marker = root / "marker.txt"
            fake = root / "codex"
            fake.write_text(
                f"""#!/usr/bin/env python3
from pathlib import Path
Path({str(marker)!r}).write_text("raw", encoding="utf-8")
""",
                encoding="utf-8",
            )
            fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
            cfg = dict(token_saver.DEFAULT_CONFIG)
            with mock.patch.dict(os.environ, {"CODEX_TOKEN_SAVER_REAL_CODEX": str(fake)}, clear=False):
                with mock.patch.object(token_saver, "translate_to_english", side_effect=RuntimeError("boom")):
                    code = token_saver.handle_exec(["exec", "请检查测试"], cfg, None)
            self.assertEqual(code, 0)
            self.assertEqual(marker.read_text(encoding="utf-8"), "raw")


class InstallerTests(unittest.TestCase):
    def run_script(self, script, *args, env=None):
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run(
            ["bash", str(ROOT / "scripts" / script), *args],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            env=merged,
        )

    def test_install_uninstall_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d) / "home"
            bindir = Path(d) / "bin"
            rcfile = Path(d) / ".zshrc"
            env = {
                "CODEX_TOKEN_SAVER_HOME": str(home),
                "CODEX_TOKEN_SAVER_BIN_DIR": str(bindir),
                "CODEX_HOME": str(Path(d) / "codex-home"),
                "SHELL_RC_FILE": str(rcfile),
            }
            skill = Path(env["CODEX_HOME"]) / "skills" / "token-trans"
            first = self.run_script("install.sh", env=env)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = self.run_script("install.sh", env=env)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertTrue((bindir / "codex-ts").is_symlink())
            self.assertTrue((skill / "SKILL.md").exists())
            self.assertTrue((skill / "agents" / "openai.yaml").exists())
            rc_text = rcfile.read_text(encoding="utf-8")
            self.assertIn("codex-token-saver managed block", rc_text)
            self.assertIn(str(bindir), rc_text)
            dry = self.run_script("uninstall.sh", "--dry-run", env=env)
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertTrue((bindir / "codex-ts").exists())
            self.assertTrue((skill / "SKILL.md").exists())
            self.assertIn("codex-token-saver managed block", rcfile.read_text(encoding="utf-8"))
            uninstall = self.run_script("uninstall.sh", env=env)
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            self.assertFalse((bindir / "codex-ts").exists())
            self.assertFalse((skill / "SKILL.md").exists())
            self.assertTrue((home / "config.toml").exists())
            self.assertNotIn("codex-token-saver managed block", rcfile.read_text(encoding="utf-8"))

    def test_install_refuses_unmanaged_shim(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d) / "home"
            bindir = Path(d) / "bin"
            bindir.mkdir()
            shim = bindir / "codex-ts"
            shim.write_text("mine", encoding="utf-8")
            env = {
                "CODEX_TOKEN_SAVER_HOME": str(home),
                "CODEX_TOKEN_SAVER_BIN_DIR": str(bindir),
                "SHELL_RC_FILE": str(Path(d) / ".zshrc"),
            }
            result = self.run_script("install.sh", env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing to overwrite unmanaged file", result.stderr)

    def test_install_no_skill(self):
        with tempfile.TemporaryDirectory() as d:
            env = {
                "CODEX_TOKEN_SAVER_HOME": str(Path(d) / "home"),
                "CODEX_TOKEN_SAVER_BIN_DIR": str(Path(d) / "bin"),
                "CODEX_HOME": str(Path(d) / "codex-home"),
                "SHELL_RC_FILE": str(Path(d) / ".zshrc"),
            }
            result = self.run_script("install.sh", "--no-skill", env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            skill = Path(env["CODEX_HOME"]) / "skills" / "token-trans"
            self.assertFalse((skill / "SKILL.md").exists())
            manifest = Path(env["CODEX_TOKEN_SAVER_HOME"]) / "install-manifest.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["codex_skill_targets"], [])

    def test_install_skill_only(self):
        with tempfile.TemporaryDirectory() as d:
            env = {
                "CODEX_TOKEN_SAVER_HOME": str(Path(d) / "home"),
                "CODEX_TOKEN_SAVER_BIN_DIR": str(Path(d) / "bin"),
                "CODEX_HOME": str(Path(d) / "codex-home"),
                "SHELL_RC_FILE": str(Path(d) / ".zshrc"),
            }
            result = self.run_script("install.sh", "--skill-only", env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            skill = Path(env["CODEX_HOME"]) / "skills" / "token-trans"
            self.assertTrue((skill / "SKILL.md").exists())
            self.assertFalse((Path(env["CODEX_TOKEN_SAVER_BIN_DIR"]) / "codex-ts").exists())
            self.assertFalse((Path(env["CODEX_TOKEN_SAVER_HOME"]) / "config.toml").exists())
            merged = os.environ.copy()
            merged.update(env)
            doctor = subprocess.run(
                ["bash", str(Path(env["CODEX_TOKEN_SAVER_HOME"]) / "scripts" / "doctor.sh")],
                text=True,
                capture_output=True,
                env=merged,
            )
            self.assertEqual(doctor.returncode, 0, doctor.stderr)
            self.assertIn("Wrapper: not installed", doctor.stdout)
            self.assertIn("Token Trans skill: installed", doctor.stdout)


if __name__ == "__main__":
    unittest.main()

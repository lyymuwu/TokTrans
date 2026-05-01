#!/usr/bin/env python3
"""Generate the visible-token benchmark table used in docs/benchmark.md.

This intentionally uses the same rough estimator as the runtime wrapper. It is
not a billing oracle; it is a reproducible way to compare prompt shapes.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from token_saver import rough_token_estimate  # noqa: E402


PROMPTS = [
    (
        "Chinese",
        "medium",
        "请帮我检查这个仓库为什么测试失败，并尽量只修改必要的文件。",
        "Please inspect why the tests in this repository are failing, and modify only the necessary files.",
    ),
    (
        "Japanese",
        "medium",
        "このリポジトリのテストが失敗する理由を調べ、必要なファイルだけを修正してください。",
        "Please inspect why the tests in this repository are failing, and modify only the necessary files.",
    ),
    (
        "Korean",
        "medium",
        "이 저장소의 테스트가 실패하는 이유를 확인하고 필요한 파일만 수정해 주세요.",
        "Please inspect why the tests in this repository are failing, and modify only the necessary files.",
    ),
    (
        "Thai",
        "medium",
        "ช่วยตรวจสอบว่าทำไมการทดสอบของโปรเจกต์นี้จึงล้มเหลว และแก้เฉพาะไฟล์ที่จำเป็น",
        "Please inspect why the tests in this repository are failing, and modify only the necessary files.",
    ),
    (
        "Hindi",
        "medium",
        "कृपया जाँचें कि इस रिपॉज़िटरी के टेस्ट क्यों असफल हो रहे हैं और केवल ज़रूरी फ़ाइलें बदलें।",
        "Please inspect why the tests in this repository are failing, and modify only the necessary files.",
    ),
    (
        "Arabic",
        "medium",
        "يرجى فحص سبب فشل اختبارات هذا المستودع وتعديل الملفات الضرورية فقط.",
        "Please inspect why the tests in this repository are failing, and modify only the necessary files.",
    ),
    (
        "Spanish",
        "medium",
        "Por favor revisa por que fallan las pruebas de este repositorio y modifica solo los archivos necesarios.",
        "Please inspect why the tests in this repository are failing, and modify only the necessary files.",
    ),
    (
        "French",
        "medium",
        "Veuillez verifier pourquoi les tests de ce depot echouent et ne modifier que les fichiers necessaires.",
        "Please inspect why the tests in this repository are failing, and modify only the necessary files.",
    ),
]


def main() -> int:
    print("| Language | Task | Original visible tokens | Translated visible tokens | Delta |")
    print("|---|---|---:|---:|---:|")
    for language, task, original, english in PROMPTS:
        before = rough_token_estimate(original)
        after = rough_token_estimate(english)
        delta = after - before
        print(f"| {language} | {task} | {before} | {after} | {delta:+d} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

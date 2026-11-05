"""방식별 왕복 시험 + 지표 비교.

    python3 research/hangul-encoding/bench.py [--bip39 path/to/korean.txt]

BIP39 한국어 목록은 저장소에 넣지 않았다. 비교하려면
https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/korean.txt
를 받아서 경로를 넘긴다.
"""

from __future__ import annotations

import argparse
import base64
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hangul_codec import (  # noqa: E402
    CHO, JONG, JUNG, Base11172x3, SentenceScheme, TableScheme, all_schemes,
    alphabet_from_words, bytes_to_bits, compose, decompose, keystrokes, nfc, pron_key,
)

ROOT = Path(__file__).resolve().parents[2]


def roundtrip(schemes, rng):
    lengths = list(range(0, 130)) + [rng.randrange(130, 2000) for _ in range(200)]
    for s in schemes:
        for n in lengths:
            bits = "".join(rng.choice("01") for _ in range(n))
            text = s.encode(bits)
            assert s.decode(text) == bits, (s.name, n, bits, text)
            # NFD로 망가뜨려도 복호되어야 한다
            import unicodedata
            assert s.decode(unicodedata.normalize("NFD", text)) == bits
    print(f"왕복 시험 통과: {len(schemes)}개 방식 × {len(lengths)}개 길이 (NFD 입력 포함)\n")


def word_key(w: str) -> str:
    return "".join(pron_key(c) for c in w)


def typo_survival(scheme) -> float:
    """기호 하나에서 자모 하나를 같은 자리의 다른 자모로 바꿨을 때
    여전히 '유효한 다른 기호'가 되는 비율 = 오류를 못 알아챌 확률."""
    if isinstance(scheme, Base11172x3):
        return 1.0  # 모든 음절이 유효
    alphabet = scheme.alphabet if isinstance(scheme, TableScheme) else scheme.words
    key = scheme.key if isinstance(scheme, TableScheme) else (lambda x: x)
    valid = {key(a) for a in alphabet}
    hit = total = 0
    for a in alphabet:
        for pos, ch in enumerate(a):
            c, v, t = decompose(ch)
            variants = ([compose(x, v, t) for x in CHO if x != c]
                        + [compose(c, x, t) for x in JUNG if x != v]
                        + [compose(c, v, x) for x in JONG if x != t])
            for var in variants:
                b = a[:pos] + var + a[pos + 1:]
                k = key(b)
                if k == key(a):
                    continue  # 발음상 같은 기호로 되돌아옴(오류가 아님)
                total += 1
                hit += k in valid
    return hit / total


def spoken_ambiguity(scheme) -> float:
    """기호표 중 발음(단독 발음 모델)이 다른 기호와 겹치는 비율."""
    if isinstance(scheme, Base11172x3):
        alphabet = [chr(0xAC00 + i) for i in range(11172)]
        key = pron_key
    elif isinstance(scheme, SentenceScheme):
        alphabet, key = scheme.words, word_key
    else:
        alphabet = scheme.alphabet
        key = pron_key if scheme.sep == "" else word_key
        if scheme.key is pron_key:
            return 0.0  # 복호 자체가 발음 키로 이루어짐
    from collections import Counter
    cnt = Counter(key(a) for a in alphabet)
    return sum(1 for a in alphabet if cnt[key(a)] > 1) / len(alphabet)


def metrics(schemes, nbits, rng):
    bits = "".join(rng.choice("01") for _ in range(nbits))
    raw = int(bits, 2).to_bytes(nbits // 8, "big")
    rows = []
    for name, text in [("hex (참고)", raw.hex()),
                       ("base64 (참고)", base64.b64encode(raw).decode())]:
        k = len(text) + sum(c.isupper() for c in text)
        rows.append((name, len(text), len(text), len(text.encode()), k, sum(c.isupper() for c in text), None, None))
    for s in schemes:
        text = s.encode(bits)
        k, sh = keystrokes(text)
        nsym = len(s.symbols(bits))
        rows.append((s.name, nsym, len(text), len(text.encode()), k, sh,
                     spoken_ambiguity(s), typo_survival(s)))
    print(f"### 입력 {nbits}비트\n")
    print("| 방식 | 기호 수 | 글자 수(공백 포함) | UTF-8 바이트 | 두벌식 타수 | 그중 Shift | 비트/글자 | 발음 겹침 | 자모 오타 미검출 |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for name, nsym, nch, nb, k, sh, amb, typo in rows:
        amb_s = "-" if amb is None else f"{amb:.1%}"
        typo_s = "-" if typo is None else f"{typo:.1%}"
        print(f"| {name} | {nsym} | {nch} | {nb} | {k} | {sh} | {nbits / nch:.2f} | {amb_s} | {typo_s} |")
    print()


def examples(schemes):
    sample = bytes.fromhex("00112233445566778899aabbccddeeff")
    bits = bytes_to_bits(sample)
    print("### 예시: 128비트 `00112233445566778899aabbccddeeff`\n")
    for s in schemes:
        print(f"- **{s.name}**: {s.encode(bits)}")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bip39", type=Path)
    ap.add_argument("--dump-alphabets", type=Path, help="기호표를 이 디렉터리에 저장")
    args = ap.parse_args()

    elements = (ROOT / "source/hangul/elements").read_text(encoding="utf-8").splitlines()
    wordlist = alphabet_from_words(elements)
    bip39 = None
    if args.bip39:
        raw = args.bip39.read_text(encoding="utf-8").split()
        nfd = sum(1 for w in raw if w != nfc(w))
        print(f"BIP39 korean.txt: {len(raw)}단어, 그중 NFD로 저장된 단어 {nfd}개\n")
        bip39 = raw

    schemes = all_schemes(wordlist, bip39)
    rng = random.Random(20261105)
    roundtrip(schemes, rng)
    for n in (128, 256, 1024):
        metrics(schemes, n, rng)
    examples(schemes)

    print("### 이론값\n")
    for name, n in [("전체 음절 11172", 11172), ("KS X 1001 완성형 2350", 2350),
                    ("BaseHangul 1024(+4)", 1024), ("받침 없는 음절 399", 399),
                    ("받침 없고 발음 구별 276", 276)]:
        print(f"- {name}자: log2 = {math.log2(n):.3f} 비트/자")
    for k in range(1, 9):
        b = math.floor(k * math.log2(11172))
        print(f"  - 11172^{k}: {b}비트를 {k}자에 → {b / k:.3f} 비트/자")

    if args.dump_alphabets:
        args.dump_alphabets.mkdir(parents=True, exist_ok=True)
        for s in schemes:
            if isinstance(s, TableScheme) and len(s.alphabet) <= 4096:
                fn = args.dump_alphabets / (s.name.split(" ")[0] + ".txt")
                fn.write_text("\n".join(f"{i:04x} {a}" for i, a in enumerate(s.alphabet)) + "\n",
                              encoding="utf-8")
                print(f"기호표 저장: {fn}")


if __name__ == "__main__":
    main()

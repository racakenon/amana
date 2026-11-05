"""임의 비트열 <-> 한국어 텍스트 인코딩 실험용 프로토타입.

모든 방식은 '0'/'1' 문자열을 받아 한국어 문자열을 돌려주고(encode),
그 반대(decode)를 한다. 비트 길이가 8의 배수일 필요는 없다.

길이 처리는 모든 방식에 공통으로 "1 뒤에 0 채움(1-0* padding)"을 쓴다.
입력 끝에 '1'을 하나 붙이고 단위 길이까지 '0'으로 채운 뒤, 복호할 때
끝의 0들과 마지막 1을 지운다. 길이 필드 없이 임의 길이의 비트열을
되살릴 수 있고, 덧붙는 비용은 최대 한 단위다.

연구용 코드라서 속도보다 읽기 쉬운 쪽을 골랐다.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# 한글 음절 구조
# ---------------------------------------------------------------------------

CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"  # 19
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"  # 21
JONG = ["", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ",
        "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]  # 28

SBASE, SCOUNT = 0xAC00, 11172


def compose(cho: str, jung: str, jong: str = "") -> str:
    return chr(SBASE + (CHO.index(cho) * 21 + JUNG.index(jung)) * 28 + JONG.index(jong))


def decompose(syl: str) -> tuple[str, str, str]:
    o = ord(syl) - SBASE
    if not 0 <= o < SCOUNT:
        raise ValueError(f"한글 음절이 아님: {syl!r}")
    return CHO[o // 588], JUNG[(o % 588) // 28], JONG[o % 28]


def has_batchim(word: str) -> bool:
    return decompose(word[-1])[2] != ""


def nfc(s: str) -> str:
    """복호 전에 반드시 NFC로 맞춘다 (macOS 파일 이름, BIP39 원본 등은 NFD)."""
    return unicodedata.normalize("NFC", s)


# ---------------------------------------------------------------------------
# 두벌식 타자 비용
# ---------------------------------------------------------------------------

SHIFT_JAMO = set("ㄲㄸㅃㅆㅉㅒㅖ")
TWO_KEY_JUNG = set("ㅘㅙㅚㅝㅞㅟㅢ")
TWO_KEY_JONG = set(["ㄳ", "ㄵ", "ㄶ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅄ"])


def keystrokes(text: str) -> tuple[int, int]:
    """(글쇠 수, 그중 Shift가 필요한 글쇠 수). 한글 아닌 글자는 1타로 센다."""
    keys = shifts = 0
    for ch in text:
        try:
            c, v, t = decompose(ch)
        except ValueError:
            keys += 1
            continue
        keys += 1 + (2 if v in TWO_KEY_JUNG else 1)
        shifts += (c in SHIFT_JAMO) + (v in "ㅒㅖ") + (v == "ㅙ") + (v == "ㅞ")
        if t:
            keys += 2 if t in TWO_KEY_JONG else 1
            shifts += t in ("ㄲ", "ㅆ")
    return keys, shifts


# ---------------------------------------------------------------------------
# 발음 모델: 소리 내어 불러 줄 때 구별되지 않는 음절을 같은 키로 묶는다.
# (단독 발음 기준. 음절 사이 연음/비음화는 따로 다룬다.)
# ---------------------------------------------------------------------------

JONG_REP = {  # 받침의 대표음 7개 (표준 발음법 제8~11항 근사)
    "": "", "ㄱ": "ㄱ", "ㄲ": "ㄱ", "ㅋ": "ㄱ", "ㄳ": "ㄱ", "ㄺ": "ㄱ",
    "ㄴ": "ㄴ", "ㄵ": "ㄴ", "ㄶ": "ㄴ",
    "ㄷ": "ㄷ", "ㅅ": "ㄷ", "ㅆ": "ㄷ", "ㅈ": "ㄷ", "ㅊ": "ㄷ", "ㅌ": "ㄷ", "ㅎ": "ㄷ",
    "ㄹ": "ㄹ", "ㄼ": "ㄹ", "ㄽ": "ㄹ", "ㄾ": "ㄹ", "ㅀ": "ㄹ",
    "ㅁ": "ㅁ", "ㄻ": "ㅁ",
    "ㅂ": "ㅂ", "ㅍ": "ㅂ", "ㅄ": "ㅂ", "ㄿ": "ㅂ",
    "ㅇ": "ㅇ",
}
PALATAL = set("ㅈㅉㅊ")
Y_TO_PLAIN = {"ㅑ": "ㅏ", "ㅕ": "ㅓ", "ㅛ": "ㅗ", "ㅠ": "ㅜ", "ㅒ": "ㅐ", "ㅖ": "ㅔ"}


def pron_key(syl: str) -> str:
    c, v, t = decompose(syl)
    # 실제 발음에서 사실상 합쳐진 모음
    v = {"ㅔ": "ㅐ", "ㅖ": "ㅒ", "ㅙ": "ㅚ", "ㅞ": "ㅚ"}.get(v, v)
    if c in PALATAL:  # 져[저], 쳐[처], 죠[조] ...
        v = Y_TO_PLAIN.get(v, v)
    if c not in ("ㅇ", "ㄹ") and v == "ㅒ":  # 계[게] (제5항 다만 2)
        v = "ㅐ"
    if c != "ㅇ" and v == "ㅢ":  # 희[히] (제5항 다만 3)
        v = "ㅣ"
    return c + v + JONG_REP[t]


# ---------------------------------------------------------------------------
# 비트 유틸
# ---------------------------------------------------------------------------

def pad_bits(bits: str, unit: int) -> str:
    bits += "1"
    return bits + "0" * (-len(bits) % unit)


def unpad_bits(bits: str) -> str:
    i = bits.rfind("1")
    if i < 0:
        raise ValueError("종료 표지(1)가 없음")
    return bits[:i]


def bytes_to_bits(b: bytes) -> str:
    return "".join(f"{x:08b}" for x in b)


def bits_to_bytes(bits: str) -> bytes:
    assert len(bits) % 8 == 0
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


# ---------------------------------------------------------------------------
# 방식들
# ---------------------------------------------------------------------------

@dataclass
class Scheme:
    name: str
    unit: int  # 기호 하나가 싣는 비트 수
    sep: str = ""

    def symbols(self, bits: str) -> list[str]:
        raise NotImplementedError

    def encode(self, bits: str) -> str:
        return self.sep.join(self.symbols(bits))

    def decode(self, text: str) -> str:
        raise NotImplementedError


class TableScheme(Scheme):
    """기호표(alphabet)에서 unit 비트씩 꺼내 쓰는 단순한 방식."""

    def __init__(self, name: str, alphabet: list[str], sep: str = "", key=None):
        unit = len(alphabet).bit_length() - 1
        assert len(alphabet) == 1 << unit, f"{name}: 기호 수 {len(alphabet)}는 2의 거듭제곱이 아님"
        assert len(set(alphabet)) == len(alphabet)
        super().__init__(name, unit, sep)
        self.alphabet = alphabet
        self.key = key or (lambda s: s)
        self.index = {}
        for i, a in enumerate(alphabet):
            k = self.key(a)
            assert k not in self.index, f"{name}: {a}와 {alphabet[self.index[k]]}의 키가 겹침"
            self.index[k] = i

    def symbols(self, bits):
        p = pad_bits(bits, self.unit)
        return [self.alphabet[int(p[i:i + self.unit], 2)] for i in range(0, len(p), self.unit)]

    def split(self, text: str) -> list[str]:
        text = nfc(text)
        return text.split() if self.sep else [c for c in text if not c.isspace()]

    def decode(self, text):
        out = []
        for tok in self.split(text):
            try:
                out.append(format(self.index[self.key(tok)], f"0{self.unit}b"))
            except KeyError:
                raise ValueError(f"{self.name}: 알 수 없는 기호 {tok!r}") from None
        return unpad_bits("".join(out))


class Base11172x3(Scheme):
    """40비트(5바이트) -> 음절 3자. 11172^3 ≈ 2^40.34.

    마지막 덩어리는 길이에 따라 1자(13비트)/2자(26비트)/3자(40비트)로 쓴다.
    전체 글자 수 mod 3 으로 마지막 덩어리의 크기를 알 수 있다.
    """

    def __init__(self):
        super().__init__("base11172×3", 0)
        self.unit = 40 / 3

    def symbols(self, bits):
        bits += "1"
        out = []
        for i in range(0, len(bits), 40):
            chunk = bits[i:i + 40]
            if i + 40 < len(bits) or len(chunk) > 26:
                width, n = 40, 3
            elif len(chunk) > 13:
                width, n = 26, 2
            else:
                width, n = 13, 1
            v = int(chunk.ljust(width, "0"), 2)
            digits = []
            for _ in range(n):
                v, d = divmod(v, SCOUNT)
                digits.append(chr(SBASE + d))
            out += reversed(digits)
        return out

    def decode(self, text):
        chars = [c for c in nfc(text) if not c.isspace()]
        out = []
        for i in range(0, len(chars), 3):
            group = chars[i:i + 3]
            width = {1: 13, 2: 26, 3: 40}[len(group)]
            v = 0
            for c in group:
                d = ord(c) - SBASE
                if not 0 <= d < SCOUNT:
                    raise ValueError(f"한글 음절이 아님: {c!r}")
                v = v * SCOUNT + d
            if v >> width:
                raise ValueError("범위를 벗어난 값 (손상된 입력)")
            out.append(format(v, f"0{width}b"))
        return unpad_bits("".join(out))


@dataclass
class SentenceScheme(Scheme):
    """명사 2048개 + 조사 틀로 '문장처럼' 보이게 만든다. 단어당 11비트.

    틀: "A의 B{이/가} C에서 D{을/를} 본다."  (명사 4개 = 44비트)
    조사는 앞 단어의 받침으로 정해지므로 정보는 없지만 읽기 쉽게 해 주고,
    복호할 때 받침과 조사가 맞는지 확인하면 오타를 일부 잡을 수 있다.
    """

    words: list[str] = field(default_factory=list)
    verb: str = "본다."

    def __post_init__(self):
        assert len(self.words) == 2048
        self.index = {w: i for i, w in enumerate(self.words)}

    @staticmethod
    def particle(word: str, slot: int) -> str:
        b = has_batchim(word)
        return ["의", "이" if b else "가", "에서", "을" if b else "를"][slot]

    def symbols(self, bits):
        p = pad_bits(bits, 11)
        toks = []
        for n, i in enumerate(range(0, len(p), 11)):
            w = self.words[int(p[i:i + 11], 2)]
            slot = n % 4
            toks.append(w + self.particle(w, slot))
            if slot == 3:
                toks.append(self.verb)
        return toks

    def encode(self, bits):
        return " ".join(self.symbols(bits))

    def decode(self, text):
        toks = [t for t in nfc(text).split() if t != self.verb]
        out = []
        for n, tok in enumerate(toks):
            slot = n % 4
            cut = 2 if slot == 2 else 1
            w, par = tok[:-cut], tok[-cut:]
            if w not in self.index:
                raise ValueError(f"사전에 없는 단어: {w!r}")
            if par != self.particle(w, slot):
                raise ValueError(f"조사 불일치: {tok!r} (오타 의심)")
            out.append(format(self.index[w], "011b"))
        return unpad_bits("".join(out))


# ---------------------------------------------------------------------------
# 기호표 만들기
# ---------------------------------------------------------------------------

def alphabet_b13() -> list[str]:
    """U+AC00(가)부터 연속된 8192자. 13비트/자. 비트 연산만으로 끝난다."""
    return [chr(SBASE + i) for i in range(8192)]


HEX_CHO = list("ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㄲㄸ")
HEX_JUNG = list("ㅏㅐㅑㅓㅔㅕㅗㅘㅚㅛㅜㅝㅟㅠㅡㅣ")
HEX_JONG = ["", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "ㅆ"]


def alphabet_hex_jamo() -> list[str]:
    """초성·중성·종성이 각각 16진수 한 자리(4비트)씩. 음절 1자 = 16진수 3자리.

    표 없이도 자모 순서만 외우면 사람이 손으로 풀 수 있다.
    """
    return [compose(c, v, t) for c in HEX_CHO for v in HEX_JUNG for t in HEX_JONG]


def alphabet_spoken_byte() -> list[str]:
    """받침 없는 음절 256자 = 1바이트/자. 불러 주어도 헷갈리지 않게 고른다.

    1) 받침 없는 음절 19×21=399자를 pron_key로 묶는다 (276개 묶음).
    2) 묶음마다 대표 철자 하나(가장 치기 쉬운 것)를 고른다.
    3) 비용(Shift, 겹모음, 약해지기 쉬운 ㅎ)이 낮은 256개를 남긴다.
    받침이 없으니 음절 사이 연음·비음화·경음화가 생기지 않는다.
    """
    groups: dict[str, list[str]] = {}
    for c in CHO:
        for v in JUNG:
            s = compose(c, v)
            groups.setdefault(pron_key(s), []).append(s)

    def cost(s):
        c, v, _ = decompose(s)
        k, sh = keystrokes(s)
        return (2 * sh + (k - 2) + (1 if c == "ㅎ" else 0) + (1 if v == "ㅢ" else 0), s)

    reps = sorted((min(g, key=cost) for g in groups.values()), key=cost)
    return sorted(reps[:256])


def alphabet_from_words(words: list[str], size: int = 2048) -> list[str]:
    """단어 목록에서 size개를 고른다: NFC, 중복 제거, Shift 없는 것 우선,
    두 음절 우선(한 음절 단어는 조사·대명사와 헷갈린다), 두벌식 타수 적은 순."""
    ws = sorted({nfc(w.strip()) for w in words if w.strip()})
    ws = [w for w in ws if all(0 <= ord(c) - SBASE < SCOUNT for c in w)]
    ws.sort(key=lambda w: (keystrokes(w)[1] > 0, len(w) != 2, len(w), keystrokes(w)[0], w))
    assert len(ws) >= size, f"단어가 모자람: {len(ws)} < {size}"
    return sorted(ws[:size])


def all_schemes(wordlist: list[str], bip39: list[str] | None = None) -> list[Scheme]:
    schemes: list[Scheme] = [
        TableScheme("B13 (8192자 연속)", alphabet_b13()),
        Base11172x3(),
        TableScheme("자모 16진 (4+4+4)", alphabet_hex_jamo()),
        TableScheme("말하기 바이트 (받침 없음)", alphabet_spoken_byte(), key=pron_key),
        TableScheme("단어 11비트 (amana elements)", wordlist, sep=" "),
    ]
    if bip39:
        schemes.append(TableScheme("단어 11비트 (BIP39 korean)", [nfc(w) for w in bip39], sep=" "))
    schemes.append(SentenceScheme("문장 틀 (조사 포함)", 11, " ", wordlist))
    return schemes

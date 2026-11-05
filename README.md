# amana
korean word list generator and dicewere tool
Generate secure passphrases using diceware

## wordlist

```
Usage: wordlist [OPTIONS]

Options:
  -i, --input <input>    Word list path; if not given, uses the default wordlist
  -b <builtin>...        [possible values: all, cities, colors, countries, day-time, elements, mountains, numbers, rivers, spices, treasures]
  -o, --output <output>  Passphrase output path
  -d, --dice <dice>      Dice use for dicewere [default: 6]
  -n, --number <number>  Number of dice use for dicewere [default: 4]
  -m, --min <min>        Min length of a word [default: 1]
  -M, --max <max>        Max length of a word [default: 20]
  -u                     Remove uppercase jamo ㅃ,ㅉ,ㄸ,ㄲ,ㅆ,ㅒ,ㅖ
      --dubeol           use dubeolic encryption ㄱ-> r
  -h, --help             Print help
```
### usage

```
wordlist -b cities colors countries day-time mountains elements numbers rivers treasures | head  -n 10

1|1|1|1 가구
1|1|1|2 가능성
1|1|1|3 가르침
1|1|1|4 가리왕산
1|1|1|5 가사
1|1|1|6 가슴속
1|1|2|1 가요
1|1|2|2 가운데
1|1|2|3 가은산
1|1|2|4 가이아나
```
## diceware

```
Usage: diceware [OPTIONS]

Options:
  -i, --input <input>          Word list path; if not given, uses the default wordlist
  -b <builtin>                 [possible values: eff-large, eff-short1, eff-short2]
  -o, --output <output>        Passphrase output path
  -c, --count <count>          Number of words in the passphrase [default: 4]
  -d, --delimiter <delimiter>  Delimiter between words in the passphrase [default: -]
  -n, --numbers <numbers>      Number of passphrases to generate [default: 1]
  -h, --help                   Print help
Generate word list for dicewere
```

### usage

```
wordlist -b all -u -m 2 -M 4 -d 6 -n 5 -o wordlist.txt
diceware -i wordlist.txt -c 5 -n 10

큰잎냉이-갈쥐치-월악산-눈퉁바리-바위취
점박각시-왕관밤게-정신-돌마자-교재
별나나니-야생팬지-휴가-시로미-애먹파리
건너편-축제-갯보리-개담배-고사리새
체중-코피-아셀횟대-간부-포도
쇠칼새-책상-고지달재-물질적-귀상어
소황금-근원-승냥이-율호박-쇠박새
돌배나무-좀싱아-고려멸구-가시가지-무한천
두별잎벌-합리적-징비록-구름-쇠종다리
종려나무-휴가-콩알게-돈나무이-속담
```

## research

- [임의 비트열을 한국어로 인코딩하기](./research/hangul-encoding/README.md): 음절, 자모, 단어, 문장 기반 인코딩 7가지 비교

## Acknowledge

### wordlist

- [cities](./source/hangul/cities) is a list of korean cities
- [colors](./source/hangul/colors) is a list of korean traditional colors
- [countries](./source/hangul/countries) is a list of un members
- [day-time](./source/hangul/daytime) is a list of words related to time and day
- [numbers](./source/hangul/numbers) is a list of words related numbers and unit 
- [treasures](./source/hangul/treasures) is obtained from 대한민국의 국보, 한국의 유네스코 등재유산

- [elements](./source/hangul/elements) is obtained from  
[한국어 학습용 어휘 목록, 국립국어연구원](https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=71)

- [mountains](./source/hangul/mountains) is obtained from 
[100대명산 및 100대 명산 플러스 우리산 100 목록, 산림청](https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardArticle.do?bbsId=BBSMSTR_1069&mn=NKFS_06_09_01&nttId=3189160)

- [rivers](./source/hangul/rivers) is obtained from 
[국가하천, RIMGIS](https://www.river.go.kr/intro/https://species.nibr.go.kr/home/mainHome.do?cont_link=002&subMenu=002003&contCd=002003005&type=view&seq_no=123&group_cd=riverInfo.do)

- [spices](./source/hangul/spices) is obtained from 
[환경부 국립생물자원관 국가생물종목록](https://species.nibr.go.kr/home/mainHome.do?cont_link=002&subMenu=002003&contCd=002003005&type=view&seq_no=123&group_cd=)

### diceware

The sources of the default list are
[EFF's wordlists](https://www.eff.org/deeplinks/2016/07/new-wordlists-random-passphrases) 

- [eff-large](./source/eff_large_wordlist.txt) 
- [eff-short1](./source/eff_short_wordlist_1.txt)
- [eff-short1](./source/eff_short_wordlist_2_0.txt)

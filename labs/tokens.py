"""count_tokens(): 입력 토큰 어림값 (실습 02·04·09·12 공용).

규칙(단순한 추정이고 실제 토크나이저가 아니다):
- ASCII가 아닌 글자(한글·한자·기호 등)는 1자 = 1토큰
- ASCII 글자(영문·숫자·공백·문장부호)는 4자 = 1토큰 (올림)

실제 값은 모델의 토크나이저가 정한다. 실습 02는 이 추정치(input_tokens_est)와
`claude -p --output-format json`이 돌려준 usage 값(input_tokens_usage)을 나란히 적는다.
usage에는 Claude Code 자체 시스템 프롬프트도 들어 있어 추정치보다 크다.
"""
import math


def count_tokens(text: str) -> int:
    non_ascii = sum(1 for ch in text if ord(ch) > 127)
    ascii_n = len(text) - non_ascii
    return non_ascii + math.ceil(ascii_n / 4)


if __name__ == "__main__":
    import sys
    print(count_tokens(sys.stdin.read()))

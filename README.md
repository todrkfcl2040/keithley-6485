


# Keithley Demo Program

이 프로그램은 Keithley 장비(예: 6485, 2400 등)와 통신하여 시간에 따른 전기적 특성(Capacitance, Voltage, Current 등)을 실시간으로 시각화하는 PyQt 기반 도구입니다.

## 1. 가상 환경(vEnv) 설정

먼저 프로젝트 디렉토리(`keithley_demo`)에서 가상 환경을 설정합니다:

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

## 2. 의존성 설치

```bash
pip install -r requirements.txt
```

또는 수동으로:

```bash
pip install pyvisa pyqt5 matplotlib
```

## 3. 장비 연결 설정

### NI-MAX를 통한 포트 확인 방법

1. [NI-VISA 드라이버](https://www.ni.com/ko-kr/support/downloads/drivers/download.ni-visa.html) 설치
2. NI-MAX 실행 → 연결된 장비(GPIB 또는 USB-TMC)의 주소 확인

예시:
- GPIB 장비 (Keithley 6485): `GPIB0::22::INSTR`
- USB 장비 (Keithley 2110): `USB0::0x05E6::0x2110::8014482::INSTR`

### 코드 내 주소 변경 위치

`main.py` 상단의 다음 부분을 수정합니다:

```python
inst = rm.open_resource('GPIB0::22::INSTR')  # GPIB 장비 예시
```

연결된 장비 주소로 변경해 주세요.

## 4. 실행 방법

가상 환경이 활성화된 상태에서:

```bash
python main2.py
```

장비가 연결되지 않았을 경우, 자동으로 데모 모드로 전환되어 사인파 기반의 시뮬레이션 측정이 실행됩니다.

## 5. 측정 가능한 항목

- Capacitance (F)
- Resistance (Ω)
- Inductance (H)
- Conductance (S)
- Voltage (V)
- Current (A)

## 6. 사용법

- 왼쪽 리스트에서 측정 모드 선택
- Start 버튼으로 측정 시작
- Pause / Stop 버튼으로 측정 제어
- 그래프는 시간에 따른 실시간 데이터를 표시

데모 모드에서는 sin(t) 기반 가상 측정 데이터가 출력됩니다.# keithley-6485

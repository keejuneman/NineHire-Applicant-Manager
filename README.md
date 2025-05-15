# NineHire Applicant Manager

NineHire 지원자 관리 시스템은 채용 프로세스에서 지원자 정보를 효율적으로 관리할 수 있는 웹 애플리케이션입니다.

## 주요 기능

- 지원자 정보 조회 및 관리
- 커스텀 컬럼 생성 및 관리
- 지원자 데이터 필터링 및 정렬
- 설정 저장 및 불러오기
- 지원자 이력서 링크 제공

## 기술 스택

- Backend: Python Flask
- Frontend: HTML, CSS, JavaScript
- Database: SQLite
- API: NineHire API

## 설치 방법

1. 저장소 클론
```bash
git clone [repository-url]
cd ninehire_web
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가합니다:
```
NINEHIRE_API_KEY=your_api_key_here
```

5. 애플리케이션 실행
```bash
python app.py
```

## 사용 방법

1. 웹 브라우저에서 `http://localhost:5000` 접속
2. Job ID 입력
3. 원하는 컬럼 선택 및 커스텀 컬럼 생성
4. 'Data Load' 버튼 클릭하여 지원자 데이터 로드
5. 지원자 정보 확인 및 관리

## 설정 저장/불러오기

- SAVE: 현재 설정을 저장
- LOAD: 저장된 설정 불러오기
- DELETE: 저장된 설정 삭제

## 주의사항

- API 키는 반드시 안전하게 보관해야 합니다.
- 데이터베이스 파일(`settings.db`)은 자동으로 생성됩니다.
- 환경 변수 파일(`.env`)은 Git에 포함되지 않습니다.

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 
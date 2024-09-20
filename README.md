# 뉴스 수집 및 마크다운 생성 시스템

이 프로젝트는 RSS 피드에서 뉴스를 수집하고, 수집된 뉴스를 기반으로 마크다운 페이지를 생성하는 시스템입니다.

## 구성 요소

1. `rssCrawler.py`: RSS 피드에서 뉴스를 수집하는 스크립트
2. `createMD.py`: 수집된 뉴스를 기반으로 마크다운 페이지를 생성하는 스크립트

## 설치 방법

1. 이 저장소를 클론합니다:
```
git clone https://github.com/yourusername/news-collector.git
cd news-collector
```


2. 필요한 Python 패키지를 설치합니다:
```
pip install feedparser requests beautifulsoup4
```


## 사용 방법

### 1. RSS 크롤러 (rssCrawler.py)

이 스크립트는 지정된 RSS 피드에서 뉴스를 수집합니다.

실행 방법:
```
python rssCrawler.py
```


주요 기능:
- RSS 피드에서 최신 뉴스 기사를 가져옵니다.
- 각 기사의 제목, URL, 요약, 본문 내용을 추출합니다.
- 추출된 정보를 JSON 파일로 저장합니다.

설정:
- `RSS_FEEDS`: RSS 피드 URL 목록을 이 변수에 추가하여 크롤링할 소스를 지정합니다.

### 2. 마크다운 생성기 (createMD.py)

이 스크립트는 수집된 뉴스 데이터를 기반으로 마크다운 형식의 페이지를 생성합니다.

실행 방법:
```
python createMD.py
```


주요 기능:
- JSON 파일에서 뉴스 데이터를 읽어옵니다.
- 뉴스 기사를 날짜순으로 정렬합니다.
- 각 기사에 대한 마크다운 형식의 요약을 생성합니다.
- 생성된 마크다운을 파일로 저장합니다.

설정:
- `OUTPUT_FILE`: 생성될 마크다운 파일의 이름을 지정합니다.

## 주의사항

- RSS 피드 URL이 유효한지 확인하세요.
- 크롤링 시 해당 웹사이트의 이용 약관을 준수하세요.
- 생성된 마크다운 파일은 정기적으로 백업하는 것이 좋습니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.




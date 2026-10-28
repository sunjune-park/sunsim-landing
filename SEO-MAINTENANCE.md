# SSBP 정적 사이트 관리

Python 표준 라이브러리로 정적 HTML을 생성합니다. Netlify는 `python3 scripts/insights.py build` 실행 후 `dist/`를 배포합니다. 별도 CMS·데이터베이스·패키지 설치는 필요하지 않습니다. 상세 운영 방법은 `CONTENT-GUIDE.md`를 확인합니다.

## 공통 메뉴

`partials/header.html`과 `partials/footer.html`을 수정하면 빌드 시 모든 배포 페이지에 적용됩니다. 기존 기본 페이지 소스에도 반영하려면 `python3 scripts/sync-layout.py`를 실행합니다. 링크는 클라이언트 JavaScript가 아닌 HTML에 포함됩니다.

## Insight 추가

1. `content/insights/<slug>.md`에 제목·요약·분류·본문을 작성합니다. 파일명과 slug는 같습니다.
2. 초안은 `status: draft`, 공개할 글은 `status: published`와 실제 `published` 날짜를 지정합니다.
3. `python3 scripts/test_insights.py`와 `python3 scripts/insights.py build`로 점검합니다.
4. 변경한 원고를 커밋합니다. 목록·상세페이지·홈페이지 최신 글·사이트맵은 배포 시 자동 생성됩니다.
5. 기존 URL과 최초 게시일은 유지합니다. 글을 수정하면 `modified`를 실제 수정일로 기록합니다. 실제 작성한 내용만 게시하고 원문 자료·사례 실적을 확인합니다.

대표 주소는 `https://ssbp.co.kr/`이며 서비스와 콘텐츠 주소는 끝에 `/`를 사용합니다. 이전 주소의 301 연결은 `_redirects`에서 관리합니다. 기존 도메인 연결 규칙, favicon, 공식 로고와 홈페이지 Organization의 sameAs는 유지합니다.

## 문의 기능

`contact/index.html`의 폼과 Google Apps Script 전송 로직은 이전 `contact.html`에서 보존했습니다. 외부 전송을 점검할 때는 실제 고객정보나 임의의 테스트 문의를 운영 데이터에 보내지 않도록 하며, 별도 확인 가능한 테스트 환경에서 수행합니다.

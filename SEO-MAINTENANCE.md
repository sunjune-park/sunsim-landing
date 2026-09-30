# SSBP 정적 사이트 관리

배포 파일은 각 디렉터리의 `index.html`입니다. 별도 프레임워크나 빌드 서버가 필요하지 않습니다.

## 공통 메뉴

`partials/header.html`과 `partials/footer.html`을 수정한 뒤 저장소 루트에서 `python3 scripts/sync-layout.py`를 실행합니다. 생성된 HTML도 함께 커밋합니다. 링크는 클라이언트 JavaScript가 아닌 HTML에 포함됩니다.

## Insight 추가

1. 기존 `insight/<slug>/index.html`을 참고해 새 글을 작성합니다.
2. 제목, description, canonical, Open Graph, 게시일, 본문, breadcrumb 및 BreadcrumbList를 새 글에 맞게 변경합니다.
3. 관련 글 링크와 `insight/index.html` 목록을 갱신합니다.
4. `sitemap.xml`에 최종 공개 URL을 추가합니다.
5. 실제 작성한 내용만 게시하고 원문 자료·게시일을 확인합니다.

대표 주소는 `https://ssbp.co.kr/`이며 서비스와 콘텐츠 주소는 끝에 `/`를 사용합니다. 이전 주소의 301 연결은 `_redirects`에서 관리합니다. 기존 도메인 연결 규칙, favicon, 공식 로고와 홈페이지 Organization의 sameAs는 유지합니다.

## 문의 기능

`contact/index.html`의 폼과 Google Apps Script 전송 로직은 이전 `contact.html`에서 보존했습니다. 외부 전송을 점검할 때는 실제 고객정보나 임의의 테스트 문의를 운영 데이터에 보내지 않도록 하며, 별도 확인 가능한 테스트 환경에서 수행합니다.

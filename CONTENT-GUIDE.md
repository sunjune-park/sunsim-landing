# Insight 운영 방법

## 원고만 수정하고 배포

원고는 `content/insights/<slug>.md`, 디자인은 `templates/`와 `assets/style.css`에서 관리합니다.
글의 개별 주소는 `/insight/<slug>/`로 유지됩니다.
Netlify는 커밋을 받으면 `python3 scripts/insights.py build`를 실행하고 `dist/`만 배포합니다.
글 상세페이지, 목록, 홈페이지 최신 글 3개, 사이트맵과 공개 글 목록 JSON이 함께 생성됩니다.
작성 중인 원고, 템플릿, 관리 스크립트는 사이트 배포물에 포함되지 않습니다. 저장소 자체는 공개 저장소이므로 비공개 고객자료는 원고 파일에 넣지 않습니다.

## 새 원고 형식

파일 이름과 slug를 동일하게 작성합니다. 아래는 예시이며 실제 큐에 자동 추가되지 않습니다.

```text
+++
{
  "slug": "new-article",
  "title": "글 제목",
  "description": "검색 설명과 글 상단 요약",
  "category": "기업인증",
  "status": "draft",
  "format": "markdown"
}
+++
첫 문단을 작성합니다.

## 소제목

내용을 작성합니다.

- 점검 항목
- 두 번째 항목

[상담 문의](https://ssbp.co.kr/contact/)
```

지원 문법은 문단, `##` 또는 `###` 소제목, 한 단계 글머리·번호 목록, 파이프 표,
링크, 굵게, 기울임, 인라인 코드입니다. 전체 CommonMark를 구현한 편집기가 아니므로
중첩 목록·코드 블록·이미지 삽입·HTML은 사용하지 않습니다. 표 구분선은 셀마다 `---`입니다.
표는 모바일에서 가로로 스크롤됩니다. 문서 제목은 metadata에서 자동 생성하므로 본문에 `#` 제목은 넣지 않습니다.

기존 10편은 시각적·내용적 손실 없이 옮기기 위해 `format: html`로 본문 조각을 보존했습니다.
기존 글도 제목·설명·분류·날짜·공통 디자인은 같은 생성기를 사용합니다.

## 공개와 예약의 구분

- `status: draft`: 빌드가 발생해도 공개하지 않습니다.
- `status: published`, `published: YYYY-MM-DD`: 해당 날짜가 한국시간 오늘 이하인 경우 공개합니다.
- 수정할 때 `modified`를 실제 수정일로 추가하고 최초 `published`는 유지합니다.
- 미래 날짜만 적는 것은 예약 실행이 아닙니다. 날짜가 되어도 배포가 실행되어야 공개됩니다.
- 이번 15편에는 `queue: 1`부터 `15`까지 부여했습니다. 일반 새 초안에는 queue를 자동 부여하지 않습니다.

## 이번 15편 게시 작업

매일 낮 12시(Asia/Seoul)에 ChatGPT 예약 작업이 다음 명령을 실행하도록 설정되어 있습니다.

```bash
python3 scripts/insights.py publish --limit 3 --apply
python3 scripts/test_insights.py
```

publish 명령은 순서대로 초안 최대 3편의 상태와 실제 공개일을 기록하고 빌드를 검증합니다.
같은 한국 날짜로 재실행하면 `published_batch`를 확인해 합계 3편을 넘지 않습니다.
검증 실패 시 변경한 원고 상태를 복구하고 기존 dist를 유지합니다.
그 후 **변경된 원고를 커밋·push해야** Netlify 배포가 시작됩니다. 명령만 실행하고 커밋하지 않으면 운영 사이트에 반영되지 않습니다.
이미 커밋된 배치를 재시도할 때는 새 글을 꺼내지 말고 해당 배포 상태부터 확인합니다.
배포가 완료된 것과 검색엔진이 새 글을 색인한 것은 별개입니다.

## 점검 및 배포

```bash
python3 scripts/insights.py list
python3 scripts/test_insights.py
python3 scripts/insights.py build
```

빌드 결과는 `dist/`에만 생성되며 Git에 넣지 않습니다.
신규 글은 원고 파일만 커밋하면 되고 목록과 사이트맵은 직접 편집하지 않습니다.
게시 후 `/insight/feed.json`과 개별 글을 확인합니다. feed에는 공개된 글만 포함됩니다.

## 디자인과 기존 페이지

- 글/목록 디자인: `templates/insight-article.html`, `templates/insight-index.html`
- 메뉴/푸터: `partials/header.html`, `partials/footer.html`
- 기본 서비스 페이지: 기존 각 디렉터리의 `index.html`
- 사이트맵에 포함할 기본 페이지: `content/site-pages.json`
- 홈페이지 최신 3편: `index.html`의 `generated:insights` 주석 영역, 빌드 시 자동 갱신

기존 로고·색상·문의 폼·추적 코드·도메인 리다이렉트는 유지합니다.
최초 개편은 기존 공개글 10편만 배포합니다. 예약 원고 15편은 큐에 초안으로 보관합니다.

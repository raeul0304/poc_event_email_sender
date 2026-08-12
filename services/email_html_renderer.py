from __future__ import annotations

import re
from html import escape
from typing import Any
from urllib.parse import urlparse


def _text(value: Any, default: str = "-") -> str:
    if value is None:
        return default

    if isinstance(value, list):
        values = [
            str(v).strip()
            for v in value
            if v is not None and str(v).strip()
        ]
        return ", ".join(values) if values else default

    value = str(value).strip()

    if value.startswith("{") and value.endswith("}"):
        value = value[1:-1]

        parts = re.findall(
            r'"([^"]*)"|([^,]+)',
            value,
        )

        cleaned = []

        for quoted, plain in parts:
            item = quoted or plain
            item = item.strip()

            if item:
                cleaned.append(item)

        return ", ".join(cleaned) if cleaned else default

    return value if value else default


def _extract_markdown_url(value: Any) -> str:
    if not value:
        return ""

    value = str(value).strip()

    match = re.match(
        r"\[.*?\]\((https?://.*?)\)$",
        value,
    )

    if match:
        return (
            match.group(1)
            .replace(r"\(", "(")
            .replace(r"\)", ")")
        )

    if value.startswith(("http://", "https://")):
        return value

    return ""


def _safe_url(value: Any) -> str:
    url = _extract_markdown_url(value)

    if not url:
        return ""

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return ""

    return url


def normalize_event(
    item: dict[str, Any],
) -> dict[str, str]:

    payload = item.get("payload") or {}
    source_row = payload.get("source_row") or {}

    title = (
        item.get("title")
        or source_row.get("제목")
    )

    organization = (
        item.get("organization")
        or source_row.get("주최")
    )

    event_type = (
        item.get("event_type")
        or source_row.get("행사 성격")
    )

    start_date = (
        source_row.get("시작 일시")
        or item.get("starts_at")
    )

    end_date = (
        source_row.get("종료 일시")
        or item.get("ends_at")
    )

    location = source_row.get("장소")

    keywords = (
        item.get("keywords")
        or source_row.get("주요 키워드")
    )

    summary = source_row.get("주제 요약")
    paid = source_row.get("유료 여부")

    detail_url = (
        _safe_url(source_row.get("상세 정보 링크"))
        or _safe_url(item.get("canonical_url"))
        or _safe_url(source_row.get("등록 링크"))
    )

    registration_url = _safe_url(
        source_row.get("등록 링크")
    )

    return {
        "event_id": _text(item.get("event_id")),
        "title": _text(title),
        "organization": _text(organization),
        "event_type": _text(event_type),
        "start_date": _text(start_date),
        "end_date": _text(end_date),
        "location": _text(location),
        "keywords": _text(keywords),
        "summary": _text(summary),
        "paid": _text(paid),
        "detail_url": detail_url,
        "registration_url": registration_url,
    }


def normalize_events(
    items: list[dict[str, Any]],
) -> list[dict[str, str]]:

    return [
        normalize_event(item)
        for item in items
    ]


def render_event_card(
    event: dict[str, str],
) -> str:

    detail_button = ""

    if event["detail_url"]:
        detail_button = f"""
        <table
          role="presentation"
          cellspacing="0"
          cellpadding="0"
          border="0"
          style="margin-top: 22px;"
        >
          <tr>
            <td
              align="left"
              style="
                background-color: #2563eb;
                border-radius: 7px;
              "
            >
              <a
                href="{escape(event['detail_url'], quote=True)}"
                target="_blank"
                style="
                  display: inline-block;
                  padding: 13px 22px;
                  color: #ffffff;
                  font-size: 14px;
                  font-weight: 700;
                  text-decoration: none;
                "
              >
                이벤트 상세 보기
              </a>
            </td>
          </tr>
        </table>
        """

    registration_link = ""

    if (
        event["registration_url"]
        and event["registration_url"]
        != event["detail_url"]
    ):
        registration_link = f"""
        <div
          style="
            margin-top: 14px;
            text-align: left;
          "
        >
          <a
            href="{escape(event['registration_url'], quote=True)}"
            target="_blank"
            style="
              color: #2563eb;
              font-size: 13px;
              font-weight: 600;
              text-decoration: none;
            "
          >
            참가/등록 페이지 바로가기 →
          </a>
        </div>
        """

    return f"""
    <table
      role="presentation"
      width="100%"
      cellspacing="0"
      cellpadding="0"
      border="0"
      style="
        margin-bottom: 22px;
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
      "
    >
      <tr>
        <td
          style="
            padding: 26px;
            text-align: left;
          "
        >

          <div
            style="
              margin-bottom: 6px;
              font-size: 19px;
              font-weight: 700;
              line-height: 1.5;
              color: #111827;
              text-align: left;
            "
          >
            {escape(event["title"])}
          </div>

          <div
            style="
              margin-bottom: 20px;
              font-size: 13px;
              line-height: 1.5;
              color: #2563eb;
              font-weight: 600;
              text-align: left;
            "
          >
            {escape(event["keywords"])}
          </div>

          <table
            role="presentation"
            width="100%"
            cellspacing="0"
            cellpadding="0"
            border="0"
            style="
              font-size: 14px;
              line-height: 1.6;
              text-align: left;
            "
          >

            <tr>
              <td
                width="92"
                valign="top"
                style="
                  padding: 7px 0;
                  color: #6b7280;
                  font-weight: 600;
                  text-align: left;
                "
              >
                주최
              </td>
              <td
                valign="top"
                style="
                  padding: 7px 0;
                  color: #1f2937;
                  text-align: left;
                "
              >
                {escape(event["organization"])}
              </td>
            </tr>

            <tr>
              <td
                width="92"
                valign="top"
                style="
                  padding: 7px 0;
                  color: #6b7280;
                  font-weight: 600;
                  text-align: left;
                "
              >
                유형
              </td>
              <td
                valign="top"
                style="
                  padding: 7px 0;
                  color: #1f2937;
                  text-align: left;
                "
              >
                {escape(event["event_type"])}
              </td>
            </tr>

            <tr>
              <td
                width="92"
                valign="top"
                style="
                  padding: 7px 0;
                  color: #6b7280;
                  font-weight: 600;
                  text-align: left;
                "
              >
                일정
              </td>
              <td
                valign="top"
                style="
                  padding: 7px 0;
                  color: #1f2937;
                  text-align: left;
                "
              >
                {escape(event["start_date"])}
                <br />
                ~ {escape(event["end_date"])}
              </td>
            </tr>

            <tr>
              <td
                width="92"
                valign="top"
                style="
                  padding: 7px 0;
                  color: #6b7280;
                  font-weight: 600;
                  text-align: left;
                "
              >
                장소
              </td>
              <td
                valign="top"
                style="
                  padding: 7px 0;
                  color: #1f2937;
                  text-align: left;
                "
              >
                {escape(event["location"])}
              </td>
            </tr>

            <tr>
              <td
                width="92"
                valign="top"
                style="
                  padding: 7px 0;
                  color: #6b7280;
                  font-weight: 600;
                  text-align: left;
                "
              >
                참가비
              </td>
              <td
                valign="top"
                style="
                  padding: 7px 0;
                  color: #1f2937;
                  text-align: left;
                "
              >
                {escape(event["paid"])}
              </td>
            </tr>

          </table>

          <div
            style="
              margin-top: 18px;
              padding: 16px;
              background-color: #f8fafc;
              border-radius: 7px;
              font-size: 14px;
              line-height: 1.7;
              color: #4b5563;
              text-align: left;
            "
          >
            {escape(event["summary"])}
          </div>

          {detail_button}

          {registration_link}

        </td>
      </tr>
    </table>
    """


def render_email_html(
    items: list[dict[str, Any]],
    user_name: str = "사용자",
) -> str:

    events = normalize_events(items)

    event_cards = "\n".join(
        render_event_card(event)
        for event in events
    )

    return f"""
<!DOCTYPE html>
<html lang="ko">

<head>
  <meta charset="UTF-8">
  <meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
  >
  <title>이벤트 안내</title>
</head>

<body
  style="
    margin: 0;
    padding: 0;
    background-color: #f3f4f6;
    font-family:
      Arial,
      'Apple SD Gothic Neo',
      'Noto Sans KR',
      sans-serif;
  "
>

<table
  role="presentation"
  width="100%"
  cellspacing="0"
  cellpadding="0"
  border="0"
  style="
    width: 100%;
    background-color: #f3f4f6;
  "
>
  <tr>
    <td
      align="center"
      style="padding: 32px 16px;"
    >

      <table
        role="presentation"
        width="100%"
        cellspacing="0"
        cellpadding="0"
        border="0"
        style="
          width: 100%;
          max-width: 680px;
          background-color: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 10px;
          overflow: hidden;
        "
      >

        <tr>
          <td
            style="
              padding: 36px 32px;
              text-align: left;
            "
          >

            <div
              style="
                margin-bottom: 10px;
                font-size: 22px;
                font-weight: 700;
                line-height: 1.4;
                color: #111827;
                text-align: left;
              "
            >
              {escape(user_name)}님,
              새로운 이벤트를 확인해 보세요.
            </div>

            <div
              style="
                margin-bottom: 30px;
                font-size: 15px;
                line-height: 1.7;
                color: #4b5563;
                text-align: left;
              "
            >
              관심 조건과 관련된 이벤트
              <strong>{len(events)}건</strong>이 확인되었습니다.
              아래에서 상세 내용을 확인할 수 있습니다.
            </div>

            {event_cards}

          </td>
        </tr>

        <tr>
          <td
            style="
              padding: 22px 32px;
              border-top: 1px solid #e5e7eb;
              background-color: #f8fafc;
              font-size: 12px;
              line-height: 1.6;
              color: #6b7280;
              text-align: left;
            "
          >
            본 메일은 이벤트 알림 수신 설정에 따라 발송되었습니다.

            <div style="margin-top: 10px;">
              © 2026 Event Finder. All rights reserved.
            </div>

          </td>
        </tr>

      </table>

    </td>
  </tr>
</table>

</body>
</html>
"""
# flake8: noqa: E501
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from city_scrapers_core.constants import BOARD
from scrapy.http import HtmlResponse, Request
from scrapy.utils.test import get_crawler

from city_scrapers.spiders.cle_transit import CleTransitSpider


@pytest.fixture
def spider():
    crawler = get_crawler(CleTransitSpider)
    return CleTransitSpider.from_crawler(crawler)


def test_parse(spider, mocker):
    html_content = """
    <div class="fc-day-grid">
        <a class="fc-day-grid-event" href="/event/1">
            <span class="fc-title">Board Meeting</span>
        </a>
        <a class="fc-day-grid-event" href="/event/2">
            <span class="fc-title">Career Day</span>
        </a>
    </div>
    """
    url = "https://www.riderta.com/events"
    request = Request(url=url)
    response = HtmlResponse(
        url=url, request=request, body=html_content.encode(), encoding="utf-8"
    )
    response.follow = MagicMock(return_value=None)

    list(spider.parse(response))

    response.follow.assert_called()
    called_args_list = response.follow.call_args_list
    assert len(called_args_list) == 1
    assert "/event/1" in called_args_list[0][0][0]


def test_filter_events(spider, mocker):
    html_content = """
    <div class="fc-day-grid">
        <a class="fc-day-grid-event" href="/event/1">
            <span class="fc-title">Board Meeting</span>
        </a>
        <a class="fc-day-grid-event" href="/event/2">
            <span class="fc-title">Career Day</span>
        </a>
    </div>
    """
    url = "https://www.riderta.com/events"
    request = Request(url=url)
    response = HtmlResponse(
        url=url, request=request, body=html_content.encode(), encoding="utf-8"
    )
    response.follow = mocker.MagicMock(return_value=None)

    list(spider.parse(response))

    # Assert follow was called for the meeting but not for the career day
    response.follow.assert_called_once_with(
        "/event/1", spider.parse_event, meta={"title": "Board Meeting"}
    )


def test_parse_event(spider, mocker):
    html_content = """
    <div class="event-details">
        <div class="views-field-field-event-date">
            <h2>Wed, May 29 2024, 9 - 10am</h2>
        </div>
        <p class="address">
            <span>The Holden Arboretum</span>, <span>9550 Sperry Rd</span>,
            <span>Kirtland</span>,
            <span>OH</span>, <span>44094</span>, <span>United States</span>
        </p>
        <div class="views-element-container block block-views block-views-blockevent-attachments-block-1">
            <h2>Attachments</h2>
            <div class="content">
                <ul>
                    <li><a href="/sites/default/files/events/2024-05-07CommitteePackageREVISED.pdf">
                    2024-05-07CommitteePackageREVISED.pdf</a></li>
                    <li><a href="/sites/default/files/events/2024-05-07CodeBookUpdatePresentation.pdf">
                    2024-05-07CodeBookUpdatePresentation.pdf</a></li>
                    <li><a href="/sites/default/files/events/2024-05-07EZFareRenewalPresentation.pdf">
                    2024-05-07EZFareRenewalPresentation.pdf</a></li>
                </ul>
            </div>
        </div>
    </div>
    """
    url = "https://www.riderta.com/event/1"
    request = Request(url=url, meta={"title": "Board meeting"})
    response = HtmlResponse(
        url=url, request=request, body=html_content.encode(), encoding="utf-8"
    )

    # Call the parse_event method
    result = spider.parse_event(response)

    # Assertions
    assert result["title"] == "Board meeting"
    assert result["start"] == datetime(2024, 5, 29, 9, 0)
    assert result["end"] == datetime(2024, 5, 29, 10, 0)
    assert result["location"] == {
        "name": "The Holden Arboretum",
        "address": "The Holden Arboretum, 9550 Sperry Rd, Kirtland, OH 44094, United States",
    }
    assert result["classification"] == BOARD
    assert len(result["links"]) == 3
    assert (
        result["links"][0]["href"]
        == "/sites/default/files/events/2024-05-07CommitteePackageREVISED.pdf"
    )
    assert result["links"][0]["title"] == "2024-05-07CommitteePackageREVISED.pdf"

    assert result["classification"] == BOARD

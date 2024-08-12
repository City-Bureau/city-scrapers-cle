import re

from city_scrapers_core.constants import BOARD, COMMITTEE, NOT_CLASSIFIED
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil import parser as date_parser


class CleTransitSpider(CityScrapersSpider):
    name = "cle_transit"
    agency = "Greater Cleveland Regional Transit Authority"
    timezone = "America/Detroit"
    location = {
        "name": "Root-McBride Building",
        "address": "1240 W. Sixth St. Cleveland, Ohio 44113",
    }
    start_urls = ["https://www.riderta.com/board"]

    def parse(self, response):
        meeting_links = response.css(
            "div.inserted-view > div.calendar-event-style > div.view-content > .mb-4.views-row a::attr(href)"  # noqa
        ).extract()
        # filter out links that are not event pages
        filtered_links = [
            meeting_link for meeting_link in meeting_links if "events" in meeting_link
        ]  # noqa
        # remove duplicates (there are some links that are repeated)
        deduped_meeting_links = list(set(filtered_links))
        for meeting_link in deduped_meeting_links:
            if "events" in meeting_link:
                yield response.follow(meeting_link, callback=self._parse_meeting)

    def _parse_meeting(self, response):
        title = self._parse_title(response)
        start, end = self._parse_date(response)
        meeting = Meeting(
            title=title,
            description=self._parse_description(response),
            classification=self._parse_classification(title),
            start=start,
            end=end,
            all_day=False,
            time_notes="",
            location=self._parse_location(response),
            links=self._parse_links(response),
            source=response.url,
        )
        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)
        yield meeting

    def _parse_title(self, response) -> str:
        return (
            response.css(".content > h1.title span span::text")
            .extract_first()
            .strip()  # noqa
        )

    def _parse_description(self, response) -> str:
        description = response.css(
            ".content .field--name-body.field--type-text-with-summary p::text"
        ).extract()
        if description:
            full_description = " ".join(description)
            # remove extra whitespace
            return re.sub(r"\s+", " ", full_description).strip()
        return ""

    def _parse_date(self, response) -> tuple:
        """
        Expect to find an element with the meeting date in format
        "Tue, Jan 23 2024, 9 - 11am" and return a tuple of start and
        end datetime objects. If no meridiem is included in the start
        time, assume the end time is in the same meridiem.
        """
        meeting_duration_str = response.css(
            ".block-views-blockevents-date-block-1 h2::text"
        ).extract_first()
        date_match_str = re.search(
            r"([A-Z][a-z]{2} \d{1,2} \d{4})", meeting_duration_str
        ).group(0)
        time_match_str = meeting_duration_str.split(",")[2].strip()
        time_matches = re.findall(r"\d{1,2}(?::\d{2})?", time_match_str)
        merdiem_matches = re.findall(r"(am|pm)", time_match_str)
        if len(merdiem_matches) == 2:
            start = date_parser.parse(
                f"{date_match_str} {time_matches[0]}{merdiem_matches[0]}",
                fuzzy=True,  # noqa
            )
            end = date_parser.parse(
                f"{date_match_str} {time_matches[1]}{merdiem_matches[1]}",
                fuzzy=True,  # noqa
            )
            return start, end
        elif len(merdiem_matches) == 1:
            start = date_parser.parse(
                f"{date_match_str} {time_matches[0]}{merdiem_matches[0]}",
                fuzzy=True,  # noqa
            )
            end = date_parser.parse(
                f"{date_match_str} {time_matches[1]}{merdiem_matches[0]}",
                fuzzy=True,  # noqa
            )
            return start, end
        else:
            raise ValueError(
                "Meeting date string does not conform to expected format"
            )  # noqa

    def _parse_location(self, response) -> dict:
        location_selectors = [
            "views-field-field-event-location-address-line1",
            "views-field-field-event-location-address-line2",
            "views-field-field-event-location-locality",
            "views-field-field-event-location-administrative-area",
            "views-field-field-event-location-postal-code",
        ]
        address = ""
        for selector in location_selectors:
            address_part = response.css(
                f".{selector} strong::text"
            ).extract_first()  # noqa
            if address_part:
                if "address-line1" in selector:
                    address = address + address_part + ", "
                else:
                    address = address + address_part + " "
        # condense whitespace
        clean_address = re.sub(r"\s+", " ", address).strip()
        return {
            "name": "",
            "address": clean_address,
        }

    def _parse_links(self, response) -> list:
        attachment_links = response.css(
            ".view-event-attachments.view-id-event_attachments a"
        )
        links = []
        for attachment_link in attachment_links:
            abs_url = response.urljoin(
                attachment_link.css("::attr(href)").extract_first()
            )
            links.append(
                {
                    "title": attachment_link.css("::text").extract_first(),
                    "href": abs_url,
                }
            )
        return links

    def _parse_classification(self, title: str) -> str:
        if "board" in title.lower():
            return BOARD
        elif "committee" in title.lower():
            return COMMITTEE
        return NOT_CLASSIFIED

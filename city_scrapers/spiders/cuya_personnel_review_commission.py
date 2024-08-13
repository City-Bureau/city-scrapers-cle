from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from dateutil.parser import parse as dateparse


class CuyaPersonnelReviewCommissionSpider(CityScrapersSpider):
    name = "cuya_personnel_review_commission"
    agency = "Cuyahoga County Personnel Review Commission"
    start_urls = ["https://cuyahogacounty.gov/personnel-review-commission/calendar"]

    def parse(self, response):
        items = response.css("div.moudle.list.events > ul > li")
        for item in items:
            title = item.css("div.title a::text").extract_first()
            meta_text = item.css(".meta span::text").extract()
            clean_meta_text = [text.strip() for text in meta_text if text.strip()]
            if not title or not meta_text:
                continue
            start, end = self._parse_times(clean_meta_text)
            meeting = Meeting(
                title=title,
                description="",
                classification=COMMISSION,
                start=start,
                end=end,
                all_day=False,
                time_notes="",
                location=self._parse_location(clean_meta_text),
                links=self._parse_links(item),
                source=response.url,
            )
            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_times(self, meta_text: list[str]) -> tuple:
        date = meta_text[1]
        start_time = meta_text[2]
        end_time = meta_text[4]
        start = dateparse(f"{date} {start_time}")
        end = dateparse(f"{date} {end_time}")
        return start, end

    def _parse_location(self, meta_text: list[str]) -> dict:
        location = meta_text[0]
        return {
            "name": "",
            "address": location,
        }

    def _parse_links(self, item) -> list:
        attachments = item.css("div.related-content a")
        links = []
        for attachment in attachments:
            url = attachment.css("a::attr(href)").extract_first()
            title = attachment.css("a span::text").extract_first()
            links.append({"href": url, "title": title})
        return links

import re
from datetime import datetime

import dateutil.parser
from city_scrapers_core.items import Meeting


class CuyaCountyMixin2:
    """
    This is a newer version of CuyaCountyMixin that handles page structure
    changes to the Cuyahoga County site that occured in 2023. It is not yet
    used in all spiders. When it is, the old mixin can be removed and this
    one renamed to CuyaCountyMixin.
    """

    timezone = "America/Detroit"

    def parse(self, response):
        links = response.css(
            ".row.bceventgrid > table > tbody > tr > td:nth-child(2) > a::attr(href)"
        ).extract()
        for link in links:
            yield response.follow(link, callback=self._parse_detail, dont_filter=True)

    def _parse_detail(self, response):
        main_el = response.css("div.moudle")
        start_date, end_date = self._parse_dates(main_el)
        meeting = Meeting(
            title=self._parse_title(main_el),
            description=self._parse_description(main_el),
            classification=self.classification,
            start=start_date,
            end=end_date,
            time_notes="",
            all_day=False,
            location=self._parse_location(main_el),
            links=self._parse_links(main_el),
            source=response.url,
        )
        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)
        yield meeting

    def _parse_title(self, selector):
        title_str = selector.css("h1.title::text").extract_first().strip()
        return title_str

    def _parse_description(self, selector):
        texts = selector.css(".content ::text").extract()
        cleaned_texts = [text.strip() for text in texts if text.strip()]
        full_text = " ".join(cleaned_texts)
        return full_text

    def _parse_dates(self, selector):
        # Extract the start date from the 'content' attribute
        start_date_str = selector.css(
            '.meta-item[itemprop="startDate"] ::attr(content)'
        ).get()
        if not start_date_str:
            raise ValueError("Could not find start date")
        start_date = dateutil.parser.parse(start_date_str).date()

        # Extract the start time text
        text_nodes = selector.css(
            ".meta-item[itemprop='startDate'] > p::text"
        ).extract()
        start_time_str = text_nodes[1].strip()
        if not start_time_str:
            raise ValueError("Could not find start time")
        start_time = dateutil.parser.parse(start_time_str).time()

        # Extract the end time text
        time_text = " ".join(selector.css(".meta-item p ::text").extract()).strip()
        time_text_parts = time_text.split(" - ")
        if len(time_text_parts) > 1:
            end_time_str = time_text_parts[1].strip()
            pattern = r"\b([1-9]|1[0-2]):[0-5][0-9]\s*(AM|PM)\b"
            match = re.search(pattern, end_time_str, re.IGNORECASE)
            if match:
                refined_end_time_str = match.group()
                end_time = dateutil.parser.parse(refined_end_time_str).time()
            else:
                raise ValueError("Could not find end time")
        else:
            raise ValueError("Could not find end time")

        # combine
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(start_date, end_time)

        return start_datetime, end_datetime

    def _parse_location(self, selector):
        address = (
            selector.css('div[itemprop="location"] [itemprop="streetAddress"]::text')
            .get()
            .strip()
        )
        return {"name": "", "address": address}

    def _parse_links(self, selector):
        links = selector.css(".related-content a")
        links_data = []
        for link in links:
            href = link.css("::attr(href)").get()
            text = link.css("span::text").get().strip()
            links_data.append({"title": text, "href": href})

        return links_data

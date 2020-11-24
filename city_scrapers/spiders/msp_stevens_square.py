from city_scrapers_core.constants import NOT_CLASSIFIED
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from datetime import datetime
import re


class MspStevensSquareSpider(CityScrapersSpider):
    name = "msp_stevens_square"
    agency = "Stevens Square Community Organization"
    timezone = "America/Chicago"
    start_urls = ["https://www.stevenssquare.org/events"]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for item in response.css("article.eventlist-event"):
            meeting = Meeting(
                title=self._parse_title(item),
                description=self._parse_description(item),
                classification=self._parse_classification(item),
                start=self._parse_start(item),
                end=self._parse_end(item),
                all_day=self._parse_all_day(item),
                time_notes=self._parse_time_notes(item),
                location=self._parse_location(item),
                links=self._parse_links(item),
                source=self._parse_source(response),
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        title = item.css('h1 a.eventlist-title-link::text').get()
        self._event_title = title
        return title

    def _parse_description(self, item):
        """Parse or generate meeting description."""
        desc = ""
        event_excerpt = item.css("div.eventlist-excerpt")
        p_tags = event_excerpt.xpath('.//p/text()')
        for p in p_tags:
            desc += p.get()
        desc = re.sub(r"\xa0", " ", desc)  # Remove &nbsp; 
        return desc

    def _parse_classification(self, item):
        """Parse or generate classification from allowed options."""
        return NOT_CLASSIFIED

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        date_str = item.css("time.event-date::text").get()
        time_str = item.css("time.event-time-12hr-start::text").get()
        date_obj = datetime.strptime(f'{date_str} {time_str}', "%A, %B %d, %Y %I:%M %p")
        return date_obj

    def _parse_end(self, item):
        """Parse end datetime as a naive datetime object. Added by pipeline if None"""
        date_str = item.css("time.event-date::text").get()
        time_str = item.css("time.event-time-12hr-end::text").get()
        date_obj = datetime.strptime(f'{date_str} {time_str}', "%A, %B %d, %Y %I:%M %p")
        return date_obj

    def _parse_time_notes(self, item):
        """Parse any additional notes on the timing of the meeting"""
        return ""

    def _parse_all_day(self, item):
        """Parse or generate all-day status. Defaults to False."""
        return False

    def _parse_location(self, item):
        """Parse or generate location."""
        # return {
        #     "address": "",
        #     "name": "",
        # }
        return ""

    def _parse_links(self, item):
        """Parse or generate links."""
        event_href = item.xpath("a/@href").get()
        event_link = f'{self.start_urls[0]}{event_href.replace("/events", "")}'
        return [{"href": event_link, "title": f'{self._event_title} Event Page'}]

    def _parse_source(self, response):
        """Parse or generate source."""
        return response.url

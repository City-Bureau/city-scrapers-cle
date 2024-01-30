from datetime import datetime, time

from city_scrapers_core.constants import COMMISSION, PASSED, TENTATIVE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider

class CleCpcSpider(CityScrapersSpider):
    name = "cle_cpc"
    agency = "Cleveland Community Police Commission"
    timezone = "America/Chicago"
    start_urls = ["https://clecpc.org/get-involved/calendar/"]
    links = [
        {
            "title": "Meeting agendas and minutes",
            "href": "https://clecpc.org/resources/meeting-agendas-minutes/",
        }
    ]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        calendars = response.css('.mec-wrap.mec-skin-grid-container')
        if len(calendars) <= 1:
            raise ("Meetings calendar not found")
        for event in calendars[0].css("article.mec-event-article"):
            event_link = event.css("h4.mec-event-title a::attr(href)").get()
            if event_link:
                yield response.follow(event_link, callback=self._parse_detail)

    def _parse_detail(self, response):
        """
        Parse details from the event detail page.
        """

        date = self._parse_date(response)
        start_time, end_time = self._parse_start_end_time(response)
        meeting = Meeting(
            title=self._parse_title(response),
            description=self._parse_description(response),
            classification=COMMISSION,
            start=self._gen_datetime(date, start_time),
            end=self._gen_datetime(date, end_time),
            time_notes="",
            all_day=False,
            location=self._parse_location(response),
            links=self.links,
            source=self._parse_source(response),
        )
        meeting["status"] = self._get_status(meeting)
        meeting["id"] = self._get_id(meeting)
        yield meeting

    def _parse_title(self, response):
        """Parse or generate meeting title."""
        title = response.css(".mec-single-title::text").get()
        if not title:
            return None
        return title.strip()

    def _parse_description(self, response):
        """
        Extracts and returns all text within the mec-single-event-description element.
        """
        description_parts = response.css(
            ".mec-single-event-description *::text"
        ).getall()
        full_description = " ".join(
            part.strip() for part in description_parts if part.strip()
        )
        return full_description

    def _parse_date(self, response):
        # Extracting the date string
        date_str = response.css(
            ".mec-single-event-date .mec-start-date-label::text"
        ).get()
        # Parsing the date string into a datetime object
        date = datetime.strptime(date_str, "%b %d %Y") if date_str else None
        return date

    def _parse_start_end_time(self, response):
        # Extracting the time string
        time_str = response.css(".mec-single-event-time .mec-events-abbr::text").get()
        if time_str:
            time_parts = time_str.split(" - ")
            if len(time_parts) == 2:
                # Splitting the start and end time and converting to datetime objects
                start_time_str, end_time_str = time_parts
                start_time = datetime.strptime(start_time_str, "%I:%M %p").time()
                end_time = datetime.strptime(end_time_str, "%I:%M %p").time()
                return start_time, end_time
            else:
                # Log a warning or handle the case where the time format is unexpected
                self.logger.warning(f"Unexpected time format: {time_str}")
        # Return None for both start and end times if the time element doesn't exist or format is incorrect
        return None, None

    def _gen_datetime(self, date, time_obj):
        """
        Generate a datetime object from a date and a time object.
        If time_obj is None, set the time to midnight.
        """
        if time_obj is None:
            time_obj = time(0, 0)  # Midnight
        return datetime.combine(date, time_obj)

    def _parse_location(self, response):
        org_name = response.css(".org::text").get().strip()
        address = response.css(".mec-address::text").get().strip()
        return {
            "name": org_name,
            "address": address,
        }

    def _parse_source(self, response):
        """Generate source."""
        return response.url

    def _get_status(self, item):
        """
        Overrides the parent class method because basing a meeting's
        cancellation status on the title and time of the meeting is not
        reliable. Instead, we'll only focus on the meeting's start time.
        """
        if item["start"] < datetime.now():
            return PASSED
        return TENTATIVE

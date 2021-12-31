import re
from datetime import datetime, timedelta

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider

from city_scrapers.utils import calculate_upcoming_meeting_days


class ClePlanningCommissionSpider(CityScrapersSpider):
    name = "cle_planning_commission"
    agency = "Cleveland City Planning Commission"
    title = "City Planning Commission"
    location = {
        "name": "City Hall",
        "address": "601 Lakeside Ave, Room 514, Cleveland OH 44114",
    }
    time_str = "9:00am"
    timezone = "America/Detroit"
    start_urls = [
        "https://planning.clevelandohio.gov/designreview/schedule.php"  # noqa
    ]
    description = "Due to Covid meetings are being held on WebEx rather than in person. For more information contact cityplanning@clevelandohio.gov"  # noqa
    calculated_description = "This is an upcoming meeting - please verify it with staff if you want attend. Due to Covid meetings are being held on WebEx rather than in person. For more information contact cityplanning@clevelandohio.gov"  # noqa

    def parse(self, response):
        """
        The current page contains both the info for the city planning commission as
        well as the info for the design review committees. The design reviews are
        handled in a separate scraper so we only need to grab info for city planning.

        There are several other points to keep in mind for this scraper:

        1. The way the data is presented doesn't make it easy to know whether or
            not a meeting occurred but doesn't have an agenda, or whether a meeting
            is going to happen on a normal meeting date.  The strategy I'm using is
            to treat the agenda links as authoritative for past (and if listed
            upcoming) meetings. So previous meetings are just read off of the agenda
            links. For future meetings we take the date of the most recent agenda
            and then calculate meetings for 60 days from that date. As dates
            progress and agendas are added, those tentative meetings will either be
            confirmed to exist or disappear based on the ways the agendas are
            updated.  For calculated meetings we add a line to the description
            encouraging users to verify the meeting with staff before attempting to
            attend.

        2. There is no mention of the year anywhere in the text of the site. We
            can extract it from the agenda link - at least for now. But it will
            be important to keep an eye on how the site is changed in January.

        3. Meetings are currently not being held in person but over webex. We've
            included this information in the meeting description.
        """

        meeting_time_schedule_str = response.css("p.mb-0::text").extract_first()
        self._validate_location(meeting_time_schedule_str)
        self._validate_start_time(meeting_time_schedule_str)
        self._validate_schedule(meeting_time_schedule_str)
        most_recent_start = datetime.today()

        dropdowns = response.css(
            "div.container div.container div.container div.dropdown"
        )
        commission_agendas = dropdowns[0]
        commission_presentations = self._parse_presentations(dropdowns[1])

        # Start by looking through the agendas for existing meetings
        for agenda in commission_agendas.css("div.dropdown-menu a.dropdown-item"):
            month_str, day_str = (
                agenda.css("*::text").extract_first().strip().split(" ")
            )

            year_str = self._parse_year_from_link(agenda)

            start = self._parse_start(year_str, month_str, day_str, self.time_str)
            # most_recent_start will be used to calculate upcoming meetings
            # with no agenda
            most_recent_start = start
            if not start:
                continue

            meeting = Meeting(
                title=self.title,
                description=self.description,
                classification=COMMISSION,
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=self._parse_links(agenda, commission_presentations, response),
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

        # next we calculate upcoming meeting dates for 60 days after the
        # last agenda date
        calc_start = most_recent_start + timedelta(days=1)
        # since downtown meetings are calculated based on the city planning
        # meeting one day ahead, we need to add an extra day to avoid
        calc_end = calc_start + timedelta(days=60)

        upcoming_meetings = calculate_upcoming_meeting_days(
            # we can safely hardcode the first and thrid friday, since we
            # validate the meeting schedule with _validate_schedule
            4,
            [0, 2],
            calc_start.date(),
            calc_end.date(),
        )

        for day in upcoming_meetings:
            start = self._parse_calculated_start(day, "9:00am")
            meeting = Meeting(
                title=self.title,
                description=self.calculated_description,
                classification=COMMISSION,
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location=self.location,
                links=[],
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _validate_start_time(self, text):
        if "9am" not in text:
            raise ValueError("Meeting start time has changed")

    def _validate_location(self, text):
        """Parse or generate location."""
        if " in Room 514, City Hall" not in text:
            raise ValueError("Meeting location has changed")

    def _validate_schedule(self, text):
        if "every 1st & 3rd Friday" not in text:
            raise ValueError("Meeting schedule has changed")

    def _parse_start(self, year_str, month_str, day_str, time_str):
        """Parse start datetime as a naive datetime object."""
        date_str = " ".join([year_str, month_str[0:3], day_str, time_str])
        return datetime.strptime(date_str, "%Y %b %d %I:%M%p")

    def _parse_calculated_start(self, day, time_str):
        """Parse start datetime from python date and a string with the time."""
        date_str = " ".join([day.strftime("%Y %B %d"), time_str])
        return datetime.strptime(date_str, "%Y %B %d %I:%M%p")

    def _parse_links(self, agenda, presentations, response):
        """Parse out the links for the meeting"""
        links = []
        links.append(
            {"title": "Agenda", "href": response.urljoin(agenda.attrib["href"])}
        )
        key = self._dropdown_to_key(agenda)
        if key in presentations:
            links.append(
                {"title": "Presentation", "href": response.urljoin(presentations[key])}
            )

        return links

    def _parse_year_from_link(self, item):
        """Parse the year as a string from a link"""
        link = item.attrib["href"]
        year_match = re.search(r"\/(20\d{2})\/", link)
        if year_match:
            return year_match.group(1)
        return "2021"

    def _parse_presentations(self, items):
        presentations = {}
        for presentation in items.css("div.dropdown-menu a.dropdown-item"):
            key = self._dropdown_to_key(presentation)
            presentations[key] = presentation.attrib["href"]
        return presentations

    def _dropdown_to_key(self, item):
        name = item.css("::text").extract_first()
        [month, day] = name.split(" ")
        month = month[0:3].lower()
        year = self._parse_year_from_link(item)
        return f"{year}-{month}-{day}"

import re
import time
from datetime import datetime, timedelta

from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from city_scrapers.utils import MeetingDateCalculator


class CleDesignReviewSpider(CityScrapersSpider):
    name = "cle_design_review"
    agency = "Cleveland Design Review Advisory Committees"
    timezone = "America/Detroit"
    start_urls = [
        "https://planning.clevelandohio.gov/designreview/schedule.php"  # noqa
    ]
    description = "Due to Covid meetings are being held on WebEx rather than in person. For more information contact "  # noqa
    calculated_description = "This is an upcoming meeting - please verify it with staff if you want attend. Due to Covid meetings are being held on WebEx rather than in person. For more information contact "  # noqa

    def parse(self, response):
        """
            There's no element that wraps both the committee name/time and
            the dropdown containing the agendas.  As such we want to grab
            each committee name/times and then use the following dropdown
            to get the agendas.  Luckily all of the committee name/times are
            (and are the only thing in) divs with the class '.mt-3' so we can
            grab all the divs with those classes and then look for the next sibling
            div with the ".dropdown" class to get the links to all the agendas.

            Note that the city planning meeting is handled by a different scraper so
            we do look at it here. Luckily the name/times for the city planning
            meeting are not currently wrapped in a div, so the list of nodes described
            above won't include it.

            There are three other points to keep in mind for this scraper:

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
        committee_metas = response.css(
            "div.mt-3"
        )  # this skips city planning since it is handled by a separate scraper
        committee_agendas = response.css("div.mt-3 + div.dropdown")
        if len(committee_metas) != len(committee_agendas):
            # we haven't sucessfully  extracted matched metas and agendas so we
            # can't safely iterate over them together.
            raise ValueError("Cannot match committee agandas to committee metadata")
        committee_items = zip(committee_metas, committee_agendas)

        for committee_meta, commitee_agenda_list in committee_items:
            title = self._parse_title(committee_meta)
            if not title:
                continue
            location = self._parse_location(committee_meta)
            time_str = self._parse_time_str(committee_meta)
            email_contact = self._parse_email_contact(committee_meta)
            weekday, chosen_ordinals, is_downtown = self._parse_meeting_schedule_info(
                committee_meta
            )
            most_recent_start = datetime.today()

            # Start by looking through the agendas for existing meetings
            for agenda in commitee_agenda_list.css("div.dropdown-menu a.dropdown-item"):
                month_str, day_str = (
                    agenda.css("*::text").extract_first().strip().split(" ")
                )
                year_str = self._parse_year_from_agenda_link(agenda)

                start = self._parse_start(year_str, month_str, day_str, time_str)
                # most_recent_start will be used to calculate upcoming meetings
                # with no agenda
                most_recent_start = start
                if not start:
                    continue
                meeting = Meeting(
                    title=title,
                    description=self.description + email_contact,
                    classification=ADVISORY_COMMITTEE,
                    start=start,
                    end=None,
                    all_day=False,
                    time_notes="",
                    location=location,
                    links=self._parse_links(agenda, response),
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
            if is_downtown:
                calc_start = calc_start + timedelta(days=1)

            calc_end = calc_start + timedelta(days=60)

            upcoming_meetings = MeetingDateCalculator.calculate_upcoming_meeting_days(
                weekday, chosen_ordinals, calc_start, calc_end
            )
            if is_downtown:  # downtown meetings are a day before the one calculated
                upcoming_meetings = [
                    day + timedelta(days=-1) for day in upcoming_meetings
                ]

            for day in upcoming_meetings:
                start = self._parse_calculated_start(day, time_str)
                meeting = Meeting(
                    title=title,
                    description=self.calculated_description + email_contact,
                    classification=ADVISORY_COMMITTEE,
                    start=start,
                    end=None,
                    all_day=False,
                    time_notes="",
                    location=location,
                    links=[],
                    source=response.url,
                )

                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        committee_strs = [
            c.strip()
            for c in item.css("h4::text").extract()
            if c.strip().upper().endswith("DESIGN REVIEW COMMITTEE")
        ]
        if len(committee_strs):
            return committee_strs[0].title()

    def _parse_time_str(self, item):
        """Parse out the time as a string in the format hh:mm:am/pm"""
        desc_text = " ".join(item.css("p.mb-1::text").extract())
        time_match = re.search(r"\d{1,2}:\d{2}\s*[apm]{2}", desc_text)
        if time_match:
            return time_match.group().replace(" ", "")
        return "12:00am"

    def _parse_start(self, year_str, month_str, day_str, time_str):
        """Parse start datetime as a naive datetime object."""
        date_str = " ".join([year_str, month_str, day_str, time_str])
        return datetime.strptime(date_str, "%Y %B %d %I:%M%p")

    def _parse_calculated_start(self, day, time_str):
        """Parse start datetime from python date and a string with the time."""
        date_str = " ".join([day.strftime("%Y %B %d"), time_str])
        return datetime.strptime(date_str, "%Y %B %d %I:%M%p")

    def _parse_location(self, item):
        """Parse or generate location."""
        desc_str = " ".join(item.css("p.mb-1::text").extract())
        loc_str = re.sub(r"\s+", " ", re.split(r"(\sin\s|\sat\s)", desc_str)[-1])
        # The downtown/flats commission doesn't give the full address - it just says
        # city hall so we need a special case to add the street address
        if "City Hall" in loc_str:
            loc_name = "City Hall"
            room_match = re.search(r"(?<=Room )\d+", loc_str)
            if room_match:
                loc_addr = "601 Lakeside Ave, Room {}, Cleveland OH 44114".format(
                    room_match.group()
                )
            else:
                loc_addr = "601 Lakeside Ave, Cleveland OH 44114"
        else:
            split_loc = loc_str.split("-")
            loc_name = "-".join(split_loc[:-1])
            loc_addr = split_loc[-1]
        # We need to make sure that the address ends with the city and state
        if "Cleveland" not in loc_addr:
            loc_addr = loc_addr.strip() + " Cleveland, OH"
        return {
            "name": loc_name.strip(),
            "address": loc_addr.strip(),
        }

    def _parse_links(self, item, response):
        """Parse out the links for the meeting"""
        links = []
        links.append({"title": "Agenda", "href": response.urljoin(item.attrib["href"])})
        return links

    def _parse_year_from_agenda_link(self, item):
        """Parse the year as a string from a link containing the agenda"""
        link = item.attrib["href"]
        year_match = re.search(r"\/(20\d{2})\/", link)
        if year_match:
            return year_match.group(1)
        return "2021"

    def _parse_email_contact(self, item):
        """Parses the email for a committee's contact"""
        email_str = item.css("p.mt-1::text").extract()[2]
        return email_str.replace(": ", "")

    def _parse_meeting_schedule_info(self, committee_meta):
        """Parses out the weekday, and frequency of the meeting for calculating
        future dates"""
        # Add special case for downtown downtown meetings are the day before city
        # planning, so we calculate using the city planning schedule (1, and 3rd
        # Friday) and set a flag so we can subtract a day from the results
        committee_str = " ".join(committee_meta.css("p.mb-1::text").extract())
        is_downtown = "prior to the City Planning Commission" in committee_str

        if is_downtown:
            weekday = 4
            chosen_ordinals = [0, 2]
        else:
            weekday_str = committee_meta.css("p.mb-1 strong::text").extract_first()
            weekday = self._parse_weekday(weekday_str)
            raw_weeks = re.findall(r"1st|2nd|3rd|4th", committee_str)
            # ordinals here just refer to the 1st, 2nd etc...
            chosen_ordinals = [self._parse_ordinal(ordinal) for ordinal in raw_weeks]
        return weekday, chosen_ordinals, is_downtown

    def _parse_weekday(self, weekday):
        """Parses weekday strings as their integer equivalent"""
        # we cut off the last char of weekday, because it comes through with
        # an 's' i.e. 'Tuesdays'
        return time.strptime(weekday[:-1], "%A").tm_wday

    def _parse_ordinal(self, ordinal_str):
        """Parses ordinals as their integer equivalent beginning from 0"""
        ordinal_lookup = {"1st": 0, "2nd": 1, "3rd": 2, "4th": 3}
        return ordinal_lookup[ordinal_str.lower()]

   
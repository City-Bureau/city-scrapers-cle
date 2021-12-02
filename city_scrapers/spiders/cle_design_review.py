import re
import calendar
import time
from datetime import datetime, date

from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import Selector


class CleDesignReviewSpider(CityScrapersSpider):
    name = "cle_design_review"
    agency = "Cleveland Design Review Advisory Committees"
    timezone = "America/Detroit"
    start_urls = [
        "https://planning.clevelandohio.gov/designreview/schedule.php"  # noqa
    ]
    time_notes = "Due to Covid meetings are generally being held on WebEx rather than in person. For more information contact "

    def parse(self, response):
        """
            There's no element that wraps both the committee name/time  and the dropdown containing the
            agendas.  As such we want to grab each committee name/times and then use the following dropdown
            to get the agendas.  Luckily all of the committee name/times are (and are the only thing in) divs with 
            the class '.mt-3' so we can grab all the divs with those classes and then look for the next sibling div with
            the ".dropdown" class to get the links to all the agendas.

            Note that the city planning meeting is handled by a different scraper so we do look at it here. Luckily
            the name/times for the city planning meeting are not currently wrapped in a div, so the list of nodes
            described above won't include it.

            There are three other points to keep in mind for this scraper:
            1. The way the data is presented doesn't make it easy to know whether or not a meeting occurred but doesn't have an
               agenda, or whether a meeting is going to happen on a normal meeting date.  The strategy I'm using is to treat
               the agenda links as authoritative for past (and if listed upcoming) meetings.  So previous meetings are just read off of the
               agenda links.  For future meetings we take the date of the most recent agenda  and then
               calculate the remaining meetings this year from that date.  As dates progress and agendas are added, those tentative meetings
               will either be confirmed to exist or disappear based on the ways the agendas are updated.

            2. There is no mention of the year anywhere in the text of the site.  We can extract it from the agenda link - at least
               for now. But it will be important to keep an eye on how the site is changed in January.

            3. Meetings are currently not being held in person but over webex.  We've included this information in the time_notes section of the
               meeting. Perhaps a more general notes section would make a bit more sense, but given the current fields on the 
               meeting object, time notes seemed like a reasonable place to put this.       
        """
        committee_metas = response.css("div.mt-3")  # this skips city planning since it is handled by a separate scraper
        committee_agendas = response.css("div.mt-3 + div.dropdown")
        if len(committee_metas) !=  len(committee_agendas):
            # we haven't sucessfully  extracted matched metas and agendas so we can't safely iterate over them together.
            raise ValueError("Cannot match committee agandas to committee metadata")
        committee_items = zip(committee_metas, committee_agendas)

        for committee_meta, commitee_agenda_list in committee_items:
            title = self._parse_title(committee_meta)
            if not title:
                continue
            location = self._parse_location(committee_meta)
            time_str = self._parse_time_str(committee_meta)
            email_contact = self._parse_email_contact(committee_meta)
            for agenda in commitee_agenda_list.css("div.dropdown-menu a.dropdown-item"):
                month_str, day_str = agenda.css("*::text").extract_first().strip().split(" ")
                year_str = self._parse_year_from_agenda_link(agenda)
                
                start = self._parse_start(year_str, month_str, day_str, time_str)
                if not start:
                    continue
                meeting = Meeting(
                    title=title,
                    description="",
                    classification=ADVISORY_COMMITTEE,
                    start=start,
                    end=None,
                    all_day=False,
                    time_notes=self.time_notes + email_contact,
                    location=location,
                    links=self._parse_links(agenda, response),
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
        desc_text = " ".join(item.css("p.mb-1::text").extract())
        time_match = re.search(r"\d{1,2}:\d{2}\s*[apm]{2}", desc_text)
        if time_match:
            return time_match.group().replace(" ", "")
        return "12:00am"

    def _parse_start(self, year_str, month_str, day_str, time_str):
        """Parse start datetime as a naive datetime object."""
        date_str = " ".join([year_str, month_str, day_str, time_str])
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
        links = []
        links.append(
            {
                "title": "Agenda",
                "href": response.urljoin(item.attrib["href"]),
            }
        )
        return links

    def _parse_year_from_agenda_link(self, item):
        link = item.attrib["href"]
        year_match = re.search(r"\/(20\d{2})\/", link)
        if year_match:
            return year_match.group(1)
        return "2021"

    def _parse_email_contact(self, item):
        email_str = item.css("p.mt-1::text").extract()[2]
        return email_str.replace(": ", "")
      
    def _parse_weekday(self, weekday):
        return time.strptime(weekday, "%A").tm_wday


    def _calculate_upcoming_meeting_days(self, chosen_weekday, chosen_weeks, start, end):
        current_month = start.month
        current_year = start.year

        current_month_days = self._calculate_meeting_days_per_month(chosen_weekday, chosen_weeks, current_year, current_month)
        raw_days = [(day, current_month, current_year) for day in current_month_days]

        while not (current_month == end.month and current_year == end.year):
            current_month_days = self._calculate_meeting_days_per_month(chosen_weekday, chosen_weeks, current_year, current_month)
            raw_days.append([(day, current_month, current_year) for day in current_month_days])

            current_month = current_month+1 if current_month != 12 else 1
            if current_month == 1:
                current_year = current_year + 1
        
            # we now have all the relevant dates for the given months but we need to filter out days before and after start and end
            return [day, month, year in raw_days if 
            (not too_early(day, month, year, start)) and (not too_late(day, month, year, end))]


def calculate_upcoming_meeting_days(chosen_weekday, chosen_weeks, start, end):
    """
    This function is used to calculate meeting dates described as the 1 and 3rd Tuesday of a month for 
    any given time frame between start and end dates.

    Parameters:
    chosen_weekday (int): the weekday that you're looking for. Monday is 0, so in the examples above this would be 2
    chosen_weeks (int[]): the particular days you're looking for - like 1st and 3rd. These days should be passed though starting the count from 0, i.e [0, 2] for first and third 
    start (date): the first day to begin calculating meetings from 
    end (date): the final day to be considered as a potential meeting date

    Returns:
    []date: an array of dates that match the given conditions
    """
    current_month = start.month
    current_year = start.year

    # current_month_days = calculate_meeting_days_per_month(chosen_weekday, chosen_weeks, current_year, current_month)
    # raw_days = [(day, current_month, current_year) for day in current_month_days]

    raw_dates = []
    while not (current_month == end.month and current_year == end.year):
        current_month_days = _calculate_meeting_days_per_month(chosen_weekday, chosen_weeks, current_year, current_month)
        raw_dates  = raw_dates + [date(current_year, current_month, day) for day in current_month_days]

        # we can't easily use % arithmetic here since we're starting at 1, so it's a bit easier to read this way
        current_month = current_month+1 if current_month != 12 else 1
        if current_month == 1:
            current_year = current_year + 1
    
    # add the days for the final month since they're missed by the loop
    current_month_days = _calculate_meeting_days_per_month(chosen_weekday, chosen_weeks, current_year, current_month)
    raw_dates  = raw_dates + [date(current_year, current_month, day) for day in current_month_days]
    # we now have all the relevant dates for the given months but we need to filter out days before and after start and end
    return [current_date for current_date in raw_dates if (start <= current_date <= end)]

def _calculate_meeting_days_per_month(chosen_weekday, chosen_weeks, year, month):
    """
    This function is used to calculate meeting dates described as the 1 and 3rd Tuesday of a month.

    Parameters:
    chosen_weekday (int): the weekday that you're looking for. Monday is 0, so in the examples above this would be 2
    chosen_weeks (int[]): the particular days you're looking for - like 1st and 3rd. These days should be passed though starting the count from 0, i.e [0, 2] for first and third 
    year (int): the year as an integer
    month (int): the month as an integer

    Returns:
    []int: an array of the days of the month that matched the given conditions.
    """

    days_of_the_month = calendar.Calendar().itermonthdays2(year, month)
    # we create a list of all days in the month that are the proper weekday - day is 0 if it is outside the month
    # but present to make complete first or last weeks
    potential_days = [day for day, weekday in days_of_the_month if day != 0 and weekday == chosen_weekday]
    # we then add one to the index and see if the resulting number is in the chosen_weeks array
    chosen_days = [day for i, day in enumerate(potential_days) if (i) in chosen_weeks ]

    return chosen_days

import re
from datetime import datetime

from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from scrapy import Selector


class CleDesignReviewSpider(CityScrapersSpider):
    name = "cle_design_review"
    agency = "Cleveland Design Review Advisory Committees"
    timezone = "America/Detroit"
    start_urls = [
        "http://clevelandohio.gov/CityofCleveland/Home/Government/CityAgencies/CityPlanningCommission/MeetingSchedules"  # noqa
    ]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """

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
            1. The way the data is presented doesn't make it easy to know whether or not a meeting happened, but doesn't have an
               agenda, or whether a meeting is going to happen on a normal meeting date.  The strategy I'm using is to treat
               the agenda links as authoritative for past (and if listed upcoming) meetings.  So previous meetings are just read off of the
               agenda links.  For future meetings we take the greater of either: (a) the most recent agenda, or (b) the current day and then
               calculate the remaining meetings this year from that info.  As dates progress and agendas are added, those tentative meetings
               will either continue to exist or disappear based on the ways the agendas are updated.

            2. There is no mention of the year anywhere in the text of the site.  We can extract it from the agenda link - at least
               for now. But it will be important to keep an eye on how the site is changed in January.

            3. Meetings are currently not being held in person but over webex.  I've included this information in the time_notes section of the
               meeting. Perhaps a more general notes section would make a bit more sense, but given the current fields on the 
               meeting object, time notes seemed like a reasonable place to put this.       
        """

        page_content = response.css("#content .field-items .field-item")[0]
        bold_text = " ".join(page_content.css("strong *::text").extract())
        year_match = re.search(r"\d{4}(?= Agenda)", bold_text)
        if year_match:
            year_str = year_match.group()
        else:
            year_str = str(datetime.now().year)
        design_review_committees = re.split(r"\<hr.*?\>", page_content.extract())[1:]
        for committee in design_review_committees:
            committee_item = Selector(text=committee)
            title = self._parse_title(committee_item)
            if not title:
                continue
            location = self._parse_location(committee_item)
            time_str = self._parse_time_str(committee_item)
            for row in committee_item.css(".report tr"):
                month_str = (
                    row.css("td:first-child::text").extract_first().replace(".", "")
                )
                for date_cell in row.css("td:not(:first-child)"):
                    start = self._parse_start(date_cell, year_str, month_str, time_str)
                    if not start:
                        continue
                    meeting = Meeting(
                        title=title,
                        description="",
                        classification=ADVISORY_COMMITTEE,
                        start=start,
                        end=None,
                        all_day=False,
                        time_notes="",
                        location=location,
                        links=self._parse_links(date_cell, response),
                        source=response.url,
                    )

                    meeting["status"] = self._get_status(meeting)
                    meeting["id"] = self._get_id(meeting)

                    yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        committee_strs = [
            c.strip()
            for c in item.css("p > strong::text").extract()
            if c.strip().upper().endswith("DESIGN REVIEW COMMITTEE")
        ]
        if len(committee_strs):
            return committee_strs[0].title()

    def _parse_time_str(self, item):
        desc_text = " ".join(item.css("p *::text").extract())
        time_match = re.search(r"\d{1,2}:\d{2}\s*[apm]{2}", desc_text)
        if time_match:
            return time_match.group().replace(" ", "")
        return "12:00am"

    def _parse_start(self, item, year_str, month_str, time_str):
        """Parse start datetime as a naive datetime object."""
        cell_text = " ".join(item.css("* ::text").extract())
        date_text = re.sub(r"\D", "", cell_text)
        if not date_text or "No meeting" in cell_text:
            return
        date_str = " ".join([year_str, month_str, date_text, time_str])
        return datetime.strptime(date_str, "%Y %b %d %I:%M%p")

    def _parse_location(self, item):
        """Parse or generate location."""
        desc_str = " ".join(item.css("p[id] *::text").extract())
        # Override for first committee
        if "CITYWIDE" in desc_str:
            desc_str = " ".join(
                [l for l in item.css("p *::text").extract() if "days" in l]
            )
        loc_str = re.sub(r"\s+", " ", re.split(r"(\sin\s|\sat\s)", desc_str)[-1])
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
        if "Cleveland" not in loc_addr:
            loc_addr = loc_addr.strip() + " Cleveland, OH"
        return {
            "name": loc_name.strip(),
            "address": loc_addr.strip(),
        }

    def _parse_links(self, item, response):
        links = []
        for link in item.css("a"):
            links.append(
                {
                    "title": " ".join(link.css("*::text").extract()).strip(),
                    "href": response.urljoin(link.attrib["href"]),
                }
            )
        return links

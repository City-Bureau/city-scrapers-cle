import re
from collections import defaultdict
from datetime import datetime

from city_scrapers_core.constants import ADVISORY_COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CleMayorInfrastructureSpider(CityScrapersSpider):
    name = "cle_mayor_infrastructure"
    agency = "Cleveland Mayor's Infrastructure and Streetscape Advisory Committee"
    timezone = "America/Detroit"
    start_urls = ["http://planning.city.cleveland.oh.us/designreview/schedule.php"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        section = response.css(
            ".table0 > tr:nth-child(2) > td > table > tr:nth-child(5) > td"
        )
        agenda_map = self._parse_agendas(section, response)
        year_str = str(datetime.now().year)
        agenda_dates = list(agenda_map.keys())
        if len(agenda_dates) > 0:
            year_str = str(agenda_dates[0].year)

        for start_date in self._parse_table_starts(section, year_str):
            meeting = Meeting(
                title="Advisory Committee",
                description="",
                classification=ADVISORY_COMMITTEE,
                start=self._parse_start(section, start_date),
                end=None,
                all_day=False,
                time_notes="",
                location=self._parse_location(section),
                links=agenda_map[start_date],
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        return re.sub(
            r"\s+", " ", " ".join(item.css("span.h1 *::text").extract()).title()
        ).strip()

    def _parse_start(self, item, start_date):
        """Parse start datetime as a naive datetime object."""
        desc_str = " ".join(item.css("span.body1 *::text").extract())
        time_str = "12:00am"
        time_fmt = "%I:%M%p"
        time_match = re.search(r"\d{1,2}(\:\d{2})?\s+[apm\.]{2,4}", desc_str)
        if time_match:
            time_str = re.sub(r"[ \.]", "", time_match.group()).strip()
        if ":" not in time_str:
            time_fmt = "%I%p"
        time_obj = datetime.strptime(time_str, time_fmt).time()
        return datetime.combine(start_date, time_obj)

    def _parse_table_starts(self, item, year_str):
        """Get start dates from table rows"""
        starts = []
        for row in item.css(".agendaTable tr"):
            month = row.css("strong::text").extract_first().replace(".", "")
            for date_cell in row.css("td:not(:first-child)::text").extract():
                date_match = re.search(r"([a-zA-Z]{3}\s+)?\d{1,2}", date_cell)
                if not date_match:
                    continue
                month_str = month
                date_str = re.sub(r"\s+", " ", date_match.group()).strip()
                if " " in date_str:
                    month_str, date_str = date_str.split(" ")
                starts.append(
                    datetime.strptime(
                        " ".join([year_str, month_str, date_str]), "%Y %b %d"
                    ).date()
                )
        return starts

    def _parse_location(self, item):
        """Parse or generate location."""
        desc_str = " ".join(item.css("span.body1")[0].css("*::text").extract())
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
        elif "-" not in loc_str:
            loc_name, loc_addr = re.split(r",", loc_str, 1)
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

    def _parse_agendas(self, item, response):
        """Parse or generate links."""
        agenda_map = defaultdict(list)
        for agenda_link in item.css("option"):
            date_match_y = re.search(r"\d{4}-\d{2}-\d{2}", agenda_link.attrib["value"])
            date_match_mo = re.search(
                r"\d{1,2}-\d{1,2}-\d{2}", agenda_link.attrib["value"]
            )
            if not date_match_y and not date_match_mo:
                continue
            if date_match_y:
                date_obj = datetime.strptime(date_match_y.group(), "%Y-%m-%d").date()
            elif date_match_mo:
                date_obj = datetime.strptime(date_match_mo.group(), "%m-%d-%y").date()
            agenda_map[date_obj].append(
                {
                    "title": "Agenda",
                    "href": response.urljoin(agenda_link.attrib["value"]),
                }
            )
        return agenda_map

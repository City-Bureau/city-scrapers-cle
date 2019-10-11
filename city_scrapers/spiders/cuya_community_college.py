import re
from datetime import datetime
from io import BytesIO, StringIO

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams


class CuyaCommunityCollegeSpider(CityScrapersSpider):
    name = "cuya_community_college"
    agency = "Cuyahoga Community College"
    timezone = "America/Detroit"
    start_urls = ["https://www.tri-c.edu/administrative-departments/tri-c-board-of-trustees.html"]

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        self.agenda_map = {}
        agenda_url = None
        for link in response.css("article a"):
            link_title = " ".join(link.css("*::text").extract()).strip()
            if "Calendar" in link_title:
                self.calendar_url = response.urljoin(link.attrib["href"])
            if "Agenda" in link_title:
                agenda_url = response.urljoin(link.attrib["href"])
        if agenda_url:
            yield response.follow(agenda_url, callback=self._parse_agenda_res, dont_filter=True)
        else:
            yield response.follow(
                self.calendar_url, callback=self._parse_calendar, dont_filter=True
            )

    def _parse_agenda_res(self, response):
        self._parse_agenda(response)
        yield response.follow(self.calendar_url, callback=self._parse_calendar, dont_filter=True)

    def _parse_agenda(self, response):
        lp = LAParams(line_margin=5.0)
        out_str = StringIO()
        extract_text_to_fp(BytesIO(response.body), out_str, laparams=lp)
        pdf_text = out_str.getvalue()
        date_match = re.search(r"[A-Z][a-z]{2,8} \d{1,2},? \d{4}", pdf_text)
        if date_match:
            date_str = date_match.group().replace(",", "")
            date_obj = datetime.strptime(date_str, "%B %d %Y").date()
            self.agenda_map[date_obj] = [{"title": "Agenda", "href": response.url}]

    def _parse_calendar(self, response):
        lp = LAParams(line_margin=5.0)
        out_str = StringIO()
        extract_text_to_fp(BytesIO(response.body), out_str, laparams=lp)
        pdf_text = out_str.getvalue()
        split_dates = re.split(r"([A-Z][a-z]{2,8}\s+\d{1,2}, \d{4}[ \n$])", pdf_text, flags=re.M)
        date_groups = [split_dates[1]]
        for split_str in split_dates[2:]:
            if re.search(r"([A-Z][a-z]{2,8}\s+\d{1,2}, \d{4}[ \n$])", split_str):
                date_groups.append(split_str)
            else:
                date_groups[-1] = date_groups[-1] + split_str

        for date_item_str in date_groups:
            item = re.sub(r" +", " ", date_item_str).strip()
            start = self._parse_start(item)
            if not start:
                continue
            meeting = Meeting(
                title="Board of Trustees",
                description="",
                classification=BOARD,
                start=start,
                end=None,
                all_day=False,
                time_notes="",
                location=self._parse_location(item),
                links=self.agenda_map.get(start.date(), []),
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting, text=item)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_start(self, item):
        """Parse start datetime as a naive datetime object."""
        date_match = re.search(r"^[A-Z][a-z]{2,8} \d{1,2}, \d{4}", item)
        if not date_match or len(re.findall(r"\d{4}", item.split("\n")[0])) > 1:
            return
        date_str = date_match.group()
        time_match = re.search(r"\d{1,2}(:\d\d) [apm\.]{2,4}", item)
        time_str = "12:00 am"
        if time_match:
            time_str = time_match.group().replace(".", "")
        dt_fmt = "%B %d, %Y%I:%M %p"
        if ":" not in time_str:
            dt_fmt = "%B %d, %Y%I %p"
        return datetime.strptime(date_str + time_str, dt_fmt)

    def _parse_location(self, item):
        """Parse or generate location."""
        split_item = [i.strip() for i in item.split("\n") if i.strip()]
        loc_str = split_item[2]
        loc_map = {
            "JSTC – Ford Room": {
                "name": "Jerry Sue Thornton Center - Ford Room",
                "address": "2500 E 22nd St, Cleveland, OH 44115",
            },
            "WESTSHORE": {
                "name": "Westshore Campus",
                "address": "31001 Clemens Rd, Westlake, OH 44145",
            },
            "WEST": {
                "name": "Western Campus",
                "address": "11000 Pleasant Valley Rd, Parma, OH 44130",
            },
            "METRO – Campus Center Metro Room 201": {
                "name": "Metropolitan Campus - Campus Center Metro Room 201",
                "address": "2900 Community College Ave, Cleveland, OH 44115",
            },
            "EAST": {
                "name": "Eastern Campus",
                "address": "4250 Richmond Rd, Highland Hills, OH 44122"
            },
            "ATTC": {
                "name": "Advanced Technology Training Center",
                "address": "3409 Woodland Ave, Cleveland, OH 44115",
            },
            "CCE Room 238": {
                "name": "Corporate College East - Room 238",
                "address": "4400 Richmond Rd, Warrensville Heights, OH 44128",
            },
        }
        return loc_map.get(loc_str, {"name": loc_str, "address": ""})

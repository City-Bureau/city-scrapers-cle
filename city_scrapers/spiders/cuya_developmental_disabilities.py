import re
from datetime import datetime
from io import BytesIO, StringIO

from city_scrapers_core.constants import BOARD, FORUM
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams


class CuyaDevelopmentalDisabilitiesSpider(CityScrapersSpider):
    name = "cuya_developmental_disabilities"
    agency = "Cuyahoga County Developmental Disabilities Board"
    timezone = "America/Detroit"
    allowed_domains = ["www.cuyahogabdd.org"]
    start_urls = ["http://www.cuyahogabdd.org/en-US/Calendar.aspx"]
    location = {
        "name": "M. A. Donzella Administration Building",
        "address": "1275 Lakeside Ave East, Cleveland, OH 44114",
    }

    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for link in response.css(".padding li a"):
            link_text = " ".join(link.css("*::text").extract())
            if "Schedule" in link_text:
                yield response.follow(
                    link.attrib["href"], callback=self._parse_pdf, dont_filter=True
                )

    def _parse_pdf(self, response):
        """Parse data from PDF file of schedule"""
        lp = LAParams(line_margin=5.0)
        out_str = StringIO()
        extract_text_to_fp(BytesIO(response.body), out_str, laparams=lp)
        pdf_text = out_str.getvalue()
        split_dates = re.split(r"([A-Z][a-z]{2,8}\s+\d{1,2}[ \n$])", pdf_text)
        desc_str = split_dates[0]
        self._validate_location(desc_str)

        date_groups = [split_dates[1]]
        for split_line in split_dates[2:]:
            if re.search(r"([A-Z][a-z]{2,8}\s+\d{1,2}[ \n$])", split_line):
                date_groups.append(split_line)
            else:
                date_groups[-1] = date_groups[-1] + split_line
        year_str = re.search(r"\d{4}", desc_str).group()

        for date_group in date_groups:
            item = date_group.strip()
            date_str = re.search(r"^[A-Z][a-z]{2,8} \d{2}", item).group()
            if "Hearing" in item:
                time_strs = [t[0] for t in re.findall(r"(\d{1,2}(:\d{2})? [APM]{2})", item)]
                details = [("Public Hearing", time_strs[0].lower()),
                           ("Board", time_strs[1].lower())]
            else:
                details = [("Board", "5:30 pm")]

            for title, start_str in details:
                meeting = Meeting(
                    title=title,
                    description="",
                    classification=self._parse_classification(title),
                    start=self._parse_start(date_str, start_str, year_str),
                    end=None,
                    all_day=False,
                    time_notes="",
                    location=self.location,
                    links=[],
                    source=response.url,
                )

                meeting["status"] = self._get_status(meeting, text=item)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _parse_classification(self, title):
        """Parse or generate classification from allowed options."""
        if "Hearing" in title:
            return FORUM
        return BOARD

    def _parse_start(self, date_str, time_str, year_str):
        """Parse start datetime as a naive datetime object."""
        dt_fmt = "%B %d %Y %I:%M %p"
        if ":" not in time_str:
            dt_fmt = "%B %d %Y %I %p"
        return datetime.strptime(" ".join([date_str, year_str, time_str]), dt_fmt)

    def _validate_location(self, text):
        """Parse or generate location."""
        if "1275" not in text:
            raise ValueError("Meeting location has changed")

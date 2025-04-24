from collections import defaultdict

from city_scrapers_core.constants import CITY_COUNCIL, COMMITTEE
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import LegistarSpider


class CleCityCouncilSpider(LegistarSpider):
    name = "cle_city_council"
    agency = "Cleveland City Council"
    timezone = "America/Detroit"
    start_urls = ["https://cityofcleveland.legistar.com/Calendar.aspx"]
    link_types = []

    def _parse_legistar_events(self, response):
        events_table = response.css("table.rgMasterTable")[0]

        headers = []
        for header in events_table.css("th[class^='rgHeader']"):
            header_text = (
                " ".join(header.css("*::text").extract()).replace("&nbsp;", " ").strip()
            )
            header_inputs = header.css("input")
            if header_text:
                headers.append(header_text)
            elif len(header_inputs) > 0:
                headers.append(header_inputs[0].attrib["value"])
            else:
                headers.append(header.css("img")[0].attrib["alt"])

        events = []
        rows = events_table.css("tr.rgRow, tr.rgAltRow")

        for _, row in enumerate(rows):
            try:
                data = defaultdict(lambda: None)

                for header, field in zip(headers, row.css("td")):
                    field_text = (
                        " ".join(field.css("*::text").extract())
                        .replace("&nbsp;", " ")
                        .strip()
                    )
                    url = None
                    if len(field.css("a")) > 0:
                        link_el = field.css("a")[0]
                        if "onclick" in link_el.attrib and link_el.attrib[
                            "onclick"
                        ].startswith(("radopen('", "window.open", "OpenTelerikWindow")):
                            url = response.urljoin(
                                link_el.attrib["onclick"].split("'")[1]
                            )
                        elif "href" in link_el.attrib:
                            url = response.urljoin(link_el.attrib["href"])

                    if url and ("View.ashx?M=IC" in url):
                        data["iCalendar"] = {"url": url}
                    elif url:
                        value = {"label": field_text, "url": url}
                        data[header] = value
                    else:
                        data[header] = field_text

                if data:
                    events.append(dict(data))
            except Exception as e:
                print(f"Error processing row: {str(e)}")

        return events

    def parse_legistar(self, events):
        """
        `parse_legistar` should always `yield` Meeting items.

        Change the `_parse_title`, `_parse_start`, etc methods to fit your scraping
        needs.
        """
        for event in events:
            start = self.legistar_start(event)
            if start:
                meeting = Meeting(
                    title=event["Name"]["label"],
                    description=self._parse_description(event),
                    classification=self._parse_classification(event),
                    start=start,
                    end=None,
                    all_day=False,
                    time_notes="",
                    location=self._parse_location(event),
                    links=self.legistar_links(event),
                    source=self.legistar_source(event),
                )

                meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)

                yield meeting

    def _parse_description(self, item):
        """Parse or generate meeting description."""
        location = item.get("Meeting Location", "")
        if isinstance(location, dict):
            location = location.get("label", "")
        if "--em--" not in location:
            return ""
        return " ".join(location.split("--em--")[1:]).strip()

    def _parse_classification(self, item):
        """Parse or generate classification from allowed options."""
        if "committee" in item["Name"]["label"].lower():
            return COMMITTEE
        return CITY_COUNCIL

    def _parse_location(self, item):
        """Parse or generate location."""
        location = item.get("Meeting Location", "")
        if isinstance(location, dict):
            location = location.get("label", "")
        return {
            "address": "601 Lakeside Ave Cleveland OH 44114",
            # Might miss rare edge cases, but will be captured in name
            "name": location.split("--em--")[0],
        }

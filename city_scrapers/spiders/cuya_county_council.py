import json
from datetime import datetime, timedelta

import pytz
from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class CuyaCountyCouncilSpider(CityScrapersSpider):
    name = "cuya_county_council"
    agency = "Cuyahoga County Council"
    timezone = "America/Detroit"
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {"Content-Type": "application/json"}
    }  # noqa
    location = {
        "address": "4th Floor 2079 East 9th Street",
        "name": "C. Ellen Connally Council Chambers",
    }

    @property
    def start_urls(self):
        start_date = datetime.now() + timedelta(days=-90)
        end_date = datetime.now() + timedelta(days=90)
        start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
        end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
        url = f"https://www.cuyahogacounty.gov/web-interface/events?StartDate={start_date_str}&EndDate={end_date_str}&EventSchedulerViewMode=month&UICulture=&Id=175b0fba-07f2-4b3e-a794-e499e98c0a93&CurrentPageId=b38b8f62-8073-4d89-9027-e7a13e53248e&sf_site=f3ea71cd-b8c9-4a53-b0db-ee5d552472fc"  # noqa
        return [url]

    def parse(self, response):
        """
        Parse JSON response and return list of Meeting items.
        """
        data = json.loads(response.text)
        for item in data:
            start = self._parse_date(item.get("Start", ""))
            if start is None:
                continue
            meeting = Meeting(
                title=item.get("Title", ""),
                description=item.get("Description", ""),
                # Although they're a "council", commission seems like the
                # closest classification among our constants
                classification=COMMISSION,
                start=start,
                # "End" is included in JSON but is always the same as start
                end=None,
                all_day=item.get("IsAllDay", False),
                time_notes="",
                location=self.location,
                links=[],
                source=response.url,
            )

            meeting["status"] = self._get_status(meeting, text=item["Title"])
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_date(self, date_str):
        """Convert a millisecond unix timestamp in a string that looks like:
        "/Date(1714399200000)/"
        To a timezone naive datetime object.
        """
        # Remove the surrounding identifiers and convert to a proper timestamp
        clean_date_str = date_str.replace("/Date(", "").replace(")/", "")
        try:
            timestamp = int(int(clean_date_str) / 1000)

            # Convert the timestamp to a datetime object
            date = datetime.fromtimestamp(timestamp)
            date = date.replace(tzinfo=pytz.utc)

            # Convert the UTC datetime to the local timezone
            local_date = date.astimezone(pytz.timezone(self.timezone))
        except ValueError:
            self.logger.error(f"Unable to parse date: {date_str}")
            return None

        # make timezone naive
        return local_date.replace(tzinfo=None)

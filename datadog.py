import os

from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.rum_api import RUMApi
from datadog_api_client.v2.model.rum_query_filter import RUMQueryFilter
from datadog_api_client.v2.model.rum_query_options import RUMQueryOptions
from datadog_api_client.v2.model.rum_query_page_options import RUMQueryPageOptions
from datadog_api_client.v2.model.rum_search_events_request import RUMSearchEventsRequest
from datadog_api_client.v2.model.rum_sort import RUMSort


class DatadogRum:
    DATADOG_HOST = os.environ.get("DATADOG_HOST") or "https://us5.datadoghq.com"

    def __init__(self):
        self.configuration = Configuration(host=DatadogRum.DATADOG_HOST)

    def _generate_body(self, email):
        query = f"@type:session AND @usr.email:{email}"
        body = RUMSearchEventsRequest(
            filter=RUMQueryFilter(
                _from="now-1h",
                query=query,
                to="now",
            ),
            options=RUMQueryOptions(
                time_offset=0,
                timezone="GMT",
            ),
            page=RUMQueryPageOptions(
                limit=25,
            ),
            sort=RUMSort("timestamp"),
        )
        return body

    def generate_url(self, session):
        session_id = session.attributes.attributes.get("session").get("id")
        seed = session.attributes.attributes.get("session").get("initial_view").get("id")
        ts = int(session.attributes.timestamp.timestamp() * 1000)
        # Build the URL
        url = f"{DatadogRum.DATADOG_HOST}/rum/replay/sessions/{session_id}?seed={seed}&ts={ts}"
        return url

    def get_rum_sessions(self, email):
        rum_body = self._generate_body(email=email)
        with ApiClient(self.configuration) as api_client:
            api_instance = RUMApi(api_client)
            sessions = api_instance.search_rum_events(body=rum_body)

        urls = [self.generate_url(session) for session in sessions.data]
        return urls

# coding=utf-8

import mock
from nose.tools import assert_equal, assert_true, assert_in, assert_not_in
from lxml import html
from ...helpers import BaseApplicationTest
from dmapiclient import APIError


class TestApplication(BaseApplicationTest):
    def setup(self):
        super(TestApplication, self).setup()

    def test_analytics_code_should_be_in_javascript(self):
        res = self.client.get('/static/javascripts/application.js')
        assert_equal(200, res.status_code)
        assert_true(
            'trackPageview'
            in res.get_data(as_text=True))

    def test_should_use_local_cookie_page_on_cookie_message(self):
        res = self.client.get('/')
        assert_equal(200, res.status_code)
        assert_true(
            '<p>GOV.UK uses cookies to make the site simpler. <a href="/cookies">Find out more about cookies</a></p>'
            in res.get_data(as_text=True)
        )


class TestHomepageBrowseList(BaseApplicationTest):
    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_dos_links_not_shown_when_dos_is_pending(self, data_api_client):
        with self.app.app_context():
            data_api_client.find_frameworks.return_value = {"frameworks": [
                {"slug": "digital-outcomes-and-specialists",
                 "status": "pending"}
            ]}

            res = self.client.get("/")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            link_texts = [item.text_content().strip() for item in document.cssselect('.browse-list-item a')]
            assert link_texts[0] == "Find cloud technology and support"
            assert link_texts[-2] == "Find specialists to work on digital projects"
            assert link_texts[-1] == "Digital Services"

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_dos_links_are_shown_when_dos_is_live(self, data_api_client):
        with self.app.app_context():
            data_api_client.find_frameworks.return_value = {"frameworks": [
                {"slug": "digital-outcomes-and-specialists",
                 "status": "live"}
            ]}

            res = self.client.get("/")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            link_texts = [item.text_content().strip() for item in document.cssselect('.browse-list-item a')]
            assert link_texts[0] == "Find an individual specialist"
            assert link_texts[-1] == "Buy physical datacentre space for legacy systems"
            assert "Find specialists to work on digital projects" not in link_texts

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_buyer_dashboard_link_exists_when_dos_is_live_and_buyer_logged_in(self, data_api_client):
        with self.app.app_context():
            data_api_client.find_frameworks.return_value = {"frameworks": [
                {"slug": "digital-outcomes-and-specialists",
                 "status": "live"}
            ]}
            self.login_as_buyer()

            res = self.client.get("/")
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 200

            link_texts = [item.text_content().strip() for item in document.cssselect('.browse-list-item a')]
            assert link_texts[-1] == "View your requirements and supplier responses"


class TestHomepageSidebarMessage(BaseApplicationTest):
    def setup(self):
        super(TestHomepageSidebarMessage, self).setup()

    @staticmethod
    def _find_frameworks(framework_slugs_and_statuses):

        _frameworks = []

        for index, framework_slug_and_status in enumerate(framework_slugs_and_statuses):
            framework_slug, framework_status = framework_slug_and_status
            _frameworks.append({
                'framework': 'framework',
                'slug': framework_slug,
                'id': index + 1,
                'status': framework_status,
                'name': 'Framework'
            })

        return {
            'frameworks': _frameworks
        }

    @staticmethod
    def _assert_message_container_is_empty(response_data):
        document = html.fromstring(response_data)
        message_container = document.xpath('//div[@class="supplier-messages column-one-third"]/aside')
        assert len(message_container) == 0

    @staticmethod
    def _assert_message_container_is_not_empty(response_data):
        document = html.fromstring(response_data)
        message_container = document.xpath('//div[@class="supplier-messages column-one-third"]/aside')
        assert len(message_container) == 1

        assert message_container[0].xpath('h2/text()')[0].strip() == "Sell services"

    @mock.patch('app.main.views.marketplace.data_api_client')
    def _load_homepage(self, framework_slugs_and_statuses, framework_messages, data_api_client):

        data_api_client.find_frameworks.return_value = self._find_frameworks(framework_slugs_and_statuses)
        res = self.client.get('/')
        assert_equal(200, res.status_code)
        response_data = res.get_data(as_text=True)

        if framework_messages:
            self._assert_message_container_is_not_empty(response_data)
            for message in framework_messages:
                assert_in(message, response_data)
        else:
            self._assert_message_container_is_empty(response_data)

    def test_homepage_sidebar_message_exists_dos_coming(self):

        framework_slugs_and_statuses = [
            ('g-cloud-7', 'pending'),
            ('digital-outcomes-and-specialists', 'coming')
        ]
        framework_messages = [
            u"Become a Digital Outcomes and Specialists supplier",
            u"Digital Outcomes and Specialists will be open for applications soon."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

    def test_homepage_sidebar_message_exists_dos_open(self):

        framework_slugs_and_statuses = [
            ('g-cloud-7', 'pending'),
            ('digital-outcomes-and-specialists', 'open')
        ]
        framework_messages = [
            u"Become a Digital Outcomes and Specialists supplier",
            u"Digital Outcomes and Specialists is open for applications."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

    def test_homepage_sidebar_message_exists_g_cloud_7_pending(self):

        framework_slugs_and_statuses = [
            ('g-cloud-7', 'pending')
        ]
        framework_messages = [
            u"G‑Cloud 7 is closed for applications",
            u"G‑Cloud 7 services will be available from 23 November 2015."
        ]

        self._load_homepage(framework_slugs_and_statuses, framework_messages)

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_homepage_sidebar_no_log_in_message_if_logged_out(self, data_api_client):
        data_api_client.find_frameworks.return_value = self._find_frameworks([
            ('digital-outcomes-and-specialists', 'live')
        ])
        res = self.client.get('/')
        assert res.status_code == 200
        response_data = res.get_data(as_text=True)

        document = html.fromstring(response_data)

        link_to_dashboard = document.xpath(
            '//div[@class="supplier-messages column-one-third"]/aside/p[1]/a[@class="top-level-link"]')  # noqa

        assert len(link_to_dashboard) == 0

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_homepage_sidebar_log_in_message_if_logged_in(self, data_api_client):
        data_api_client.find_frameworks.return_value = self._find_frameworks([
            ('digital-outcomes-and-specialists', 'live')
        ])
        self.login_as_supplier()

        res = self.client.get('/')
        assert res.status_code == 200
        response_data = res.get_data(as_text=True)

        document = html.fromstring(response_data)

        link_to_dashboard = document.xpath(
            '//div[@class="supplier-messages column-one-third"]/aside/p[1]/a[@class="top-level-link"]')  # noqa

        assert len(link_to_dashboard) == 1
        assert link_to_dashboard[0].text.strip() == "View your services and account details"

    def test_homepage_sidebar_message_doesnt_exist_without_frameworks(self):
        framework_slugs_and_statuses = [
            ('g-cloud-2', 'expired'),
            ('g-cloud-3', 'expired'),
            ('g-cloud-4', 'expired')
        ]

        # there are no messages
        self._load_homepage(framework_slugs_and_statuses, None)

    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_api_error_message_doesnt_exist(self, data_api_client):

        data_api_client.find_frameworks.side_effect = APIError()
        res = self.client.get('/')
        assert_equal(200, res.status_code)
        self._assert_message_container_is_empty(res.get_data(as_text=True))

    # here we've given an valid framework with a valid status but there is no message.yml file to read from
    @mock.patch('app.main.views.marketplace.data_api_client')
    def test_g_cloud_6_open_blows_up(self, data_api_client):
        framework_slugs_and_statuses = [
            ('g-cloud-6', 'open')
        ]

        data_api_client.find_frameworks.return_value = self._find_frameworks(framework_slugs_and_statuses)
        res = self.client.get('/')
        assert_equal(500, res.status_code)


class TestStaticMarketplacePages(BaseApplicationTest):
    def setup(self):
        super(TestStaticMarketplacePages, self).setup()

    def test_cookie_page(self):
        res = self.client.get('/cookies')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>Cookies</h1>'
            in self._strip_whitespace(res.get_data(as_text=True))
        )

    def test_cookie_page(self):
        res = self.client.get('/terms-and-conditions')
        assert_equal(200, res.status_code)
        assert_true(
            '<h1>Termsandconditions</h1>'
            in self._strip_whitespace(res.get_data(as_text=True))
        )


class TestBriefPage(BaseApplicationTest):

    def setup(self):
        super(TestBriefPage, self).setup()

        self._data_api_client = mock.patch(
            'app.main.views.marketplace.data_api_client'
        ).start()

        self.brief = self._get_dos_brief_fixture_data()
        self._data_api_client.get_brief.return_value = self.brief

    def teardown(self):
        self._data_api_client.stop()

    def _assert_page_title(self, document):
        brief_title = self.brief['briefs']['title']
        brief_organisation = self.brief['briefs']['organisation']

        page_heading = document.xpath('//header[@class="page-heading-smaller"]')[0]
        page_heading_h1 = page_heading.xpath('h1/text()')[0]
        page_heading_context = page_heading.xpath('p[@class="context"]/text()')[0]

    def test_dos_brief_404s_if_brief_is_draft(self):
        self.brief['briefs']['status'] = 'draft'
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert_equal(404, res.status_code)

    def test_dos_brief_has_correct_title(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        self._assert_page_title(document)

    def test_dos_brief_has_at_least_one_section(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        section_heading = document.xpath('//h2[@class="summary-item-heading"]')[0]
        section_attributes = section_heading.xpath('following-sibling::table[1]/tbody/tr')

        start_date_key = section_attributes[0].xpath('td[1]/span/text()')
        start_date_value = section_attributes[0].xpath('td[2]/span/text()')

        contract_length_key = section_attributes[1].xpath('td[1]/span/text()')
        contract_length_value = section_attributes[1].xpath('td[2]/span/text()')

        assert_equal(section_heading.get('id'), 'opportunity-attributes-1')
        assert_equal(section_heading.text.strip(), 'Overview')
        assert_equal(start_date_key[0], 'Start date')
        assert_equal(start_date_value[0], '01/03/2016')
        assert_equal(contract_length_key[0], 'Contract length')
        assert_equal(contract_length_value[0], '4 weeks')

    def test_dos_brief_has_questions_and_answers(self):
        brief_id = self.brief['briefs']['id']
        res = self.client.get('/digital-outcomes-and-specialists/opportunities/{}'.format(brief_id))
        assert_equal(200, res.status_code)

        document = html.fromstring(res.get_data(as_text=True))

        xpath = '//h2[@id="clarification-questions"]/following-sibling::table/tbody/tr'
        clarification_questions = document.xpath(xpath)

        question = clarification_questions[0].xpath('td[1]/span/text()')
        answer = clarification_questions[0].xpath('td[2]/span/text()')

        assert_equal(question[0], "Why?")
        assert_equal(answer[0], "Because")
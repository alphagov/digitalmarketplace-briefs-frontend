
import mock
import re
from lxml import html

from app import data_api_client
from app.main.helpers import framework_helpers

from ...helpers import BaseApplicationTest


class UnavailableBanner(object):

    def __init__(self, document):
        self.banner = document.xpath(
            '//div[@id="wrapper"]//div[@class="banner-temporary-message-without-action"]'
        )

    @property
    def exists(self):
        return bool(self.banner)

    def heading_text(self):
        return self.banner[0].xpath('h2/text()')[0].strip()

    def body_text(self):
        return self.banner[0].xpath('p[@class="banner-message"]/text()')[0].strip()


class TestServicePage(BaseApplicationTest):

    def setup_method(self, method):
        super(TestServicePage, self).setup_method(method)

        self.supplier = self._get_supplier_fixture_data()

        # must use singleton API Client, see BaseApplicationTest.setup_method
        data_api_client.get_supplier = mock.Mock()
        data_api_client.get_supplier.return_value = self.supplier

        data_api_client.get_framework = mock.Mock()
        data_api_client.get_service = mock.Mock()

        self.lots = framework_helpers.get_lots_by_slug(
            self._get_framework_fixture_data('g-cloud-6')['frameworks']
        )

    def _assert_contact_details(self, document):

        supplier_name = self.supplier['suppliers']['name']
        contact_info = self.supplier['suppliers']['contactInformation'][0]

        meta = document.xpath('//div[@id="meta"]')[0]
        contact_heading = meta.xpath('//div/p[@class="contact-details-organisation"]/span/text()')[0]  # noqa
        ps = [
            p.text_content().strip()
            for p in meta.xpath('//div[@class="contact-details"]//p')
        ]

        assert contact_heading == supplier_name

        for contact_detail in [
            contact_info['contactName'],
            contact_info['phoneNumber'],
            contact_info['email']
        ]:
            assert "{}".format(contact_detail) in ps

    def _assert_document_links(self, document):

        service = self.service['services']

        # Hardcoded stuff comes from 'get_documents' in service_presenters.py
        url_keys = [
            'pricingDocumentURL',
            'sfiaRateDocumentURL',
            'serviceDefinitionDocumentURL',
            'termsAndConditionsDocumentURL'
        ]

        doc_hrefs = [a.get('href') for a in document.xpath(
            '//div[@id="meta"]//li[@class="document-list-item"]/a')]

        for url_key in url_keys:
            if url_key in self.service['services']:
                assert (
                    # Replace all runs of whitespace with a '%20'
                    self._replace_whitespace(service[url_key], '%20')
                    in doc_hrefs
                )

        if 'additionalDocumentURLs' in service:
            for document_url in service['additionalDocumentURLs']:
                assert (
                    self._replace_whitespace(document_url, '%20')
                    in doc_hrefs
                )

    def _replace_whitespace(self, string, replacement_substring):
            # Replace all runs of whitespace with replacement_substring
            return re.sub(r"\s+", replacement_substring, string)

    def _assert_breadcrumbs(self, document, lot):
        # check links exist back to
        # (1) digital marketplace,
        # (2) cloud tech and support,
        # (3) search page for lot

        # Hardcoded stuff found in 'views.py'
        breadcrumbs_expected = {
            '/': 'Digital Marketplace',
            '/g-cloud': 'Cloud technology and support',
            '/g-cloud/search?lot={}'.format(lot): self.lots[lot]['name']
        }

        breadcrumbs = document.xpath('//div[@id="global-breadcrumb"]//a')
        assert len(breadcrumbs) == 3

        for breadcrumb in breadcrumbs:
            breadcrumb_text = breadcrumb.text_content().strip()
            breakcrumb_href = breadcrumb.get('href').strip()
            # check that the link exists in our expected breadcrumbs
            assert breakcrumb_href in breadcrumbs_expected
            # check that the link text is the same
            assert breadcrumb_text == breadcrumbs_expected[breakcrumb_href]

    def _assert_service_page_url(self):

        service_id = self.service['services']['id']
        service_title = self.service['services']['title']
        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        page_title = document.xpath('//div[@id="wrapper"]//h1/text()')[0]
        assert page_title == "{}".format(service_title)

        self._assert_contact_details(document)
        self._assert_document_links(document)
        self._assert_breadcrumbs(document, self.service['services']['lot'])

    def _get_status_update_audit_event_for(self,
                                           update_type=None,
                                           old_status=None,
                                           new_status=None,
                                           timestamp=None,
                                           service=None):
        audit_event = {
            "links": {
                "oldArchivedService": "http://localhost:5000/archived-services/1",
                "self": "http://localhost:5000/audit-events",
                "newArchivedService": "http://localhost:5000/archived-services/2"
            },
            "type": update_type,
            "acknowledged": False,
            "user": "joebloggs",
            "id": 1,
            "createdAt": timestamp
        }

        if update_type is 'update_service_status':
            audit_event["data"] = {
                "supplierId": service["supplierId"],
                "newArchivedServiceId": 2,
                "new_status": new_status,
                "supplierName": service["supplierName"],
                "serviceId": service["id"],
                "old_status": old_status,
                "oldArchivedServiceId": 1
            }
        elif update_type is "framework_update":
            audit_event["data"] = {
                "update": {
                    "status": new_status,
                    "clarificationQuestionsOpen": True
                }
            }

        return audit_event

    def test_g5_service_page_url(self):
        data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-5')
        self.service = self._get_g5_service_fixture_data()
        data_api_client.get_service.return_value = self.service

        self._assert_service_page_url()

    def test_g6_service_page_url(self):
        data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-6')
        self.service = self._get_g6_service_fixture_data()
        data_api_client.get_service.return_value = self.service

        self._assert_service_page_url()

    def test_published_service_doesnt_have_unavailable_banner(self):
        self.service = self._get_g6_service_fixture_data()
        data_api_client.get_service.return_value = self.service
        data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-6')

        service_id = self.service['services']['id']
        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        unavailable_banner = UnavailableBanner(document)
        assert not unavailable_banner.exists

    def test_enabled_service_has_unavailable_banner(self):
        self.service = self._get_g6_service_fixture_data()

        self.service['services']['status'] = 'enabled'
        self.service['serviceMadeUnavailableAuditEvent'] = \
            self._get_status_update_audit_event_for(
                update_type='update_service_status',
                old_status='published',
                new_status='enabled',
                timestamp='2016-01-05T17:01:07.649587Z',
                service=self.service['services']
            )
        data_api_client.get_service.return_value = self.service
        data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-6')

        service_id = self.service['services']['id']
        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert res.status_code == 410

        document = html.fromstring(res.get_data(as_text=True))

        unavailable_banner = UnavailableBanner(document)
        assert unavailable_banner.exists
        assert unavailable_banner.heading_text() == '{} stopped offering this service on {}'.format(
            self.service['services']['supplierName'],
            'Tuesday 5 January 2016.',
        )
        assert unavailable_banner.body_text() == 'Any existing contracts for this service are still valid.'

    def test_disabled_service_has_unavailable_banner(self):
        self.service = self._get_g6_service_fixture_data()
        self.service['services']['status'] = 'disabled'
        self.service['serviceMadeUnavailableAuditEvent'] = \
            self._get_status_update_audit_event_for(
                update_type='update_service_status',
                old_status='published',
                new_status='disabled',
                timestamp='2016-01-05T17:01:07.649587Z',
                service=self.service['services']
            )
        data_api_client.get_service.return_value = self.service
        data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-6')

        service_id = self.service['services']['id']
        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert res.status_code == 410

        document = html.fromstring(res.get_data(as_text=True))

        unavailable_banner = UnavailableBanner(document)
        assert unavailable_banner.exists
        assert unavailable_banner.heading_text() == '{} stopped offering this service on {}'.format(
            self.service['services']['supplierName'],
            'Tuesday 5 January 2016.',
        )
        assert unavailable_banner.body_text() == 'Any existing contracts for this service are still valid.'

    def test_expired_framework_causes_service_to_have_unavailable_banner(self):
        self.service = self._get_g6_service_fixture_data()
        self.service['services']['frameworkStatus'] = 'expired'
        self.service['serviceMadeUnavailableAuditEvent'] = \
            self._get_status_update_audit_event_for(
                update_type='framework_update',
                old_status='live',
                new_status='expired',
                timestamp='2016-01-05T17:01:07.649587Z',
                service=self.service['services']
            )
        data_api_client.get_service.return_value = self.service
        data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-6')

        service_id = self.service['services']['id']
        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert res.status_code == 410

        document = html.fromstring(res.get_data(as_text=True))
        unavailable_banner = UnavailableBanner(document)
        assert unavailable_banner.exists
        assert unavailable_banner.heading_text() == 'This {} service is no longer available to buy.'.format(
            self.service['services']['frameworkName'],
        )
        assert unavailable_banner.body_text() == 'The {} framework expired on {}. Any existing contracts with {} are' \
            ' still valid.'.format(
                self.service['services']['frameworkName'],
                'Tuesday 5 January 2016',
                self.service['services']['supplierName'],
            )

    def test_pre_live_framework_causes_404(self):
        self.service = self._get_g6_service_fixture_data()
        self.service['services']['frameworkStatus'] = 'standstill'
        data_api_client.get_service.return_value = self.service
        data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-6')

        service_id = self.service['services']['id']

        res = self.client.get('/g-cloud/services/{}'.format(service_id))

        assert res.status_code == 404

    def test_service_on_framework_without_a_display_service_manifest_causes_404(self):
        self.service = self._get_g6_service_fixture_data()
        self.service['services']['frameworkSlug'] = 'digital-outcomes-and-specialists'
        data_api_client.get_service.return_value = self.service
        data_api_client.get_framework.return_value = self._get_framework_fixture_data(
            'digital-outcomes-and-specialists'
        )

        service_id = self.service['services']['id']
        # This is the "Display service" page, generally for G-Cloud services, but in this case it now has a valid
        # digital-outcomes-and-specialists service ID.  There is no "display_service" manifest, which will make the
        # content loader raise a ContentNotFoundError
        res = self.client.get('/g-cloud/services/{}'.format(service_id))

        assert res.status_code == 404

    def test_certifications_section_not_displayed_if_service_has_none(self):
        self.service = self._get_g6_service_fixture_data()
        self.service['services']['vendorCertifications'] = []
        data_api_client.get_service.return_value = self.service
        data_api_client.get_framework.return_value = self._get_framework_fixture_data('g-cloud-6')

        service_id = self.service['services']['id']

        res = self.client.get('/g-cloud/services/{}'.format(service_id))
        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))

        attribute_headings = document.xpath(
            '//div[@id="wrapper"]//div[@class="grid-row service-attributes"]' +
            '//h2/text()')

        attribute_headings = [
            heading.strip() for heading in attribute_headings]

        assert 'Certifications' not in attribute_headings

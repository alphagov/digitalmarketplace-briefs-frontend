describe("GOVUK.Analytics", function () {
  var analytics,
      sortCalls;

  SortCallsToGaByMethod = function (calls) {
    var gaMethodCalls = {},
        callNum = calls.length;

    while (callNum--) {
      var method = calls[callNum].args.shift(),
          args = calls[callNum].args;

      if (gaMethodCalls.hasOwnProperty(method)) {
        gaMethodCalls[method].push(args);
      } else {
        gaMethodCalls[method] = [args];
      }
    }
    this._calls = gaMethodCalls;
  };
  SortCallsToGaByMethod.prototype.callsTo = function (method) {
    if (this._calls.hasOwnProperty(method)) {
      return this._calls[method];
    }
    return [];
  };

  beforeEach(function () {
    window.ga = function() {};
    spyOn(window, 'ga');
  });

  describe('when initialised', function () {

    it('should initialise pageviews, events, track external links and virtual pageviews', function () {
      spyOn(window.GOVUK.GDM.analytics, 'register');
      spyOn(window.GOVUK.GDM.analytics.pageViews, 'init');
      spyOn(window.GOVUK.GDM.analytics.events, 'init');
      spyOn(window.GOVUK.GDM.analytics.trackExternalLinks, 'init');

      window.GOVUK.GDM.analytics.init();

      expect(window.GOVUK.GDM.analytics.register).toHaveBeenCalled();
      expect(window.GOVUK.GDM.analytics.pageViews.init).toHaveBeenCalled();
      expect(window.GOVUK.GDM.analytics.events.init).toHaveBeenCalled();
      expect(window.GOVUK.GDM.analytics.trackExternalLinks.init).toHaveBeenCalled();
    });
  });

  describe('when registered', function() {
    var universalSetupArguments;

    beforeEach(function() {
      GOVUK.GDM.analytics.init();
      universalSetupArguments = window.ga.calls.allArgs();
    });

    it('configures a universal tracker', function() {
      expect(universalSetupArguments).toContain(['create', 'UA-49258698-1', {
        'cookieDomain': document.domain
      }]);
      expect(universalSetupArguments).toContain(['send', 'pageview']);
    });
    it('configures a cross domain tracker', function() {
      expect(universalSetupArguments).toContain(['create', 'UA-145652997-1', 'auto', {
        'name': 'govuk_shared'
      }]);
      expect(universalSetupArguments).toContain(['require', 'linker']);
      expect(universalSetupArguments).toContain(['govuk_shared.require', 'linker']);
      expect(universalSetupArguments).toContain(['linker:autoLink', [ 'www.gov.uk' ]]);
      expect(universalSetupArguments).toContain(['govuk_shared.linker:autoLink', [ 'www.gov.uk' ]]);
      expect(universalSetupArguments).toContain(['govuk_shared.set', 'anonymizeIp', true ]);
      expect(universalSetupArguments).toContain(['govuk_shared.send', 'pageview']);
    });
  });

  describe('link tracking', function () {
    var mockLink,
        assetHost = 'https://assets.digitalmarketplace.service.gov.uk';

    beforeEach(function () {
      mockLink = document.createElement('a');
      window.ga.calls.reset();
    });

    it('sends the right event when an outcomes supplier responses download link is clicked', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1/responses');

      $(mockLink).append('<span class="document-icon">CSV</span><span> document:</span></span>');

      mockLink.appendChild(document.createTextNode('Download supplier responses to ‘Brief 1’'));
      mockLink.href = assetHost + '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1/responses/download';
      GOVUK.GDM.analytics.events.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.allArgs()).toContain(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'supplier response list | outcomes | 1',
        'transport': 'beacon'
      }]);
    });

    it('sends the right event when a digital specialists supplier responses download link is clicked', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1/responses');

      $(mockLink).append('<span class="document-icon">CSV</span><span> document:</span></span>');

      mockLink.appendChild(document.createTextNode('Download supplier responses to ‘Brief 1’'));
      mockLink.href = assetHost + '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1/responses/download';
      GOVUK.GDM.analytics.events.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.allArgs()).toContain(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'supplier response list | specialists | 1',
        'transport': 'beacon'
      }]);
    });

    it('sends the right event when a list of user research labs download link is clicked', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/buyers/frameworks/digital-outcomes-and-specialists/requirements/user-research-studios');

      $(mockLink).append('<span class="document-icon">CSV</span><span> document:</span></span>');
      mockLink.appendChild(document.createTextNode('List of labs'));
      mockLink.href = assetHost + '/digital-outcomes-and-specialists/communications/catalogues/user-research-studios.csv';
      GOVUK.GDM.analytics.events.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.allArgs()).toContain(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'list of user research labs',
        'transport': 'beacon'
      }]);
    });

    it('sends the right event when a list of user research participants download link is clicked', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/buyers/frameworks/digital-outcomes-and-specialists/requirements/user-research-participants');

      mockLink.appendChild(document.createTextNode('Download list of suppliers.'));
      mockLink.href = assetHost + '/digital-outcomes-and-specialists/communications/catalogues/user-research-participants-suppliers.csv';
      GOVUK.GDM.analytics.events.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.allArgs()).toContain(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'list of user research participant suppliers',
        'transport': 'beacon'
      }]);
    });

    it('sends the right event when a list of suppliers for digital specialists download link is clicked', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists');

      mockLink.appendChild(document.createTextNode('Download list of suppliers.'));
      mockLink.href = assetHost + '/digital-outcomes-and-specialists/communications/catalogues/digital-specialists-suppliers.csv';
      GOVUK.GDM.analytics.events.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.allArgs()).toContain(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'list of specialists suppliers',
        'transport': 'beacon'
      }]);
    });

    it('sends the right event when a list of suppliers for digital outcomes download link is clicked', function() {
      spyOn(GOVUK.GDM.analytics.location, "pathname")
        .and
        .returnValue('/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes');

      mockLink.appendChild(document.createTextNode('Download list of suppliers.'));
      mockLink.href = assetHost + '/digital-outcomes-and-specialists/communications/catalogues/digital-outcomes-suppliers.csv';
      GOVUK.GDM.analytics.events.supplierListDownload({ 'target': mockLink });
      expect(window.ga.calls.allArgs()).toContain(['send', {
        'hitType': 'event',
        'eventCategory': 'download',
        'eventAction': 'csv',
        'eventLabel': 'list of outcomes suppliers',
        'transport': 'beacon'
      }]);
    });
  });

  describe("Virtual Page Views", function () {
    var $analyticsString;

    afterEach(function () {
      $analyticsString.remove();
    });

    it("Should not call google analytics without a url", function () {
      $analyticsString = $("<div data-analytics='trackPageView'/>");
      $(document.body).append($analyticsString);
      window.GOVUK.GDM.analytics.virtualPageViews();
      expect(window.ga.calls.any()).toEqual(false);
    });

    it("Should call google analytics if url exists", function () {
      $analyticsString = $("<div data-analytics='trackPageView' data-url='http://example.com'/>");
      $(document.body).append($analyticsString);
      window.GOVUK.GDM.analytics.virtualPageViews();
      expect(window.ga.calls.allArgs()).toContain([ 'send', 'pageview', { page: 'http://example.com/vpv' } ]);
    });


      it("Should add '/vpv/' to url before question mark", function () {
        $analyticsString = $('<div data-analytics="trackPageView" data-url="http:/testing.co.uk/testrubbs?sweet"/>');
        $(document.body).append($analyticsString);
        window.GOVUK.GDM.analytics.virtualPageViews();
        expect(window.ga.calls.allArgs()).toContain(['send', 'pageview', {page: "http:/testing.co.uk/testrubbs/vpv?sweet"}]);
      });

      it("Should add '/vpv/' to url at the end if no question mark", function () {
        $analyticsString = $("<div data-analytics='trackPageView' data-url='http://example.com'/>");
        $(document.body).append($analyticsString);
        window.GOVUK.GDM.analytics.virtualPageViews();
        expect(window.ga.calls.allArgs()).toContain(['send', 'pageview', {page: "http://example.com/vpv"}]);
      });
  });

});

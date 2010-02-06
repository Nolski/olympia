from django import test
from nose.tools import eq_
from stats.models import DownloadCount, UpdateCount, StatsDict

from datetime import date


class TestDownloadCountModel(test.TestCase):
    fixtures = ['stats/test_models.json']

    def test_sources(self):
        dc = DownloadCount.objects.get(id=1)

        assert isinstance(dc.sources, StatsDict), 'sources is not a StatsDict'
        assert len(dc.sources) > 0, 'sources is empty'

    def test_summary(self):
        # somewhat contrived, but a good test: summarize the entire dataset
        summary = DownloadCount.objects.all().summary(
                count_sum='count', sources_sum='sources')

        eq_(len(summary), 4, 'unexpected number of keys in summary')
        eq_(summary['start'], None, 'start is not None')
        assert summary['row_count'] > 0, 'zero rows in summary'
        assert summary['count_sum'] > 0, 'zero count_sum in summary'
        assert sum(summary['sources_sum'].values()) > 0, \
                'zero sources in summary'

    def test_remap_special_fields(self):
        qs = DownloadCount.objects.filter(pk=1)
        days = list(qs.daily_summary(date='start', rows='row_count',
                                     start='count'))

        eq_(len(days), 1, 'unexpected number of days')
        assert 'date' in days[0], 'date key not in summary results'
        assert 'rows' in days[0], 'rows key not in summary results'
        assert 'start' in days[0], 'start key not in summary results'
        eq_(days[0]['date'], date(2009, 6, 1), 'unexpected date value')
        eq_(days[0]['rows'], 1, 'unexpected rows value')
        eq_(days[0]['start'], 10, 'unexpected start value')

    def test_weekly_summary(self):
        qs = DownloadCount.objects.filter(addon=4,
                date__range=(date(2009, 6, 1), date(2009, 7, 3)))
        weeks = list(qs.weekly_summary('count', 'sources'))

        eq_(len(weeks), 5, 'unexpected number of weeks')
        eq_(weeks[0]['start'], date(2009, 6, 29),
            'unexpected start date for week 1')
        eq_(weeks[4]['start'], date(2009, 6, 1),
            'unexpected start date for week 5')
        eq_(weeks[4]['row_count'], 2, 'unexpected # of rows in week 5')
        eq_(weeks[4]['count'], 20, 'unexpected count total in week 5')
        eq_(sum(weeks[4]['sources'].values()), 10,
            'unexpected sources total in week 5')

    def test_monthly_summary(self):
        qs = DownloadCount.objects.filter(addon=4,
                date__range=(date(2009, 6, 1), date(2009, 9, 30)))
        months = list(qs.monthly_summary('count', 'sources'))

        eq_(len(months), 4, 'unexpected number of months')
        eq_(months[0]['start'], date(2009, 9, 1),
            'unexpected start date for month 1')
        eq_(months[3]['start'], date(2009, 6, 1),
            'unexpected start date for month 4')
        eq_(months[3]['row_count'], 5, 'unexpected # of rows in month 4')
        eq_(months[3]['count'], 50, 'unexpected count total in month 4')
        eq_(sum(months[3]['sources'].values()), 25,
                'unexpected sources total in month 4')

    def test_daily_fill_holes(self):
        qs = DownloadCount.objects.filter(addon=4,
                date__range=(date(2009, 6, 1), date(2009, 6, 7)))
        days = list(qs.daily_summary('count', 'sources', fill_holes=True))

        eq_(len(days), 7, 'unexpected number of days')
        eq_(days[1]['start'], date(2009, 6, 6),
            'unexpected start date for day 2')
        eq_(days[1]['row_count'], 0, 'unexpected non-zero row_count')
        eq_(days[1]['count'], 0, 'unexpected non-zero count')
        eq_(days[1]['sources'], {}, 'unexpected non-empty sources')


class TestUpdateCountModel(test.TestCase):
    fixtures = ['stats/test_models.json']
    test_app = '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}'
    test_ver = '3.0.9'

    def test_serial_types(self):
        uc = UpdateCount.objects.get(id=1)

        assert isinstance(uc.versions, StatsDict), 'versions not a StatsDict'
        assert isinstance(uc.statuses, StatsDict), 'statuses not a StatsDict'
        assert isinstance(uc.applications, StatsDict), \
            'applications not a StatsDict'
        assert isinstance(uc.oses, StatsDict), 'oses not a StatsDict'
        assert uc.locales == None, 'locales is not None'
        assert len(uc.statuses) > 0, 'statuses is empty'

    def test_applications(self):
        uc = UpdateCount.objects.get(id=1)

        assert isinstance(uc.applications[self.test_app], dict), \
            'applications item is not a dict'
        assert uc.applications[self.test_app][self.test_ver] == 7, \
            'unexpected count for app version'

    def test_applications_summary(self):
        qs = UpdateCount.objects.filter(addon=4,
                date__range=(date(2009, 6, 1), date(2009, 6, 2)))
        summary = qs.summary(apps='applications')

        eq_(summary['row_count'], 2,
            'unexpected row_count in applications summary')
        eq_(summary['apps'][self.test_app][self.test_ver], 13,
            'unexpected total for app version')

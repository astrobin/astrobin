from django.core.files import File
from django.test import TestCase
from django.urls import reverse

from astrobin.tests.generators import Generators
from astrobin_apps_platesolving.services import SolutionService
from astrobin_apps_platesolving.tests.platesolving_generators import PlateSolvingGenerators


class SolutionServiceTest(TestCase):
    def setUp(self):
        self.image = Generators.image()
        self.solution = PlateSolvingGenerators.solution(self.image)
        self.service = SolutionService(self.solution)

    def test_get_or_create_advanced_settings_only_image(self):
        advanced_settings, created = SolutionService.get_or_create_advanced_settings(self.image)
        self.assertIsNone(advanced_settings.sample_raw_frame_file.name)
        self.assertTrue(created)

    def test_get_or_create_advanced_settings_revision_inherits_everything(self):
        advanced_settings, created = SolutionService.get_or_create_advanced_settings(self.image)
        advanced_settings.sample_raw_frame_file = File(open('astrobin/fixtures/test.fits', 'rb'), "test.fits")
        advanced_settings.scaled_font_size = "L"

        self.solution.advanced_settings = advanced_settings
        self.solution.content_object = self.image
        self.solution.save()
        advanced_settings.save()

        advanced_settings, created = SolutionService.get_or_create_advanced_settings(
            Generators.image_revision(image=self.image))

        self.assertNotEqual(advanced_settings.sample_raw_frame_file.name, "")
        self.assertEqual(advanced_settings.scaled_font_size, "L")
        self.assertFalse(created)

    def test_get_or_create_advanced_settings_image_does_not_inherit_file(self):
        advanced_settings, created = SolutionService.get_or_create_advanced_settings(self.image)
        advanced_settings.sample_raw_frame_file = File(open('astrobin/fixtures/test.fits', 'rb'), "test.fits")
        advanced_settings.scaled_font_size = "L"

        self.solution.advanced_settings = advanced_settings
        self.solution.content_object = self.image
        self.solution.save()
        advanced_settings.save()

        advanced_settings, created = SolutionService.get_or_create_advanced_settings(Generators.image(user=self.image.user))

        self.assertIsNone(advanced_settings.sample_raw_frame_file.name)
        self.assertEqual(advanced_settings.scaled_font_size, "L")
        self.assertFalse(created)

    def test_get_objects_in_field(self):
        self.maxDiff = None
        basic = \
            'Merope Nebula, NGC 1435, Maia Nebula, NGC 1432, Barnard\'s Merope Nebula, IC 349, ' \
            'The star Pleione (28Tau), The star Atlas (27Tau), The star ηTau, The star Merope (23Tau), ' \
            'The star Sterope I (21Tau), The star Taygeta (19Tau), The star 18Tau, The star Electra (17Tau), ' \
            'The star Celaeno (16Tau)'
        advanced = \
            'GridLabel,2357.38,1145.92,2380.38,1154.92,+21°\nGridLabel,1942.40,889.69,1965.40,898.69,+22°\n' \
            'GridLabel,1528.86,631.94,1551.86,641.94,+23°\n' \
            'GridLabel,1113.79,377.34,1136.79,386.34,+24°\n' \
            'GridLabel,700.20,120.49,723.20,130.49,+25°\n' \
            'GridLabel,285.09,-136.42,308.09,-126.42,+26°\n' \
            'GridLabel,1994.54,-147.41,2027.54,-137.41,3h36m\n' \
            'GridLabel,1762.26,236.24,1795.26,246.24,3h40m\n' \
            'GridLabel,1528.86,617.94,1561.86,627.94,3h44m\n' \
            'GridLabel,1290.74,998.51,1323.74,1008.51,3h48m\n' \
            'GridLabel,1051.11,1376.96,1084.11,1386.96,3h52m\n' \
            'Label,892.38,870.27,931.38,881.27,26 Tau\n' \
            'Label,948.59,588.56,987.59,599.56,23 Tau\n' \
            'Label,945.59,609.56,987.59,622.56,Merope\n' \
            'Label,798.97,828.40,837.97,839.40,27 Tau\n' \
            'Label,798.97,850.40,827.97,861.40,Atlas\n' \
            'Label,803.78,667.12,854.78,680.12,25 eta Tau\n' \
            'Label,843.28,684.62,888.28,697.62,Alcyone\n' \
            'Label,1026.51,420.43,1064.51,431.43,17 Tau\n' \
            'Label,965.51,420.43,1004.51,431.43,Electra\n' \
            'Label,880.10,641.68,919.10,652.68,24 Tau\n' \
            'Label,702.22,820.08,741.22,831.08,28 Tau\n' \
            'Label,721.22,803.58,761.22,814.58,Pleione\n' \
            'Label,957.99,368.50,995.99,379.50,16 Tau\n' \
            'Label,923.99,352.00,969.99,363.00,Celaeno\n' \
            'Label,865.82,444.53,904.82,455.53,20 Tau\n' \
            'Label,817.82,444.53,843.82,455.53,Maia\n' \
            'Label,789.96,359.80,838.96,372.80,19 q Tau\n' \
            'Label,825.96,342.30,873.96,355.30,Taygeta\n' \
            'Label,745.37,440.50,784.37,451.50,22 Tau\n' \
            'Label,709.87,423.00,764.87,436.00,Sterope II\n' \
            'Label,784.14,403.94,823.14,414.94,21 Tau\n' \
            'Label,710.14,391.94,762.14,404.94,Asterope\n' \
            'Label,710.28,260.68,748.28,271.68,18 Tau\n' \
            'Label,877.04,672.33,930.04,684.33,Pleiades\n' \
            'Label,830.04,645.73,855.04,657.73,M45\n' \
            'Label,1014.65,642.27,1072.65,654.27,NGC1435\n' \
            'Label,1094.65,619.27,1188.65,633.27,Merope nebula\n' \
            'Label,1012.63,602.11,1048.63,614.11,IC349\n'

        self.solution.objects_in_field = basic
        self.solution.advanced_annotations = advanced

        self.assertEqual(
            ["16 Tau", "17 Tau", "18 Tau", "19 q Tau", "20 Tau", "21 Tau", "22 Tau", "23 Tau", "24 Tau", "25 eta Tau",
             "26 Tau", "27 Tau", "28 Tau", "Alcyone", "Asterope", "Atlas", "Barnard's Merope Nebula", "Celaeno",
             "Electra", "IC 349", "M 45", "Maia", "Maia Nebula", "Merope", "Merope Nebula",
             "NGC 1432", "NGC 1435", "Pleiades", "Pleione", "Sterope II", "Taygeta", "The star 18Tau",
             "The star Atlas (27Tau)", "The star Celaeno (16Tau)", "The star Electra (17Tau)",
             "The star Merope (23Tau)", "The star Pleione (28Tau)", "The star Sterope I (21Tau)",
             "The star Taygeta (19Tau)", "The star ηTau"],
            SolutionService(self.solution).get_objects_in_field()
        )

    def test_get_objects_in_field_2(self):
        basic = \
            'M 43, Mairan\'s Nebula, NGC 1982, Upper Sword, NGC 1981, Lower Sword, NGC 1980, the Running Man Nebula, ' \
            'NGC 1977, M 42, Orion Nebula, Great Orion Nebula, NGC 1976, NGC 1975, NGC 1973, The star 45Ori, ' \
            'The star ιOri, The star θ2Ori, The star θ1Ori, The star 42Ori'
        advanced = \
            'GridLabel,2100.97,889.69,2133.97,899.69,−7°30′\n' \
            'GridLabel,1752.10,661.34,1785.10,671.34,−6°45′\n' \
            'GridLabel,1403.90,433.37,1420.90,443.37,−6°\n' \
            'GridLabel,1055.90,205.27,1088.90,215.27,−5°15′\n' \
            'GridLabel,707.92,-23.04,740.92,-13.04,−4°30′\n' \
            'GridLabel,359.61,-251.42,392.61,-241.42,−3°45′\n' \
            'GridLabel,2014.56,-503.48,2047.56,-493.48,5h24m\n' \
            'GridLabel,1708.58,-41.88,1741.58,-31.88,5h28m\n' \
            'GridLabel,1403.90,419.37,1436.90,429.37,5h32m\n' \
            'GridLabel,1100.39,880.64,1133.39,890.64,5h36m\n' \
            'GridLabel,797.83,1342.59,830.83,1352.59,5h40m\n' \
            'Label,1047.55,803.40,1090.55,814.40,44 iot Ori\n' \
            'Label,1050.55,780.40,1090.55,793.40,Hatysa\n' \
            'Label,840.08,653.15,912.08,664.15,43 the02 Ori\n' \
            'Label,835.68,597.86,907.68,608.86,41 the01 Ori\n' \
            'Label,577.89,515.42,612.89,526.42,45 Ori\n' \
            'Label,618.81,462.10,663.81,473.10,42 c Ori\n' \
            'Label,883.02,616.32,955.02,627.32,41 the01 Ori\n' \
            'Label,783.97,590.40,808.97,602.40,M43\n' \
            'Label,668.97,618.90,790.97,630.90,De Mairan\'s nebula\n' \
            'Label,1412.06,1150.52,1471.06,1162.52,NGC1999\n' \
            'Label,1116.54,791.05,1175.54,803.05,NGC1980\n' \
            'Label,590.69,425.52,648.69,437.52,NGC1977\n' \
            'Label,552.36,377.02,610.36,389.02,NGC1973\n' \
            'Label,473.70,416.32,531.70,428.32,NGC1975\n' \
            'Label,447.67,310.97,505.67,322.97,NGC1981\n' \
            'Label,1330.13,255.41,1357.13,263.41,VdB42\n' \
            'Label,684.14,18.22,711.14,26.22,VdB44\n' \
            'Label,946.28,588.09,979.28,596.09,Sh2-281\n' \
            'Label,550.18,457.48,583.18,465.48,Sh2-279\n'

        self.solution.objects_in_field = basic
        self.solution.advanced_annotations = advanced

        self.assertEqual(
            ['41 the01 Ori', '42 c Ori', '43 the02 Ori', '44 iot Ori', '45 Ori', 'De Mairan\'s nebula',
             'Great Orion Nebula', 'Hatysa', 'Lower Sword', 'M 42', 'M 43', 'Mairan\'s Nebula', 'NGC 1973',
             'NGC 1975', 'NGC 1976', 'NGC 1977', 'NGC 1980', 'NGC 1981', 'NGC 1982',
             'NGC 1999', 'Orion Nebula', 'Sh2-279', 'Sh2-281', 'The star 42Ori', 'The star 45Ori',
             'The star θ1Ori', 'The star θ2Ori', 'The star ιOri', 'Upper Sword', 'VdB42', 'VdB44',
             'the Running Man Nebula'],
            SolutionService(self.solution).get_objects_in_field()
        )

    def test_get_objects_in_field_clean(self):
        basic = 'M 45'
        advanced = 'Label,1,2,3,M45'

        self.solution.objects_in_field = basic
        self.solution.advanced_annotations = advanced

        self.assertEqual(['M 45', 'M45'], SolutionService(self.solution).get_objects_in_field(clean=False))
        self.assertEqual(['M 45'], SolutionService(self.solution).get_objects_in_field())

    def test_get_objects_in_field_capitals(self):
        basic = 'Merope nebula'
        advanced = 'Label,1,2,3,Merope Nebula'

        self.solution.objects_in_field = basic
        self.solution.advanced_annotations = advanced

        self.assertEqual(['Merope nebula'], SolutionService(self.solution).get_objects_in_field(clean=False))
        self.assertEqual(['Merope nebula'], SolutionService(self.solution).get_objects_in_field())

    def test_duplicate_objects_in_field_by_catalog_space(self):
        basic = "Orion Nebula, M 42, M 43"
        advanced = \
            "Label,1,2,3,M42\n" \
            "Label,1,2,3,M43\n" \
            "Label,1,2,3,M 45\n" \
            "Label,1,2,3,LDN123\n" \
            "Label,1,2,3,LDN 999\n" \
            "Label,1,2,3,LBN456\n" \
            "Label,1,2,3,Sh2-129\n" \
            "Label,1,2,3,TYC5403-2132-1\n"

        self.solution.objects_in_field = basic
        self.solution.advanced_annotations = advanced

        objects = SolutionService(self.solution).duplicate_objects_in_field_by_catalog_space()

        self.assertTrue("Orion Nebula" in objects)

        self.assertTrue("M42" in objects)
        self.assertTrue("M 42" in objects)

        self.assertTrue("M43" in objects)
        self.assertTrue("M 43" in objects)

        self.assertTrue("M45" in objects)
        self.assertTrue("M 45" in objects)

        self.assertTrue("LDN123" in objects)
        self.assertTrue("LDN 123" in objects)

        self.assertTrue("LDN999" in objects)
        self.assertTrue("LDN 999" in objects)

        self.assertTrue("LBN456" in objects)
        self.assertTrue("LBN 456" in objects)

        self.assertTrue("Sh2-129" in objects)
        self.assertTrue("Sh2_129" in objects)

        self.assertTrue("TYC5403-2132-1" in objects)
        self.assertTrue("TYC5403_2132_1" in objects)

    def test_get_search_query_around_with_no_advanced_coordinates(self):
        self.service.solution = type('solution', (object,), {})()  # Mock solution object
        self.service.solution.ra = 10.0
        self.service.solution.dec = 20.0
        self.service.solution.advanced_ra = None
        self.service.solution.advanced_dec = None

        # Test the method with default RA and DEC
        expected_url = reverse('haystack_search') + \
                       "?q=&d=i&t=all&coord_ra_min=7.50&coord_ra_max=12.50" + \
                       "&coord_dec_min=17.50&coord_dec_max=22.50" + \
                       "&field_radius_min=0.00&field_radius_max=5.00"
        result = self.service.get_search_query_around(5)
        self.assertEqual(result, expected_url)

    def test_get_search_query_around_with_advanced_coordinates(self):
        self.service.solution = type('solution', (object,), {})()  # Mock solution object
        self.service.solution.ra = 10.0
        self.service.solution.dec = 20.0
        self.service.solution.advanced_ra = None
        self.service.solution.advanced_dec = None

        # Test the method with advanced RA and DEC
        self.service.solution.advanced_ra = 30.0
        self.service.solution.advanced_dec = 40.0

        expected_url = reverse('haystack_search') + \
                       "?q=&d=i&t=all&coord_ra_min=27.50&coord_ra_max=32.50" + \
                       "&coord_dec_min=37.50&coord_dec_max=42.50" + \
                       "&field_radius_min=0.00&field_radius_max=5.00"
        result = self.service.get_search_query_around(5)
        self.assertEqual(result, expected_url)

    def test_get_search_query_around_near_zero_ra_dec(self):
        # Test method with RA and DEC near zero
        self.service.solution.ra = 1.0
        self.service.solution.dec = 1.0
        expected_url = reverse('haystack_search') + \
                       "?q=&d=i&t=all&coord_ra_min=359.00&coord_ra_max=3.00" + \
                       "&coord_dec_min=-1.00&coord_dec_max=3.00" + \
                       "&field_radius_min=0.00&field_radius_max=4.00"
        result = self.service.get_search_query_around(4)
        self.assertEqual(result, expected_url)

    def test_get_search_query_around_near_max_ra(self):
        # Test method with RA near 360 degrees
        self.service.solution.ra = 359.0
        self.service.solution.dec = 20.0
        expected_url = reverse('haystack_search') + \
                       "?q=&d=i&t=all&coord_ra_min=357.00&coord_ra_max=1.00" + \
                       "&coord_dec_min=18.00&coord_dec_max=22.00" + \
                       "&field_radius_min=0.00&field_radius_max=4.00"
        result = self.service.get_search_query_around(4)
        self.assertEqual(result, expected_url)

    def test_get_search_query_around_near_polar_dec_minus_90(self):
        # Test method with DEC near -90
        self.service.solution.ra = 10.0
        self.service.solution.dec = -89.0
        expected_url = reverse('haystack_search') + \
                       f"?q=&d=i&t=all&coord_ra_min=8.00&coord_ra_max=12.00" + \
                       f"&coord_dec_min=-90.00&coord_dec_max=-87.00" + \
                       "&field_radius_min=0.00&field_radius_max=4.00"
        result = self.service.get_search_query_around(4)
        self.assertEqual(result, expected_url)

    def test_get_search_query_around_near_polar_dec_plus_90(self):
        # Test method with DEC near +90
        self.service.solution.ra = 10.0
        self.service.solution.dec = 89.0
        expected_url = reverse('haystack_search') + \
                       f"?q=&d=i&t=all&coord_ra_min=8.00&coord_ra_max=12.00" + \
                       f"&coord_dec_min=87.00&coord_dec_max=90.00" + \
                       "&field_radius_min=0.00&field_radius_max=4.00"
        result = self.service.get_search_query_around(4)
        self.assertEqual(result, expected_url)


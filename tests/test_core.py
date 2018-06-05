import unittest

from xiami_downloader.core import decrypt_location


class TestDecryptLocation(unittest.TestCase):

    def test_none(self):
        actual = decrypt_location(None)
        self.assertIsNone(actual)

    def test_split_a(self):
        text_input = '4%22i.%2F%672E55F55119%2m3teD84%%%b8%6e9%55d2F8an27252%132E1EE65151pFhy17%5557d53a25E46Fm.meF%1E22%77%839121E13a_%575EEEf9E265Ecb%1xit22142F51%2%%8_625.%uk322E---a9f73b%88'  # NOQA
        expected = '//m128.xiami.net/227/2110462227/2103715270/1803098161_1526911205211.mp3?auth_key=1528772400-0-0-b7fa8d990f6327ea63925b00c854b8d6'  # NOQA
        actual = decrypt_location(text_input)
        self.assertEqual(actual, expected)

    def test_split_b(self):
        text_input = '8%2.7512583953e8%%599528n4E717%294Fy755E893F.e%%6%75985a%7EEd3a4%xt25756E_7.u32--9b462i%FE4E%211mtD4%b3f45Fa22%%3285%ph1%53a282mmF1526F2253_55E8b8f1i6%EF6172E%k2E-%92e'  # NOQA
        expected = '//m128.xiami.net/674/2100017674/2103665776/1802827329_1522998710545.mp3?auth_key=1528772400-0-0-b380d93ab9983bf28299a448fe534652'  # NOQA
        actual = decrypt_location(text_input)
        self.assertEqual(actual, expected)

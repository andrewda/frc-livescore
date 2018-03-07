#!/usr/bin/env python
# -*- coding: utf-8 -*-
import regex


def num_pat(r):
    return r.replace('@', '0-9ZSO')  # Characters that might get recognized as numbers


class MatchNameParser(object):
    QF_BRACKET_ELIM_MAPPING = {
        1: (1, 1),  # (set, match)
        2: (2, 1),
        3: (3, 1),
        4: (4, 1),
        5: (1, 2),
        6: (2, 2),
        7: (3, 2),
        8: (4, 2),
    }

    SF_BRACKET_ELIM_MAPPING = {
        1: (1, 1),  # (set, match)
        2: (2, 1),
        3: (1, 2),
        4: (2, 2),
    }

    # Possible formats are like:
    # Test Match
    # Practice X of Y
    # Qualification X of Y
    # Octofinal X of Y
    # Octofinal Tiebreaker X
    # Quarterfinal X of Y
    # Quarterfinal Tiebreaker X
    # Semifinal X of Y
    # Semifinal Tiebreaker X
    # Final X
    # Overtime X
    # Einstein X of Y
    # Einstein Final X
    # Einstein Overtime X
    MATCH_ID_FORMATS = [
        # English
        (regex.compile(num_pat('(Test\s+Match){e<=3}')), 'test', False),
        (regex.compile(num_pat('(Practice){e<=3}\s+([@]+)'), False), 'pm', False),
        (regex.compile(num_pat('(Qualification){e<=3}\s+([@]+)'), False), 'qm', False),
        (regex.compile(num_pat('(Octofinal){e<=3}\s+([@]+)'), False), 'ef', False),
        (regex.compile(num_pat('(Octofinal\s+Tiebreaker){e<=3}\s+([@]+)'), False), 'ef', True),
        (regex.compile(num_pat('(Quarterfinal){e<=3}\s+([@]+)'), False), 'qf', False),
        (regex.compile(num_pat('(Quarterfinal\s+Tiebreaker){e<=3}\s+([@]+)'), False), 'qf', True),
        (regex.compile(num_pat('(Semifinal){e<=3}\s+([@]+)'), False), 'sf', False),
        (regex.compile(num_pat('(Semifinal\s+Tiebreaker){e<=3}\s+([@]+)'), False), 'sf', True),
        (regex.compile(num_pat('(Final){e<=3}\s+([@]+)'), False), 'f', False),
        (regex.compile(num_pat('(Overtime){e<=3}\s+([@]+)'), False), 'overtimef', False),
        (regex.compile(num_pat('(Einstein){e<=3}\s+([@]+)'), False), 'sf', False),
        (regex.compile(num_pat('(Einstein\s+Final){e<=3}\s+([@]+)'), False), 'f', False),
        (regex.compile(num_pat('(Einstein\s+Final\s+Overtime){e<=3}\s+([@]+)'), False), 'f', True),
        # Spanish
        (regex.compile(num_pat('(Juego\s+de\s+Preuba){e<=3}')), 'test', False),
        (regex.compile(num_pat('(Practica){e<=3}\s+([@]+)'), False), 'pm', False),
        (regex.compile(num_pat('(Clasificacion){e<=3}\s+([@]+)'), False), 'qm', False),
        (regex.compile(num_pat('(Cuarto\s+de\s+final){e<=3}\s+([@]+)'), False), 'qf', False),
        (regex.compile(num_pat('(Desempate\s+Cuarto\s+de\s+final){e<=3}\s+([@]+)'), False), 'qf', True),
        (regex.compile(num_pat('(Semifinal){e<=3}\s+([@]+)'), False), 'sf', False),
        (regex.compile(num_pat('(Desempate\s+Semifinal){e<=3}\s+([@]+)'), False), 'sf', True),
        (regex.compile(num_pat('(Final){e<=3}\s+([@]+)'), False), 'f', False),
        (regex.compile(num_pat('(Tiempo\s+Extra){e<=3}\s+([@]+)'), False), 'overtimef', False),
        # French
        (regex.compile(num_pat('(Simulation){e<=3}')), 'test', False),
        (regex.compile(num_pat('(Practique){e<=3}\s+([@]+)'), False), 'pm', False),
        (regex.compile(num_pat('(Qualification){e<=3}\s+([@]+)'), False), 'qm', False),
        (regex.compile(num_pat('(Quart\s+de\s+finale){e<=3}\s+([@]+)'), False), 'qf', False),
        (regex.compile(num_pat(u'(Bris\s+d\'égalité\s+){e<=3}QF\s+([@]+)'), False), 'qf', True),
        (regex.compile(num_pat('(Demi-finale){e<=3}\s+([@]+)'), False), 'sf', False),
        (regex.compile(num_pat(u'(Bris\s+d\'égalité\s+){e<=3}DF\s+([@]+)'), False), 'sf', True),
        (regex.compile(num_pat('(Finale){e<=3}\s+([@]+)'), False), 'f', False),
        (regex.compile(num_pat('(Prolongation){e<=3}\s+([@]+)'), False), 'overtimef', False),
        # Turkish
        (regex.compile(num_pat(u'(Test\s+Maçı){e<=3}')), 'test', False),
        (regex.compile(num_pat(u'(Pratik\s+Maçı){e<=3}\s+([@]+)'), False), 'pm', False),
        (regex.compile(num_pat(u'(Sıralama\s+Maçı){e<=3}\s+([@]+)'), False), 'qm', False),
        (regex.compile(num_pat(u'(Çeyrek\s+Final){e<=3}\s+([@]+)'), False), 'qf', False),
        (regex.compile(num_pat(u'ÇF\s+(Son\s+Maç){e<=3}\s+([@]+)'), False), 'qf', True),
        (regex.compile(num_pat(u'(Yarı\s+Final){e<=3}\s+([@]+)'), False), 'sf', False),
        (regex.compile(num_pat(u'YF\s+(Son\s+Maç){e<=3}\s+([@]+)'), False), 'sf', True),
        (regex.compile(num_pat('(Final){e<=3}\s+([@]+)'), False), 'f', False),
        (regex.compile(num_pat('(Uzatma){e<=3}\s+([@]+)'), False), 'overtimef', False),
        # Chinese
        (regex.compile(num_pat(u'测试赛')), 'test', False),
        (regex.compile(num_pat(u'练习赛\s+([@]+)'), False), 'pm', False),
        (regex.compile(num_pat(u'资格赛\s+([@]+)'), False), 'qm', False),
        (regex.compile(num_pat(u'8进4淘汰赛第\s+([@]+)'), False), 'qf', False),
        (regex.compile(num_pat(u'8进4淘汰赛决胜局\s+([@]+)'), False), 'qf', True),
        (regex.compile(num_pat(u'半决赛\s+([@]+)'), False), 'sf', False),
        (regex.compile(num_pat(u'半决赛决胜赛 第\s+([@]+)'), False), 'sf', True),
        (regex.compile(num_pat(u'决赛\s+([@]+)'), False), 'f', False),
        (regex.compile(num_pat(u'加时赛\s+([@]+)'), False), 'overtimef', False),
    ]

    def _fix_digits(self, text):
        return int(text.replace('Z', '2').replace('S', '5').replace('O', '0'))

    def get_match_key(self, raw_match_name):
        print raw_match_name
        for reg, comp_level, tiebreaker in self.MATCH_ID_FORMATS:
            match = reg.match(raw_match_name)
            if match:
                # TODO: Make API call to TBA to figure out match key
                if comp_level == 'pm':
                    return 'pm{}'.format(self._fix_digits(match.group(2)))
                elif comp_level == 'qm':
                    return 'qm{}'.format(self._fix_digits(match.group(2)))
                elif comp_level == 'ef':
                    return 'ef{}'.format(self._fix_digits(match.group(2)))  # TODO: not correct
                elif comp_level == 'qf':
                    s, m = self.QF_BRACKET_ELIM_MAPPING[self._fix_digits(match.group(2))]
                    if tiebreaker:
                        m = 3
                    return 'qf{}m{}'.format(s, m)
                elif comp_level == 'sf':
                    s, m = self.SF_BRACKET_ELIM_MAPPING[self._fix_digits(match.group(2))]
                    if tiebreaker:
                        m = 3
                    return 'sf{}m{}'.format(s, m)
                elif comp_level == 'f':
                    return 'f1m{}'.format(self._fix_digits(match.group(2)))
                elif comp_level == 'overtimef':
                    return 'f1m{}'.format(3+self._fix_digits(match.group(2)))
                else:
                    return 'test'
        return None

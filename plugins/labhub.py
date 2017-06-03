import json
import os
import re

import github3
from errbot import BotPlugin, re_botcmd

from plugins import constants


class LabHub(BotPlugin):
    """GitHub and GitLab utilities"""  # Ignore QuotesBear

    INVITE_SUCCESS = {
        'newcomers': """
 Welcome @{}! :tada:\n\nTo get started, please follow our
 [newcomers guide](https://coala.io/newcomer). Most issues will be explained
 there and in linked pages - it will save you a lot of time, just read it.
 *Really.*\n\n*Do not take an issue if you don't understand it on your own.*
 Especially if you are new you have to be aware that getting started with an
 open source community is not trivial: you will have to work hard and most
 likely become a better coder than you are now just as we all did.\n\n
 Don't get us wrong: we are *very* glad to have you with us on this journey
 into open source! We will also be there for you at all times to help you
 with actual problems. :)
""",
        'developers': """
 Wow @{}, you are a part of developers team now! :tada: Welcome to our
 community!
""",
        'maintainers': """
 @{} you seem to be awesome! You are now a maintainer! :tada: Please go
 through https://github.com/coala/coala/wiki/Membership
"""
    }

    GH_ORG_NAME = constants.GH_ORG_NAME
    def __init__(self, bot, name=None):
        super().__init__(bot, name)

        teams = dict()
        try:
            gh = github3.login(os.environ.get('GH_TOKEN'))
            assert gh is not None
        except AssertionError:
            self.log.error('Cannot create github object, please check GH_TOKEN')
        else:
            self.GH3_ORG = gh.organization(self.GH_ORG_NAME)
            for team in self.GH3_ORG.iter_teams():
                teams[team.name] = team

        self._teams = teams

    @property
    def TEAMS(self):
        return self._teams

    @TEAMS.setter
    def TEAMS(self, new):
        self._teams = new

    @re_botcmd(pattern=r'(?:(?:invite)|(?:inv))\s+(\w+)\s*(?:to)\s+(\w+)')
    def invite_cmd(self, msg, match):
        """
        Invite given user to given team. By default it invites to
        "newcomers" team.
        """
        invitee = match.group(1)
        inviter = msg.frm.nick

        team = (self.GH_ORG_NAME + ' newcomers' if match.group(2) is None
                else match.group(2))

        self.log.info('{} invited {} to {}'.format(inviter, invitee, team))

        if self.TEAMS[self.GH_ORG_NAME + ' maintainers'].is_member(invitee):
            valid_teams = ['newcomers', 'developers', 'maintainers']
            if team.lower() not in valid_teams:
                return 'Please select from one of the ' + ', '.join(valid_teams)
            team_mapping = {
                'newcomers': self.GH_ORG_NAME + ' newcomers',
                'developers': self.GH_ORG_NAME + ' developers',
                'maintainers': self.GH_ORG_NAME + ' maintainers'
            }

            # send the invite
            self.TEAMS[team_mapping[team.lower()]].invite(invitee)
            return self.INVITE_SUCCESS[team.lower()].format(invitee)
        else:
            return ('@{}, you are not a maintainer, only maintainers can invite'
                    ' other people. Nice try :poop:'.format(inviter))

    def callback_message(self, msg):
        """Invite the user whose message includes the holy 'hello world'"""
        if re.search(r'hello\s*,?\s*world', msg.body, flags=re.IGNORECASE):
            user = msg.frm.nick
            if not self.TEAMS[self.GH_ORG_NAME + ' newcomers'].is_member(user):
                # send the invite
                self.send(msg.frm,
                          self.INVITE_SUCCESS['newcomers'].format(user))
                self.TEAMS[self.GH_ORG_NAME + ' newcomers'].invite(user)

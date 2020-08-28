import re

import ldap
import logging
import datetime


def get_users(config, group_list, ldap_url):
    ldap_logger = logging.getLogger('generator.LDAP')
    ad = ldap.initialize(ldap_url)
    ad.protocol_version = ldap.VERSION3

    try:
        ad.simple_bind_s(config["LDAP"]["ad_username"], config["LDAP"]["ad_password"])
    except ldap.SERVER_DOWN:
        ldap_logger.exception('Connection error to ' + ldap_url)
    except ldap.INVALID_CREDENTIALS:
        ldap_logger.exception('Invalid "ad_username" or/and "ad_password".')
    else:
        ldap_logger.info('Connection established to ' + ldap_url)

    ad.set_option(ldap.OPT_REFERRALS, 0)
    scope = ldap.SCOPE_SUBTREE

    ldap_filter = "(&(|(objectCategory=container)(objectCategory=organizationalUnit)))"
    ldap_users = ad.search_s(config["LDAP"]["base_dn"], scope, ldap_filter, ["name"])
    groups = {}
    if ldap_users[0]:
        pattern = re.compile('(^|\s)[-a-zA-Z0-9_.]+@([-a-zA-Z0-9]+\.)+[a-zA-Z]{2,6}(\s|$)')
        for group in group_list:
            ldap_group_filter = '(&(objectCategory=person)(objectClass=user)(mail=*)' \
                                '(!(useraccountcontrol=514))(memberOf=cn={},{}))' \
                .format(group, config["LDAP"]["base_dn"])

            ldap_users_of_group = ad.search_s(ldap_users[0][0], scope, ldap_group_filter, ["cn", "mail"])

            if len(ldap_users_of_group) > 0:
                groups.update({group: []})

                for ldap_user in ldap_users_of_group:
                    if pattern.fullmatch(ldap_user[1]["mail"][0].decode('utf-8')):
                        groups[group].append({
                            "name": ldap_user[1]["cn"][0],
                            "email": ldap_user[1]["mail"][0],
                            "group": group})

    groups.update({"External": []})
    if config["Mail"]["external_email"]:
        emails = config["Mail"]["external_email"].split(';')
        for email in emails:
            groups["External"].append({
                "email": bytes(email, 'utf-8'),
                "group": b"External"
            })
    elif len(groups["External"]) < 2:
        groups["External"].append({
            "email": b"abcd@abc.org",
            "group": b"External"
        }).append({
            "email": b"efgh@abc.org",
            "group": b"External"
        })

    return groups

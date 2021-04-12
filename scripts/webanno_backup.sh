#!/bin/bash
# This script describes the backup of the webanno instance on nlp.dainst.org
# Installation was: https://webanno.github.io/webanno/releases/3.6.6/docs/admin-guide.html#_running_via_separate_tomcat_war

set -e

# Backup the webanno database to the webanno home dir, then backup the webanno home dir
DB_PASS=$(grep 'database.password' /srv/webanno/settings.properties | egrep -o '[^=]+$')
mysqldump -u webanno -p"$DB_PASS" --no-tablespaces webanno > /tmp/webanno.sql
sudo mv /tmp/webanno.sql /srv/webanno/db-backup.sql
sudo tar czf webanno-backup-$(date +"%Y-%m-%d").tar.gz -C /srv /srv/webanno

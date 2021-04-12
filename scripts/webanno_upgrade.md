
## Webanno Upgrade

For the webanno instance on nlp.dainst.org.dainst:1808

Relevant links:

* [Original Installation Instructions](https://webanno.github.io/webanno/releases/3.6.6/docs/admin-guide.html#_running_via_separate_tomcat_war)
* [Upgrade/Backup Procedure](https://webanno.github.io/webanno/releases/3.6.6/docs/admin-guide.html#sect_upgrade)
* __NB__: A webanno backup script is in this directory
* Be sure to read the release notes for your version, e.g.: https://github.com/webanno/webanno/releases/tag/webanno-3.6.7

With a running tomcat, get the new war file and delete the old one:

```
wget https://github.com/webanno/webanno/releases/download/webanno-3.6.7/webanno-webapp-3.6.7.war
sudo rm /opt/webanno/webapps/webanno.war
```

Now, the running tomcat should have deleted the webanno dir, make sure that this has completed, only then stop the tomcat

```shell
test -d /opt/webanno/webapps/webanno || echo "OK, is deleted"
sudo service webanno stop
```

Copy the new war into place and restart the tomcat:

```
sudo cp webanno-webapp-3.6.7.war /opt/webanno/webapps/webanno.war
sudo service webanno start
```

Navigate to:

* http://nlp.dainst.org:18080/webanno/login.html

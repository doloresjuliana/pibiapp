
## Pibiapp

Pibiapp is an application developed on the Frappe framework to integrate it with other systems and expand the functionality of applications on this framework.

#### Current modules

- Nextcloud
    
    Connect Frappe and Nextcloud, store the attachments on the Nextcloud server
    
    Create folders to archive by application and module.
    
    Share the link with Nextcloud users that belong to the group corresponding to the module
    
    Tag in Nextcloud the attached files taking into account the application, the modules, the identifier of the transaction and other related data. Includes tagging of the Frappe transaction as file tags in Nextcloud.
    
    Manage a history of versions in Nextcloud. When the same file is uploaded from Frappe with successive modifications.

### License

GNU General Public License v3. See license.txt

### Install

You must have previously installed the Frappe framework v10.1.68+ and bench

Go to your bench folder and setup the new app

```
bench get-app pibiapp https://github.com/doloresjuliana/pibiapp
bench --site yoursite install-app pibiapp
```

Login to your site to configure the app.

https://github.com/doloresjuliana/pibiapp/wiki/NEXTCLOUD-SETTINGS


## Pibiapp

Pibiapp is an application developed on the Frappe framework to integrate it with other systems and expand the functionality of applications on this framework.

#### Current modules

- **Nextcloud**
    
    Connect Frappe and Nextcloud, store the attachments on the Nextcloud server
    
    Create folders to archive by application and module.
    
    Share the link with Nextcloud users that belong to the group corresponding to the module
    
    Tag in Nextcloud the attached files taking into account the application, the modules, the identifier of the transaction and other related data. Includes tagging of the Frappe transaction as file tags in Nextcloud.
    
    Manage a history of versions in Nextcloud. When the same file is uploaded from Frappe with successive modifications.
    
    Include archives stored in Nextcloud as attachments to the email
    
    Upload database backups and local files
    
- **External Data**
    
    Automatically create a new DocType with its data structure of a file
    
    Allows you to select the Module of a Frappe application in which you will create the DocType
    
    Supports files with formats: Excel, CSV, JSON and XML
    
    Analyze the data set to determine the type of data that fields are mandatory and lists of selectable values
    
    Allows successive data loads, provided that the format of the file and the position of the data match the original file used to create the DocType
    
    
    It is limited to data structures of simple records without tables. This version does not load a JSON or XML with hierarchized data in several levels.    

- **Redash**

    Integrate the view of dashboards in Frappe so that end users do not need to access Redash
    
    Provides a security layer that allows Frappe to manage user access to control panels according to their roles

    It is not the purpose of this connector to allow the definition of new Redash panels from Frappe. The system administrator or an expert BI technician should define directly in Redash the control panels that will be visible by this connector in this new module.
    
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

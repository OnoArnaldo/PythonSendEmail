# PythonSendMail
Send email from a recipient list and attachments.

## Usage
```
python send_email.py
```

## Configuration
You will need to set the file config.py. Below is a short description of the parameters.

EMAIL_SENDER: Sender, it will appear in 'To' field.<br>
EMAIL_SUBJECT: Subject of the email. It can have placeholders.<br>

EMAIL_SMTP_USER: User to connect to SMTP.<br>
EMAIL_SMTP_PWD: Password to connect to SMTP.<br>
EMAIL_SMTP_HOST: SMTP host.<br>
EMAIL_SMTP_PORT: SMTP port.<br>

ATTACH_DIR: Folder with all files which will be attached.<br>
TEMPLATE_FILE: File with the body template. It can have the extensions .txt or .html.<br>
RECIPIENT_FILE: File with the placeholders values. It must have the email column.<br>
RECIPIENT_FILE_SEPARATOR: Separator used in Recipient File.<br>

## Placeholders
Placeholders can be used in Subject and Template File. It must start with $ symbol.

If the value does not exists in Recipient File, it will show the placeholder name (no exception will raise).

## Recipient list file
The recipient file must have the email column and any other used in template or subject.

The column name is without the $ symbol.

## Example
### Subject
```
Happy christmas $friend!
```

### Template
```
Dear $friend,

I am sending you $thing.

$missing_placeholder

Regards,
Me
```

### Recipient list
```
email, friend, thing
Tim <tim@email.com>, Tim, a laptop
ben@email.com, Ben, a cake
tal@email.com, Tal, a t-shirt
```

## result
The send_email.py will send one email for each line in the Recipient File.

For the first line, this will be the result.
```
From: <from config>
To: Tim <tim@email.com>
Subject: Happy christmas Tim!
Body:
Dear Tim,

I am sending you a laptop.

$missing_placeholder

Regards,
Me
```